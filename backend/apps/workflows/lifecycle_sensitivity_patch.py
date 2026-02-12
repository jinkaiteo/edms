"""
Patch for document_lifecycle.py to add sensitivity label handling.

MODIFICATIONS NEEDED:
"""

# ============================================================================
# 1. MODIFY approve_document method (line 349-443)
# ============================================================================

def approve_document(self, document: Document, user: User, 
                    effective_date: date, comment: str = '', approved: bool = True,
                    review_period_months: int = None,
                    sensitivity_label: str = None,  # NEW PARAMETER
                    sensitivity_change_reason: str = '') -> bool:  # NEW PARAMETER
    """
    Approve document with required effective date and sensitivity label.
    
    Args:
        document: Document to approve
        user: User approving (must be assigned approver)
        effective_date: Date when document becomes effective (REQUIRED)
        comment: Approval comment
        approved: True to approve, False to reject
        review_period_months: Periodic review interval in months
        sensitivity_label: Sensitivity classification (REQUIRED for approval)
        sensitivity_change_reason: Reason if sensitivity changed from inherited
        
    Returns:
        bool: True if successful
    """
    workflow = self._get_active_workflow(document)
    if not workflow:
        raise ValidationError("No active workflow found for document")
    
    # Validate user can approve/reject
    if not self._can_approve(document, user):
        raise ValidationError("User is not authorized to approve this document")
    
    # Validate current state
    if workflow.current_state.code != 'PENDING_APPROVAL':
        raise ValidationError(f"Cannot approve from state: {workflow.current_state.code}")
    
    # Handle rejection path
    if not approved:
        return self.reject_document(document, user, comment)
    
    # === NEW: SENSITIVITY LABEL VALIDATION ===
    if not sensitivity_label:
        raise ValidationError("Sensitivity label is required for document approval")
    
    # Import access control
    from apps.documents.access_control import SensitivityAccessControl
    from apps.documents.sensitivity_labels import SENSITIVITY_CHOICES
    
    # Validate sensitivity label value
    valid_labels = [choice[0] for choice in SENSITIVITY_CHOICES]
    if sensitivity_label not in valid_labels:
        raise ValidationError(f"Invalid sensitivity label: {sensitivity_label}. Valid options: {', '.join(valid_labels)}")
    
    # Check if user can approve documents at this sensitivity level
    can_approve_result = SensitivityAccessControl.can_approve_sensitivity_level(user, sensitivity_label)
    if not can_approve_result['allowed']:
        raise ValidationError(
            f"You do not have authority to approve {sensitivity_label} documents. {can_approve_result['reason']}"
        )
    
    # Detect if sensitivity changed from inherited value
    sensitivity_changed = (document.sensitivity_label != sensitivity_label)
    
    # Validate sensitivity change if changed
    if sensitivity_changed:
        validation_result = SensitivityAccessControl.validate_sensitivity_change(
            document.sensitivity_label,
            sensitivity_label,
            user,
            sensitivity_change_reason
        )
        
        if not validation_result['allowed']:
            raise ValidationError(validation_result['reason'])
        
        # Require reason for sensitivity changes
        if not sensitivity_change_reason or len(sensitivity_change_reason.strip()) < 20:
            raise ValidationError(
                "A detailed reason (minimum 20 characters) is required when changing sensitivity classification"
            )
    
    # Set sensitivity label with full tracking
    old_sensitivity = document.sensitivity_label
    document.sensitivity_label = sensitivity_label
    document.sensitivity_set_by = user
    document.sensitivity_set_at = timezone.now()
    
    if sensitivity_changed:
        document.sensitivity_change_reason = sensitivity_change_reason
    
    # === END SENSITIVITY LABEL HANDLING ===
    
    # Validate effective_date is provided for approvals only
    if not effective_date:
        raise ValidationError("Effective date is required for approval")

    # Set effective date and approval date
    document.effective_date = effective_date
    document.approval_date = timezone.now()
    
    # Set periodic review schedule if provided
    if review_period_months is not None and review_period_months > 0:
        document.review_period_months = review_period_months
        from dateutil.relativedelta import relativedelta
        document.next_review_date = effective_date + relativedelta(months=review_period_months)
    else:
        document.review_period_months = None
        document.next_review_date = None
    
    document.save()

    # === NEW: Log sensitivity in audit trail ===
    from apps.audit.models import AuditTrail
    
    if sensitivity_changed:
        AuditTrail.objects.create(
            document=document,
            action='SENSITIVITY_CHANGED',
            user=user,
            details={
                'old_sensitivity': old_sensitivity,
                'new_sensitivity': sensitivity_label,
                'reason': sensitivity_change_reason,
                'changed_during': 'approval',
                'severity': validation_result.get('severity', 'unknown')
            }
        )
    else:
        AuditTrail.objects.create(
            document=document,
            action='SENSITIVITY_CONFIRMED',
            user=user,
            details={
                'sensitivity': sensitivity_label,
                'inherited_from': document.sensitivity_inherited_from.document_number if document.sensitivity_inherited_from else None,
                'confirmed_during': 'approval'
            }
        )
    # === END AUDIT LOGGING ===

    # Determine target state based on effective date
    today = timezone.now().date()
    if effective_date <= today:
        target_state = 'EFFECTIVE'
        comment_suffix = f' - Effective immediately ({effective_date})'
    else:
        target_state = 'APPROVED_PENDING_EFFECTIVE'
        comment_suffix = f' - Pending effective {effective_date}'

    # Transition to appropriate state
    success = self._transition_workflow(
        workflow=workflow,
        to_state_code=target_state,
        user=user,
        comment=(comment or f'Document approved by {user.get_full_name()}') + comment_suffix,
        assignee=None
    )
    
    # Send notifications...
    if success:
        from .author_notifications import author_notification_service
        try:
            notification_sent = author_notification_service.notify_author_approval_completed(
                document=document,
                approver=user,
                approved=True,
                comment=comment,
                effective_date=effective_date
            )
            print(f"✅ Author notification sent for approval completion: {notification_sent}")
            
            if target_state == 'APPROVED_PENDING_EFFECTIVE':
                self._send_scheduled_effective_notification(document, user, effective_date)
                
        except Exception as e:
            print(f"❌ Failed to send author notification: {e}")
            import traceback
            traceback.print_exc()
    
    return success


# ============================================================================
# 2. MODIFY start_version_workflow method (line 582-694)
# ============================================================================

def start_version_workflow(self, existing_document: Document, user: User,
                          new_version_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start up-versioning workflow to create new version and supersede old.
    
    NEW: Inherits sensitivity label from parent document.
    
    Args:
        existing_document: Current effective document
        user: User initiating versioning
        new_version_data: Data for new version (title, description, etc.)
        
    Returns:
        dict: Contains new_document and workflow info
    """
    with transaction.atomic():
        # Validate existing document
        if existing_document.status != 'EFFECTIVE':
            raise ValidationError("Can only version EFFECTIVE documents")
        
        # Create new version
        major, minor = existing_document.get_next_version(
            major_increment=new_version_data.get('major_increment', False)
        )
        
        # Validate version limits
        if major > 99:
            raise ValidationError("Major version cannot exceed 99.")
        if minor > 99:
            raise ValidationError("Minor version cannot exceed 99.")
        
        # Generate versioned document number
        base_doc_number = existing_document.document_number
        if '-v' in base_doc_number:
            base_doc_number = base_doc_number.split('-v')[0]
        
        versioned_doc_number = f"{base_doc_number}-v{major:02d}.{minor:02d}"
        
        # Check for conflicts and resolve them
        conflict_count = 0
        original_versioned_number = versioned_doc_number
        while Document.objects.filter(document_number=versioned_doc_number).exists():
            conflict_count += 1
            if conflict_count == 1:
                minor += 1
                versioned_doc_number = f"{base_doc_number}-v{major:02d}.{minor:02d}"
            elif conflict_count == 2:
                major += 1
                minor = 0
                versioned_doc_number = f"{base_doc_number}-v{major:02d}.{minor:02d}"
            else:
                import uuid
                unique_suffix = str(uuid.uuid4())[:8]
                versioned_doc_number = f"{base_doc_number}-v{major:02d}.{minor:02d}-{unique_suffix}"
                break
                
            if conflict_count > 10:
                raise ValidationError(f"Unable to generate unique document number for version {major}.{minor}")
        
        if conflict_count > 0:
            print(f"Document number conflict resolved: {original_versioned_number} → {versioned_doc_number}")
        
        # === NEW: INHERIT SENSITIVITY LABEL ===
        new_document = Document.objects.create(
            document_number=versioned_doc_number,
            title=new_version_data.get('title', existing_document.title),
            description=new_version_data.get('description', existing_document.description),
            document_type=existing_document.document_type,
            document_source=existing_document.document_source,
            author=user,
            reviewer=new_version_data.get('reviewer', existing_document.reviewer),
            approver=new_version_data.get('approver', existing_document.approver),
            version_major=major,
            version_minor=minor,
            supersedes=existing_document,
            reason_for_change=new_version_data.get('reason_for_change', ''),
            change_summary=new_version_data.get('change_summary', ''),
            status='DRAFT',
            
            # INHERIT SENSITIVITY FROM PARENT
            sensitivity_label=existing_document.sensitivity_label,
            sensitivity_inherited_from=existing_document,
            sensitivity_set_by=None,  # Will be set by approver
            sensitivity_set_at=None,
            sensitivity_change_reason=''
        )
        # === END SENSITIVITY INHERITANCE ===
        
        # Log sensitivity inheritance in audit trail
        from apps.audit.models import AuditTrail
        AuditTrail.objects.create(
            document=new_document,
            action='VERSION_CREATED',
            user=user,
            details={
                'parent_version': f"{existing_document.document_number} v{existing_document.version_major}.{existing_document.version_minor}",
                'inherited_sensitivity': existing_document.sensitivity_label,
                'message': f"New version inherits {existing_document.get_sensitivity_label_display()} classification"
            }
        )
        
        # Copy dependencies from existing document to new version
        self._copy_dependencies_smart(existing_document, new_document, user)
        
        # Start review workflow for new version
        workflow = self.start_review_workflow(
            document=new_document,
            initiated_by=user,
            reviewer=new_document.reviewer,
            approver=new_document.approver
        )
        
        # Use up-versioning workflow type if available
        upversion_type = self.workflow_types.get('UP_VERSION')
        if upversion_type:
            workflow.workflow_type = upversion_type.workflow_type
            workflow.save()
        
        # Send upversion started notification
        self._send_upversion_started_notification(new_document, existing_document, user)
        
        return {
            'new_document': new_document,
            'workflow': workflow,
            'superseded_document': existing_document
        }
