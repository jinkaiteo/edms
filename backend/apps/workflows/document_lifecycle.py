"""
Document Lifecycle Workflows for EDMS

Implements the 4 simple workflows described in EDMS_details_workflow.txt:
1. Review Workflow: DRAFT → PENDING_REVIEW → UNDER_REVIEW → APPROVED → EFFECTIVE
2. Up-versioning Workflow: Create new version and supersede old
3. Obsolete Workflow: Mark documents obsolete with dependency checks
4. Workflow Termination: Return to last approved state

Using the static workflow engine with DocumentState and WorkflowType.
"""

from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from datetime import date
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import DocumentWorkflow, DocumentState, DocumentTransition, WorkflowType
from apps.documents.models import Document

User = get_user_model()


class DocumentLifecycleService:
    """
    Simple document lifecycle service implementing the 4 basic workflows.
    
    Provides straightforward workflow operations without complex configuration,
    focusing on the essential document lifecycle paths.
    """
    
    def __init__(self):
        # Cache commonly used objects
        self._states = None
        self._workflow_types = None
    
    @property
    def states(self):
        """Cached access to document states."""
        if self._states is None:
            self._states = {
                state.code: state for state in DocumentState.objects.all()
            }
        return self._states
    
    @property
    def workflow_types(self):
        """Cached access to workflow types."""
        if self._workflow_types is None:
            self._workflow_types = {
                wt.workflow_type: wt for wt in WorkflowType.objects.filter(is_active=True)
            }
        return self._workflow_types
    
    # =================================================================
    # 1. REVIEW WORKFLOW (Primary document workflow)
    # =================================================================
    
    def start_review_workflow(self, document: Document, initiated_by: User, 
                             reviewer: User = None, approver: User = None) -> DocumentWorkflow:
        """
        Start a standard review workflow for a document.
        
        Workflow Path: DRAFT → PENDING_REVIEW → UNDER_REVIEW → APPROVED → EFFECTIVE
        
        Args:
            document: Document to start workflow for
            initiated_by: User starting the workflow
            reviewer: Optional reviewer assignment
            approver: Optional approver assignment
            
        Returns:
            DocumentWorkflow: Created workflow instance
        """
        with transaction.atomic():
            # Validate document can start workflow
            if document.status not in ['DRAFT']:
                raise ValidationError(f"Cannot start review workflow. Document status: {document.status}")
            
            # Assign reviewer and approver if provided
            if reviewer:
                document.reviewer = reviewer
            if approver:
                document.approver = approver
            document.save()
            
            # Get appropriate workflow type (prefer Document Review for standard process)
            workflow_type = (self.workflow_types.get('REVIEW') or 
                           WorkflowType.objects.filter(workflow_type='REVIEW').first())
            
            if not workflow_type:
                raise ValidationError("No REVIEW workflow type found")
            
            # Create workflow
            workflow = DocumentWorkflow.objects.create(
                document=document,
                workflow_type=workflow_type.workflow_type,  # CRITICAL FIX: Use string value, not model instance
                current_state=self.states['DRAFT'],
                initiated_by=initiated_by,
                current_assignee=document.author,
                due_date=self._calculate_due_date(workflow_type),
                workflow_data={'review_type': 'standard'}
            )
            
            # Set document to initial workflow state
            document.status = 'DRAFT'
            document.save()
            
            return workflow
    
    def submit_for_review(self, document: Document, user: User, 
                         comment: str = '') -> bool:
        """
        Submit document for review (DRAFT → PENDING_REVIEW).
        
        Args:
            document: Document to submit
            user: User submitting (must be author)
            comment: Optional submission comment
            
        Returns:
            bool: True if successful
        """
        print(f"🔍 submit_for_review called for {document.document_number}")
        print(f"   Document status: {document.status}")
        print(f"   User: {user.username}")
        print(f"   Reviewer assigned: {document.reviewer.username if document.reviewer else 'None'}")
        
        # Validate document can be submitted
        if document.status != 'DRAFT':
            print(f"❌ Cannot submit: document status is {document.status}, not DRAFT")
            raise ValidationError(f"Cannot submit document for review. Current status: {document.status}")
        
        # Validate user can submit
        if document.author != user and not user.is_superuser:
            print(f"❌ Cannot submit: user {user.username} is not document author {document.author.username}")
            raise ValidationError("Only document author can submit for review")
        
        # Validate reviewer is assigned
        if not document.reviewer:
            print(f"❌ Cannot submit: no reviewer assigned")
            raise ValidationError("Document must have a reviewer assigned")
        
        # Get or create workflow
        workflow = self._get_active_workflow(document)
        if not workflow:
            print(f"🔧 No active workflow found, creating new workflow...")
            workflow = self.start_review_workflow(
                document=document,
                initiated_by=user,
                reviewer=document.reviewer,
                approver=document.approver
            )
            print(f"   ✅ Workflow created: ID {workflow.id}, state: {workflow.current_state.code}")
        else:
            print(f"✅ Found existing workflow: ID {workflow.id}, state: {workflow.current_state.code}")
        
        # Validate current workflow state
        if workflow.current_state.code != 'DRAFT':
            print(f"❌ Cannot submit from workflow state: {workflow.current_state.code}")
            raise ValidationError(f"Cannot submit from state: {workflow.current_state.code}")
        
        print(f"🔄 Transitioning workflow from DRAFT to PENDING_REVIEW...")
        
        # Execute the transition
        success = self._transition_workflow(
            workflow=workflow,
            to_state_code='PENDING_REVIEW',
            user=user,
            comment=comment or 'Document submitted for review',
            assignee=document.reviewer
        )
        
        print(f"📊 Transition result: {success}")
        
        if success:
            # Refresh document to verify status change
            document.refresh_from_db()
            print(f"✅ Document status after transition: {document.status}")
        else:
            print(f"❌ Transition failed")
        
        return success
    
    def start_review(self, document: Document, user: User, 
                    comment: str = '') -> bool:
        """
        Start reviewing document (PENDING_REVIEW → UNDER_REVIEW).
        
        Args:
            document: Document to start reviewing
            user: User starting review (must be assigned reviewer)
            comment: Optional review start comment
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can review
        if not self._can_review(document, user):
            raise ValidationError("User is not authorized to review this document")
        
        # Validate current state
        if workflow.current_state.code != 'PENDING_REVIEW':
            raise ValidationError(f"Cannot start review from state: {workflow.current_state.code}")
        
        return self._transition_workflow(
            workflow=workflow,
            to_state_code='UNDER_REVIEW',
            user=user,
            comment=comment or 'Review started',
            assignee=user
        )
    
    def complete_review(self, document: Document, user: User, 
                       approved: bool = True, comment: str = '') -> bool:
        """
        Complete document review (UNDER_REVIEW → PENDING_APPROVAL or back to DRAFT).
        
        Args:
            document: Document being reviewed
            user: User completing review
            approved: True if review passed, False to reject back to DRAFT
            comment: Review comment (required)
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can complete review
        if not self._can_review(document, user):
            raise ValidationError("User is not authorized to complete review")
        
        # Validate current state
        if workflow.current_state.code != 'UNDER_REVIEW':
            raise ValidationError(f"Cannot complete review from state: {workflow.current_state.code}")
        
        if not comment:
            raise ValidationError("Review comment is required")
        
        # Complete the workflow transition
        success = False
        if approved:
            # Review approved - transition to REVIEWED state for author to route to approval
            success = self._transition_workflow(
                workflow=workflow,
                to_state_code='REVIEW_COMPLETED',
                user=user,
                comment=comment,
                assignee=document.author  # Return to author to select approver
            )
        else:
            # ENHANCEMENT: Clear reviewer assignment on rejection so author can reassign
            with transaction.atomic():
                # Store rejection info in workflow data for history
                rejected_by_user = document.reviewer
                rejection_comment = comment
                
                # Clear reviewer assignment - author will need to reassign
                document.reviewer = None
                document.save()
                
                # Transition back to draft
                success = self._transition_workflow(
                    workflow=workflow,
                    to_state_code='DRAFT',
                    user=user,
                    comment=f'Review rejected by {user.get_full_name()}: {comment}',
                    assignee=document.author
                )
                
                # Store rejection metadata for history and recommendations
                if success and workflow.workflow_data:
                    workflow.workflow_data.update({
                        'last_rejection': {
                            'type': 'review',
                            'rejected_by': user.id,
                            'rejected_by_name': user.get_full_name(),
                            'rejection_date': timezone.now().isoformat(),
                            'comment': rejection_comment,
                            'previous_reviewer': rejected_by_user.id if rejected_by_user else None
                        }
                    })
                    workflow.save()
        
        # Send notification to author about review completion and create task
        if success:
            from .author_notifications import author_notification_service
            try:
                notification_sent = author_notification_service.notify_author_review_completed(
                    document=document,
                    reviewer=user,
                    approved=approved,
                    comment=comment
                )
                print(f"✅ Author notification sent for review completion: {notification_sent}")
            except Exception as e:
                print(f"❌ Failed to send author notification: {e}")
                import traceback
                traceback.print_exc()
        
        return success
    
    def route_for_approval(self, document: Document, user: User, 
                          approver: User, comment: str = '') -> bool:
        """
        Route document for approval after review completion (REVIEWED → PENDING_APPROVAL).
        
        Args:
            document: Document to route for approval
            user: User routing (must be document author)
            approver: User to assign as approver
            comment: Routing comment
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can route for approval
        if document.author != user and not user.is_superuser:
            raise ValidationError("Only document author can route for approval")
        
        # Validate current state
        if workflow.current_state.code != 'REVIEW_COMPLETED':
            raise ValidationError(f"Cannot route for approval from state: {workflow.current_state.code}")
        
        # Assign approver and route
        document.approver = approver
        document.save()
        
        return self._transition_workflow(
            workflow=workflow,
            to_state_code='PENDING_APPROVAL',
            user=user,
            comment=comment or f'Document routed to {approver.get_full_name()} for approval',
            assignee=approver
        )

    def approve_document(self, document: Document, user: User, 
                        effective_date: date, comment: str = '', approved: bool = True,
                        review_period_months: int = None,
                        sensitivity_label: str = None,
                        sensitivity_change_reason: str = '') -> bool:
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
        
        # === SENSITIVITY LABEL VALIDATION ===
        print(f"🔍 Sensitivity label validation:")
        print(f"   sensitivity_label type: {type(sensitivity_label)}")
        print(f"   sensitivity_label value: {repr(sensitivity_label)}")
        print(f"   bool(sensitivity_label): {bool(sensitivity_label)}")
        
        if not sensitivity_label:
            raise ValidationError("Sensitivity label is required for document approval")
        
        from apps.documents.sensitivity_labels import SENSITIVITY_CHOICES
        valid_labels = [choice[0] for choice in SENSITIVITY_CHOICES]
        if sensitivity_label not in valid_labels:
            raise ValidationError(f"Invalid sensitivity label: {sensitivity_label}. Valid options: {', '.join(valid_labels)}")
        
        # Detect if sensitivity changed from inherited value
        sensitivity_changed = (document.sensitivity_label != sensitivity_label)
        
        if sensitivity_changed and not sensitivity_change_reason:
            raise ValidationError(
                "A detailed reason is required when changing sensitivity classification"
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
            # Calculate next review date from effective date
            from dateutil.relativedelta import relativedelta
            document.next_review_date = effective_date + relativedelta(months=review_period_months)
        else:
            # No periodic review required
            document.review_period_months = None
            document.next_review_date = None
        
        document.save()
        
        # === LOG SENSITIVITY IN AUDIT TRAIL ===
        from apps.audit.models import AuditTrail
        from django.contrib.contenttypes.models import ContentType
        
        if sensitivity_changed:
            AuditTrail.objects.create(
                action='SENSITIVITY_CHANGED',
                user=user,
                content_type=ContentType.objects.get_for_model(document),
                object_id=str(document.id),
                object_representation=f"{document.document_number} - {document.title}",
                description=f"Sensitivity changed from {old_sensitivity} to {sensitivity_label}",
                metadata={
                    'old_sensitivity': old_sensitivity,
                    'new_sensitivity': sensitivity_label,
                    'reason': sensitivity_change_reason,
                    'changed_during': 'approval'
                },
                module='workflows',
                severity='INFO'
            )
        else:
            AuditTrail.objects.create(
                action='SENSITIVITY_CONFIRMED',
                user=user,
                content_type=ContentType.objects.get_for_model(document),
                object_id=str(document.id),
                object_representation=f"{document.document_number} - {document.title}",
                description=f"Sensitivity confirmed as {sensitivity_label}",
                metadata={
                    'sensitivity': sensitivity_label,
                    'inherited_from': document.sensitivity_inherited_from.document_number if document.sensitivity_inherited_from else None,
                    'confirmed_during': 'approval'
                },
                module='workflows',
                severity='INFO'
            )
        # === END AUDIT LOGGING ===

        # Determine target state based on effective date
        today = timezone.now().date()
        if effective_date <= today:
            # Effective today or in the past = immediately effective
            target_state = 'EFFECTIVE'
            comment_suffix = f' - Effective immediately ({effective_date})'
        else:
            # Effective in the future = pending effective
            target_state = 'APPROVED_PENDING_EFFECTIVE'
            comment_suffix = f' - Pending effective {effective_date}'

        # Transition to appropriate state
        success = self._transition_workflow(
            workflow=workflow,
            to_state_code=target_state,
            user=user,
            comment=(comment or f'Document approved by {user.get_full_name()}') + comment_suffix,
            assignee=None  # No further assignment needed for intentional workflow
        )
        
        # Send notification to author about approval completion  
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
                
                # If scheduled for future effective date, send additional notification
                if target_state == 'APPROVED_PENDING_EFFECTIVE':
                    self._send_scheduled_effective_notification(document, user, effective_date)
                    
            except Exception as e:
                print(f"❌ Failed to send author notification: {e}")
                import traceback
                traceback.print_exc()
        
        return success
    
    def reject_document(self, document: Document, user: User, comment: str = '') -> bool:
        """
        Reject document during approval process (PENDING_APPROVAL → DRAFT).
        
        Args:
            document: Document to reject
            user: User rejecting (must be assigned approver)
            comment: Rejection comment (required)
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can reject
        if not self._can_approve(document, user):
            raise ValidationError("User is not authorized to reject this document")
        
        # Validate current state
        if workflow.current_state.code != 'PENDING_APPROVAL':
            raise ValidationError(f"Cannot reject from state: {workflow.current_state.code}")
        
        if not comment:
            raise ValidationError("Rejection comment is required")

        # ENHANCEMENT: Clear both reviewer and approver assignments on approval rejection
        with transaction.atomic():
            # Store rejection info before clearing assignments
            rejected_by_user = document.approver
            previous_reviewer = document.reviewer
            rejection_comment = comment
            
            # Clear both reviewer and approver assignments - author will need to reassign
            document.reviewer = None
            document.approver = None
            document.save()
            
            # Transition back to DRAFT for revision
            success = self._transition_workflow(
                workflow=workflow,
                to_state_code='DRAFT',
                user=user,
                comment=f'Document rejected by {user.get_full_name()}: {comment}',
                assignee=document.author  # Return to author for revision
            )
            
            # Store rejection metadata for history and recommendations
            if success and workflow.workflow_data:
                workflow.workflow_data.update({
                    'last_rejection': {
                        'type': 'approval',
                        'rejected_by': user.id,
                        'rejected_by_name': user.get_full_name(),
                        'rejection_date': timezone.now().isoformat(),
                        'comment': rejection_comment,
                        'previous_reviewer': previous_reviewer.id if previous_reviewer else None,
                        'previous_approver': rejected_by_user.id if rejected_by_user else None
                    }
                })
                workflow.save()
        
        # Send notification to author about rejection
        if success:
            from .author_notifications import author_notification_service
            try:
                notification_sent = author_notification_service.notify_author_approval_completed(
                    document=document,
                    approver=user,
                    approved=False,
                    comment=comment,
                    effective_date=None
                )
                print(f"✅ Author notification sent for document rejection: {notification_sent}")
            except Exception as e:
                print(f"❌ Failed to send author notification: {e}")
                import traceback
                traceback.print_exc()
        
        return success
    
    def activate_pending_effective_documents(self, user: User = None) -> int:
        """
        Scheduler task: Activate documents that are APPROVED_PENDING_EFFECTIVE and due today.
        Called daily at midnight to check and update document statuses.
        
        Args:
            user: System user for audit trail (optional, defaults to system)
            
        Returns:
            int: Number of documents activated
        """
        from django.contrib.auth import get_user_model
        
        if not user:
            User = get_user_model()
            user, _ = User.objects.get_or_create(
                username='system',
                defaults={'first_name': 'System', 'last_name': 'Scheduler', 'is_staff': True}
            )
        
        today = timezone.now().date()
        activated_count = 0
        
        # Find documents that are pending effective and due today or earlier
        pending_docs = Document.objects.filter(
            status='APPROVED_PENDING_EFFECTIVE',
            effective_date__lte=today
        )
        
        for document in pending_docs:
            try:
                with transaction.atomic():
                    workflow = self._get_active_workflow(document)
                    if workflow and workflow.current_state.code == 'APPROVED_PENDING_EFFECTIVE':
                        # Transition to EFFECTIVE
                        success = self._transition_workflow(
                            workflow=workflow,
                            to_state_code='EFFECTIVE',
                            user=user,
                            comment=f'Document automatically activated on scheduled effective date: {document.effective_date}',
                            assignee=None
                        )
                        if success:
                            activated_count += 1
                            
            except Exception as e:
                # Log error but continue processing other documents
                print(f"Failed to activate document {document.document_number}: {e}")
        
        return activated_count
    
    # =================================================================
    # 2. UP-VERSIONING WORKFLOW
    # =================================================================
    
    def start_version_workflow(self, existing_document: Document, user: User,
                              new_version_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start up-versioning workflow to create new version and supersede old.
        
        Process:
        1. Create new document version
        2. Start review workflow for new version
        3. When new version becomes effective, mark old as SUPERSEDED
        
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
            
            # Validate version limits (1-99 for major, 0-99 for minor)
            if major > 99:
                raise ValidationError("Major version cannot exceed 99. Consider starting a new document series.")
            if minor > 99:
                raise ValidationError("Minor version cannot exceed 99. Consider incrementing major version.")
            
            # Generate versioned document number to maintain uniqueness while showing relationship
            # Extract base document number by removing any existing version suffix
            base_doc_number = existing_document.document_number
            if '-v' in base_doc_number:
                # Remove existing version (e.g., "SOP-2025-0001-v1.0" -> "SOP-2025-0001")
                base_doc_number = base_doc_number.split('-v')[0]
            
            versioned_doc_number = f"{base_doc_number}-v{major:02d}.{minor:02d}"
            
            # Check for conflicts and resolve them
            conflict_count = 0
            original_versioned_number = versioned_doc_number
            while Document.objects.filter(document_number=versioned_doc_number).exists():
                conflict_count += 1
                if conflict_count == 1:
                    # Try next minor version
                    minor += 1
                    versioned_doc_number = f"{base_doc_number}-v{major:02d}.{minor:02d}"
                elif conflict_count == 2:
                    # Try next major version
                    major += 1
                    minor = 0
                    versioned_doc_number = f"{base_doc_number}-v{major:02d}.{minor:02d}"
                else:
                    # Add unique suffix to avoid infinite loop
                    import uuid
                    unique_suffix = str(uuid.uuid4())[:8]
                    versioned_doc_number = f"{base_doc_number}-v{major:02d}.{minor:02d}-{unique_suffix}"
                    break
                    
                # Prevent infinite loop
                if conflict_count > 10:
                    raise ValidationError(f"Unable to generate unique document number for version {major}.{minor}")
            
            if conflict_count > 0:
                print(f"Document number conflict resolved: {original_versioned_number} → {versioned_doc_number}")
            
            new_document = Document.objects.create(
                document_number=versioned_doc_number,  # Conflict-free versioned document number
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
                # === INHERIT SENSITIVITY FROM PARENT ===
                sensitivity_label=existing_document.sensitivity_label,
                sensitivity_inherited_from=existing_document,
                sensitivity_set_by=None,  # Will be set by approver
                sensitivity_set_at=None,
                sensitivity_change_reason=''
            )
            
            # Log sensitivity inheritance in audit trail
            from apps.audit.models import AuditTrail
            from django.contrib.contenttypes.models import ContentType
            
            AuditTrail.objects.create(
                action='VERSION_CREATED',
                user=user,
                content_type=ContentType.objects.get_for_model(new_document),
                object_id=str(new_document.id),
                object_representation=f"{new_document.document_number} - {new_document.title}",
                description=f"New version created from {existing_document.document_number}",
                metadata={
                    'parent_version': f"{existing_document.document_number} v{existing_document.version_major}.{existing_document.version_minor}",
                    'inherited_sensitivity': existing_document.sensitivity_label,
                    'message': f"New version inherits {existing_document.get_sensitivity_label_display() if hasattr(existing_document, 'get_sensitivity_label_display') else existing_document.sensitivity_label} classification"
                },
                module='workflows',
                severity='INFO'
            )
            
            # Copy dependencies from existing document to new version (with smart resolution)
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
    
    def complete_versioning(self, new_document: Document, user: User) -> bool:
        """
        Complete versioning by making old document SUPERSEDED.
        Called automatically when new version becomes EFFECTIVE.
        
        Args:
            new_document: New effective document
            user: User completing the versioning
            
        Returns:
            bool: True if successful
        """
        if not new_document.supersedes:
            return True  # Nothing to supersede
        
        if new_document.status != 'EFFECTIVE':
            raise ValidationError("New document must be EFFECTIVE to supersede old version")
        
        with transaction.atomic():
            old_document = new_document.supersedes
            old_document.status = 'SUPERSEDED'
            old_document.obsolete_date = timezone.now().date()
            old_document.save()
            
            # Record transition if old document has workflow
            old_workflow = self._get_active_workflow(old_document)
            if old_workflow:
                self._transition_workflow(
                    workflow=old_workflow,
                    to_state_code='SUPERSEDED',
                    user=user,
                    comment=f'Superseded by {new_document.document_number}',
                    assignee=None
                )
            
            # Send superseded notification
            self._send_superseded_notification(old_document, new_document, user)
        
        return True
    
    # =================================================================
    # 3. OBSOLETE WORKFLOW
    # =================================================================
    
    def start_obsolete_workflow(self, document: Document, user: User,
                               reason: str, target_date: date = None, approver: User = None) -> DocumentWorkflow:
        """
        Start obsolescence workflow with dependency checking.
        
        Args:
            document: Document to make obsolete
            user: User initiating obsolescence
            reason: Reason for obsolescence (required)
            target_date: Target obsolescence date
            
        Returns:
            DocumentWorkflow: Obsolescence workflow
        """
        with transaction.atomic():
            # Validate document can be obsoleted
            if document.status != 'EFFECTIVE':
                raise ValidationError("Can only obsolete EFFECTIVE documents")
            
            if not reason:
                raise ValidationError("Reason for obsolescence is required")
            
            # Check for dependent documents - ENHANCED DEPENDENCY PROTECTION
            # Any document that lists this document as a dependency (regardless of workflow status)
            # must be in a final state (TERMINATED, SUPERSEDED, or OBSOLETE) to allow obsolescence
            from apps.documents.models import DocumentDependency
            
            active_dependents = DocumentDependency.objects.filter(
                depends_on=document
            ).exclude(
                document__status__in=['TERMINATED', 'SUPERSEDED', 'OBSOLETE']
            )
            
            if active_dependents.exists():
                dependent_docs = []
                for dep in active_dependents:
                    dependent_docs.append(f"{dep.document.document_number} (Status: {dep.document.status})")
                
                raise ValidationError(
                    f"Cannot obsolete document while other documents depend on it. "
                    f"The following dependent documents must be terminated, superseded, or obsoleted first: {'; '.join(dependent_docs)}"
                )
            
            # Get obsolete workflow type - use simple string instead of WorkflowType object
            obsolete_workflow_type = 'OBSOLETE'
            
            # Get or update existing workflow for obsolescence
            workflow, created = DocumentWorkflow.objects.get_or_create(
                document=document,
                defaults={
                    'workflow_type': obsolete_workflow_type,
                    'current_state': self.states['PENDING_APPROVAL'],
                    'initiated_by': user,
                    'current_assignee': approver or document.approver or document.author,
                    'due_date': None,
                    'workflow_data': {
                        'obsolete_reason': reason,
                        'target_obsolete_date': target_date.isoformat() if target_date else None
                    }
                }
            )
            
            # If workflow already exists, update it for obsolescence
            if not created:
                workflow.workflow_type = obsolete_workflow_type
                workflow.current_state = self.states['PENDING_APPROVAL']
                workflow.current_assignee = approver or document.approver or document.author
                workflow.workflow_data.update({
                    'obsolete_reason': reason,
                    'target_obsolete_date': target_date.isoformat() if target_date else None
                })
                workflow.save()
            
            return workflow
    
    def obsolete_document_directly(self, document: Document, user: User, 
                                  reason: str, obsolescence_date) -> bool:
        """
        Direct obsolescence for authorized users (approvers/admins).
        No workflow needed - immediate scheduling with notifications.
        
        Args:
            document: Document to obsolete
            user: User with obsolescence authority
            reason: Reason for obsolescence (required)
            obsolescence_date: Date when document becomes obsolete (required) - can be date object or string
            
        Returns:
            bool: True if successfully scheduled
        """
        with transaction.atomic():
            # Validate document can be obsoleted
            if document.status == 'SCHEDULED_FOR_OBSOLESCENCE':
                raise ValidationError(f"Document is already scheduled for obsolescence on {document.obsolescence_date}. Cancel the existing schedule first if you need to change it.")
            elif document.status in ['OBSOLETE', 'SUPERSEDED', 'TERMINATED']:
                raise ValidationError(f"Cannot obsolete document with status: {document.status}")
            elif document.status != 'EFFECTIVE':
                raise ValidationError(f"Can only obsolete EFFECTIVE documents. Current status: {document.status}")
            
            if not reason:
                raise ValidationError("Reason for obsolescence is required")
                
            if not obsolescence_date:
                raise ValidationError("Obsolescence date is required")
            
            # Convert string date to date object if needed
            if isinstance(obsolescence_date, str):
                from datetime import datetime
                try:
                    obsolescence_date = datetime.strptime(obsolescence_date, '%Y-%m-%d').date()
                except ValueError as e:
                    raise ValidationError(f"Invalid date format. Expected YYYY-MM-DD, got: {obsolescence_date}")
            
            today = timezone.now().date()
            if obsolescence_date <= today:
                raise ValidationError(f"Obsolescence date must be in the future. Today is {today}, provided date is {obsolescence_date}")
            
            # Enhanced conflict detection
            self._validate_obsolescence_eligibility(document)
            
            # Validate user authority
            has_authority = (
                user == document.approver or
                user.is_staff or
                user.is_superuser
            )
            
            if not has_authority:
                raise ValidationError("User does not have authority to obsolete this document")
            
            # Update document status to scheduled for obsolescence
            document.status = 'SCHEDULED_FOR_OBSOLESCENCE'
            document.obsolescence_date = obsolescence_date
            document.obsolescence_reason = reason
            document.obsoleted_by = user
            document.save()
            
            # Create audit trail record (using existing audit system)
            from apps.audit.models import LoginAudit  # Use existing audit model pattern
            # TODO: Integrate with proper audit system for document obsolescence
            print(f"📋 Audit: Document {document.document_number} scheduled for obsolescence by {user.username}")
            
            # Send immediate notifications
            self._send_obsolescence_notifications(
                document=document,
                user=user,
                reason=reason,
                obsolescence_date=obsolescence_date,
                notification_type='scheduled'
            )
            
            print(f"✅ Document {document.document_number} scheduled for obsolescence on {obsolescence_date}")
            return True

    def _validate_obsolescence_eligibility(self, document: Document):
        """Enhanced validation for obsolescence eligibility with conflict detection."""
        # Check for dependent documents - ENHANCED DEPENDENCY PROTECTION
        # Any document that lists this document as a dependency (regardless of workflow status)
        # must be in a final state (TERMINATED, SUPERSEDED, or OBSOLETE) to allow obsolescence
        from apps.documents.models import DocumentDependency
        
        active_dependents = DocumentDependency.objects.filter(
            depends_on=document,
            is_active=True
        ).exclude(
            document__status__in=['TERMINATED', 'SUPERSEDED', 'OBSOLETE']
        )
        
        if active_dependents.exists():
            dependent_docs = []
            for dep in active_dependents:
                dependent_docs.append(f"{dep.document.document_number} (Status: {dep.document.status})")
            
            raise ValidationError(
                f"Cannot obsolete document while other documents depend on it. "
                f"The following dependent documents must be terminated, superseded, or obsoleted first: {'; '.join(dependent_docs)}"
            )
        
        # Check for active workflows on this document
        active_workflows = DocumentWorkflow.objects.filter(
            document=document,
            workflow_type__in=['REVIEW', 'UP_VERSION'],
            is_terminated=False  # Only consider non-terminated workflows as active
        ).exclude(current_state__code__in=['TERMINATED', 'COMPLETED', 'OBSOLETE', 'EFFECTIVE'])
        
        if active_workflows.exists():
            workflow_types = [w.workflow_type for w in active_workflows]
            raise ValidationError(
                f"Cannot obsolete document with active workflows: {', '.join(workflow_types)}"
            )
        
        # Check if document is already scheduled for obsolescence
        if document.status == 'SCHEDULED_FOR_OBSOLESCENCE':
            raise ValidationError("Document is already scheduled for obsolescence")
            
        # CRITICAL: Check for newer versions in development/review
        self._validate_no_newer_versions_in_development(document)
    
    def _validate_no_newer_versions_in_development(self, document: Document):
        """
        Prevent obsolescence if newer versions of this document are being developed.
        This ensures continuity of documented processes and regulatory compliance.
        """
        # Extract base document number (remove version suffix if present)
        base_number = document.document_number
        if '-v' in base_number:
            base_number = base_number.split('-v')[0]
        
        # Find all documents with the same base number
        related_documents = Document.objects.filter(
            document_number__startswith=base_number
        ).exclude(id=document.id)
        
        # Check for newer versions in development/review
        problematic_versions = []
        
        for related_doc in related_documents:
            # Skip if this is an older version
            if (related_doc.version_major < document.version_major or 
                (related_doc.version_major == document.version_major and 
                 related_doc.version_minor <= document.version_minor)):
                continue
                
            # Check if newer version is in development/review
            if related_doc.status in [
                'DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEW_COMPLETED',
                'PENDING_APPROVAL', 'UNDER_APPROVAL', 'APPROVED'
            ]:
                version_str = f"v{related_doc.version_major}.{related_doc.version_minor}"
                problematic_versions.append(f"{related_doc.document_number} ({version_str}) - {related_doc.status}")
        
        if problematic_versions:
            raise ValidationError(
                f"Cannot obsolete document while newer versions are in development. "
                f"Complete or terminate these workflows first: {'; '.join(problematic_versions)}"
            )
        
        # Check for active up-versioning workflows on related documents
        active_version_workflows = DocumentWorkflow.objects.filter(
            document__document_number__startswith=base_number,
            workflow_type='UP_VERSION'
        ).exclude(
            current_state__code__in=['TERMINATED', 'COMPLETED', 'OBSOLETE']
        ).exclude(document=document)
        
        if active_version_workflows.exists():
            active_docs = [
                f"{wf.document.document_number} ({wf.workflow_type})" 
                for wf in active_version_workflows
            ]
            raise ValidationError(
                f"Cannot obsolete document while up-versioning workflows are active: {'; '.join(active_docs)}"
            )

    def _send_obsolescence_notifications(self, document: Document, user: User, 
                                       reason: str, obsolescence_date: date, notification_type: str):
        """Send notifications for obsolescence events."""
        # Get notification recipients
        recipients = self._get_obsolescence_notification_recipients(document)
        
        notification_data = {
            'document_number': document.document_number,
            'document_title': document.title,
            'obsoleted_by': user.get_full_name(),
            'reason': reason,
            'obsolescence_date': obsolescence_date.isoformat(),
            'notification_type': notification_type
        }
        
        if notification_type == 'scheduled':
            subject = f"Document Scheduled for Obsolescence: {document.document_number}"
            message = f"""
            Document {document.document_number} - {document.title} has been scheduled for obsolescence.
            
            Obsoleted by: {user.get_full_name()}
            Reason: {reason}
            Obsolescence Date: {obsolescence_date.strftime('%Y-%m-%d')}
            
            The document will become obsolete on the specified date.
            All stakeholders will be notified when obsolescence takes effect.
            """
        else:  # notification_type == 'activated'
            subject = f"Document Now Obsolete: {document.document_number}"
            message = f"""
            Document {document.document_number} - {document.title} is now OBSOLETE.
            
            This document is no longer valid and should not be used.
            Please ensure any references to this document are updated.
            """
        
        # Send actual email notifications
        from django.core.mail import send_mail
        from django.conf import settings
        
        for recipient in recipients:
            try:
                send_mail(
                    subject,
                    message.strip(),
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                    fail_silently=False
                )
                print(f"📧 Email sent to {recipient.email}: {subject}")
            except Exception as e:
                print(f"❌ Failed to send email to {recipient.email}: {e}")
        
        # Log notification activity
        print(f"📋 Obsolescence notifications sent: {len(recipients)} recipients")

    def _get_obsolescence_notification_recipients(self, document: Document):
        """Get list of users who should be notified about obsolescence."""
        recipients = set()
        
        # Always notify document stakeholders
        if document.author:
            recipients.add(document.author)
        if document.approver:
            recipients.add(document.approver)
        if document.reviewer:
            recipients.add(document.reviewer)
            
        # Notify users with dependent documents
        dependent_doc_authors = User.objects.filter(
            authored_documents__dependencies__depends_on=document,
            authored_documents__dependencies__is_active=True
        ).distinct()
        recipients.update(dependent_doc_authors)
        
        # Notify department/role-based stakeholders
        # TODO: Add department-based notification logic if needed
        
        return list(recipients)
    
    def _send_superseded_notification(self, old_document: Document, new_document: Document, user: User):
        """Send notification when document is superseded by new version."""
        from django.core.mail import send_mail
        from django.conf import settings
        
        recipients = self._get_obsolescence_notification_recipients(old_document)
        
        subject = f"Document Superseded: {old_document.document_number} replaced by {new_document.document_number}"
        message = f"""
Document Superseded - New Version Available

Old Document: {old_document.document_number} v{old_document.version_major}.{old_document.version_minor:02d} - {old_document.title}
Status: SUPERSEDED

New Document: {new_document.document_number} v{new_document.version_major}.{new_document.version_minor:02d} - {new_document.title}
Status: EFFECTIVE

Superseded by: {user.get_full_name()}
Date: {timezone.now().strftime('%Y-%m-%d')}

ACTION REQUIRED:
Please update any references to use the new document version.
The old version is no longer valid and should not be used.

Access the new document in EDMS: {settings.FRONTEND_URL}/document-management

---
This is an automated notification from the EDMS system.
        """.strip()
        
        for recipient in recipients:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                    fail_silently=False
                )
                print(f"📧 Superseded notification sent to {recipient.email}")
            except Exception as e:
                print(f"❌ Failed to send superseded notification to {recipient.email}: {e}")
    
    def _send_scheduled_effective_notification(self, document: Document, user: User, effective_date: date):
        """Send notification when document is approved with future effective date."""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"Document Scheduled to Become Effective: {document.document_number}"
        message = f"""
Document Approved - Scheduled for Effectiveness

Document: {document.document_number} v{document.version_major}.{document.version_minor:02d} - {document.title}
Current Status: APPROVED (Pending Effective Date)
Scheduled Effective Date: {effective_date.strftime('%Y-%m-%d')}

Approved by: {user.get_full_name()}
Approval Date: {timezone.now().strftime('%Y-%m-%d')}

Your document has been approved and will automatically become effective on {effective_date.strftime('%Y-%m-%d')}.
You will receive another notification when the document becomes effective.

Until the effective date, the document is not yet available for use.

Access EDMS: {settings.FRONTEND_URL}/document-management

---
This is an automated notification from the EDMS system.
        """.strip()
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [document.author.email],
                fail_silently=False
            )
            print(f"📧 Scheduled effective notification sent to {document.author.email}")
        except Exception as e:
            print(f"❌ Failed to send scheduled effective notification: {e}")
    
    def _send_upversion_started_notification(self, new_document: Document, old_document: Document, user: User):
        """Send notification when document upversion/revision process is started."""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"New Document Version Created: {new_document.document_number}"
        message = f"""
New Document Version Created - Review Workflow Started

New Version: {new_document.document_number} v{new_document.version_major}.{new_document.version_minor:02d} - {new_document.title}
Previous Version: {old_document.document_number} v{old_document.version_major}.{old_document.version_minor:02d}
Status: DRAFT (In Review Workflow)

Created by: {user.get_full_name()}
Created Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

Reason for Change: {new_document.reason_for_change or 'Not specified'}
Change Summary: {new_document.change_summary or 'Not specified'}

NEXT STEPS:
1. The new version is now in DRAFT status
2. It will go through the standard review and approval workflow
3. Reviewer: {new_document.reviewer.get_full_name() if new_document.reviewer else 'Not assigned'}
4. Approver: {new_document.approver.get_full_name() if new_document.approver else 'Not assigned'}

The new version will be routed for review automatically. You will receive notifications
as it progresses through the review and approval workflow.

The previous version ({old_document.document_number}) will remain EFFECTIVE until the new 
version is approved and becomes effective.

Access EDMS: {settings.FRONTEND_URL}/document-management

---
This is an automated notification from the EDMS system.
        """.strip()
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [new_document.author.email],
                fail_silently=False
            )
            print(f"📧 Upversion started notification sent to {new_document.author.email}")
        except Exception as e:
            print(f"❌ Failed to send upversion started notification: {e}")

    def approve_obsolescence(self, document: Document, user: User,
                            comment: str = '') -> bool:
        """
        Approve document obsolescence (PENDING_APPROVAL → OBSOLETE).
        
        Args:
            document: Document to obsolete
            user: User approving obsolescence
            comment: Approval comment
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow or 'OBSOLETE' not in workflow.workflow_type:
            raise ValidationError("No active obsolescence workflow found")
        
        # Validate user can approve obsolescence
        if not self._can_approve(document, user):
            raise ValidationError("User is not authorized to approve obsolescence")
        
        success = self._transition_workflow(
            workflow=workflow,
            to_state_code='OBSOLETE',
            user=user,
            comment=comment or 'Obsolescence approved',
            assignee=None
        )
        
        if success:
            # Update document
            document.status = 'OBSOLETE'
            document.obsolete_date = timezone.now().date()
            document.save()
        
        return success
    
    # =================================================================
    # REJECTION HISTORY AND ASSIGNMENT RECOMMENDATIONS
    # =================================================================
    
    def get_rejection_history(self, document: Document) -> List[Dict[str, Any]]:
        """
        Get complete rejection history for a document to help authors make informed decisions.
        
        Args:
            document: Document to get rejection history for
            
        Returns:
            List of rejection events with details
        """
        # Get rejection history from transitions
        workflow = DocumentWorkflow.objects.filter(document=document).first()
        if not workflow:
            return []
        
        rejection_transitions = DocumentTransition.objects.filter(
            workflow=workflow,
            to_state__code='DRAFT',
            comment__icontains='rejected'
        ).select_related('transitioned_by', 'from_state', 'to_state').order_by('-transitioned_at')
        
        rejections = []
        for transition in rejection_transitions:
            # Extract rejection type from comment or workflow data
            rejection_type = 'review' if 'review rejected' in transition.comment.lower() else 'approval'
            
            rejections.append({
                'rejection_date': transition.transitioned_at,
                'rejection_type': rejection_type,
                'rejected_by': transition.transitioned_by.get_full_name(),
                'rejected_by_username': transition.transitioned_by.username,
                'from_state': transition.from_state.name,
                'comment': transition.comment,
                'can_contact': True  # Author can contact the rejector for clarification
            })
        
        return rejections
    
    def get_assignment_recommendations(self, document: Document) -> Dict[str, Any]:
        """
        Get smart recommendations for reviewer/approver assignment based on rejection history.
        
        Args:
            document: Document to get recommendations for
            
        Returns:
            Dictionary with recommendations and warnings
        """
        rejection_history = self.get_rejection_history(document)
        
        # Get previously rejected reviewers/approvers
        rejected_reviewers = set()
        rejected_approvers = set()
        
        for rejection in rejection_history:
            if rejection['rejection_type'] == 'review':
                rejected_reviewers.add(rejection['rejected_by_username'])
            elif rejection['rejection_type'] == 'approval':
                rejected_approvers.add(rejection['rejected_by_username'])
        
        # Get last rejection info from workflow data if available
        workflow = DocumentWorkflow.objects.filter(document=document).first()
        last_rejection_from_data = None
        if workflow and hasattr(workflow, 'workflow_data') and workflow.workflow_data:
            last_rejection_from_data = workflow.workflow_data.get('last_rejection')
        
        recommendations = {
            'has_rejections': len(rejection_history) > 0,
            'rejection_count': len(rejection_history),
            'previously_rejected_reviewers': list(rejected_reviewers),
            'previously_rejected_approvers': list(rejected_approvers),
            'latest_rejection': rejection_history[0] if rejection_history else None,
            'latest_rejection_details': last_rejection_from_data,
            'recommendations': {
                'prefer_same_reviewer': len(rejected_reviewers) > 0,  # ENCOURAGE same reviewer for continuity
                'prefer_same_approver': len(rejected_approvers) > 0,  # ENCOURAGE same approver for continuity  
                'review_rejection_comments': len(rejection_history) > 0,
                'address_concerns_first': len(rejection_history) > 0,
                'continuity_recommended': len(rejection_history) > 0  # Overall recommendation for continuity
            }
        }
        
        return recommendations

    # =================================================================
    # 4. WORKFLOW TERMINATION
    # =================================================================
    
    def terminate_workflow(self, document: Document, user: User,
                          reason: str) -> bool:
        """
        Terminate active workflow and return document to last approved state.
        
        Args:
            document: Document with workflow to terminate
            user: User terminating workflow
            reason: Reason for termination (required)
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow to terminate")
        
        if not reason:
            raise ValidationError("Reason for termination is required")
        
        # Validate user can terminate
        if (document.author != user and 
            not self._can_approve(document, user) and 
            not user.is_superuser):
            raise ValidationError("User not authorized to terminate workflow")
        
        with transaction.atomic():
            # Determine return state based on document history
            return_state = self._determine_return_state(document)
            
            # Terminate workflow
            success = self._transition_workflow(
                workflow=workflow,
                to_state_code='TERMINATED',
                user=user,
                comment=f'Workflow terminated: {reason}',
                assignee=None
            )
            
            if success:
                # Update document to return state
                document.status = return_state
                document.save()
                
                # Note: DocumentWorkflow doesn't have is_active/completed_at fields
                # The workflow state is already set to TERMINATED above
        
        return success
    
    # =================================================================
    # UTILITY METHODS
    # =================================================================
    
    def get_document_workflow_status(self, document: Document) -> Dict[str, Any]:
        """Get current workflow status for a document."""
        workflow = self._get_active_workflow(document)
        
        if not workflow:
            return {
                'has_active_workflow': False,
                'document_status': document.status,
                'next_actions': self._get_available_actions(document, None)
            }
        
        return {
            'has_active_workflow': True,
            'workflow_type': workflow.workflow_type,
            'current_state': workflow.current_state.code,
            'current_assignee': workflow.current_assignee.username if workflow.current_assignee else None,
            'started_at': workflow.created_at,
            'due_date': workflow.due_date,
            'is_overdue': workflow.due_date and workflow.due_date < timezone.now(),
            'document_status': document.status,
            'next_actions': self._get_available_actions(document, workflow)
        }
    
    def _get_active_workflow(self, document: Document) -> Optional[DocumentWorkflow]:
        """Get active workflow for a document."""
        # DocumentWorkflow doesn't have is_active field, so get the most recent one
        return DocumentWorkflow.objects.filter(
            document=document
        ).order_by('-created_at').first()
    
    def _transition_workflow(self, workflow: DocumentWorkflow, to_state_code: str,
                           user: User, comment: str, assignee: User = None) -> bool:
        """Execute a workflow state transition."""
        try:
            with transaction.atomic():
                from_state = workflow.current_state
                to_state = self.states[to_state_code]
                
                # Create transition record
                transition = DocumentTransition.objects.create(
                    workflow=workflow,
                    from_state=from_state,
                    to_state=to_state,
                    transitioned_by=user,
                    comment=comment,
                    transition_data={'assignee': assignee.username if assignee else None}
                )
                
                # Update workflow state
                workflow.current_state = to_state
                workflow.current_assignee = assignee
                workflow.save()
                print(f"✅ Workflow state updated to: {workflow.current_state.code}")
                
                # Update document status - CRITICAL FIX: Force refresh and verify save
                document = workflow.document
                document.status = to_state_code
                document.save()
                
                # Verify the save actually worked
                document.refresh_from_db()
                print(f"✅ Document status updated to: {document.status}")
                print(f"✅ Database verification: {document.status == to_state_code}")
                
                if document.status != to_state_code:
                    print(f"❌ CRITICAL: Document status save failed!")
                    print(f"   Expected: {to_state_code}, Got: {document.status}")
                    return False
                
                # CRITICAL FIX: Defer task creation to prevent transaction rollback
                # Task creation moved to post-transaction to prevent database errors from affecting main workflow
                
                # Handle post-transition actions
                self._handle_post_transition(workflow, transition)
                
                # Complete current assignee's existing task before creating new one
                if workflow.current_assignee and workflow.current_assignee != assignee:
                    from django.db import transaction as db_transaction
                    db_transaction.on_commit(
                        lambda: self._complete_current_task_safe(workflow.current_assignee.id, workflow.document.document_number, user.id)
                    )
                
                # Schedule task creation after transaction commits successfully
                if assignee:
                    from django.db import transaction as db_transaction
                    db_transaction.on_commit(
                        lambda: self._create_workflow_task_safe(workflow.id, to_state.code, assignee.id, user.id, comment)
                    )
                
                return True
                
        except Exception as e:
            # Log error for debugging
            print(f"Workflow transition failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_workflow_task_for_assignee(self, workflow: DocumentWorkflow, to_state, 
                                          assignee: User, transitioned_by: User, comment: str):
        """Create WorkflowTask when workflow is assigned to a user."""
        if not assignee:
            return
            
        try:
            # Use ScheduledTask with metadata for task tracking
            from ..scheduler.models import ScheduledTask
            document = workflow.document
            
            # Determine task type and details based on state
            task_mapping = {
                'PENDING_REVIEW': {
                    'task_type': 'REVIEW',
                    'name': f'Review Document: {document.document_number}',
                    'description': f'Review "{document.title}" and provide feedback. Document submitted by {transitioned_by.get_full_name()}.',
                    'priority': 'normal',
                    'due_days': 5
                },
                'PENDING_APPROVAL': {
                    'task_type': 'APPROVE', 
                    'name': f'Approve Document: {document.document_number}',
                    'description': f'Final approval required for "{document.title}". Document has passed review stage.',
                    'priority': 'high',
                    'due_days': 3
                },
                'UNDER_REVIEW': {
                    'task_type': 'REVIEW',
                    'name': f'Continue Review: {document.document_number}',
                    'description': f'Continue reviewing "{document.title}". Review started by {transitioned_by.get_full_name()}.',
                    'priority': 'normal',
                    'due_days': 3
                }
            }
            
            task_config = task_mapping.get(to_state.code)
            if task_config:
                # Check if task already exists to avoid duplicates
                existing_task = ScheduledTask.objects.filter(
                    name__icontains=document.document_number,
                    metadata__assignee=assignee.username,
                    status='PENDING',
                    task_type='workflow_task'
                ).first()
                
                if not existing_task:
                    # Create a scheduled task that represents the workflow task
                    due_date = timezone.now() + timezone.timedelta(days=task_config['due_days'])
                    
                    task = ScheduledTask.objects.create(
                        name=task_config['name'],
                        description=task_config['description'], 
                        task_type='workflow_task',
                        task_function='workflow.task.execute',
                        task_module='apps.workflows.tasks',
                        status='PENDING',
                        created_by=transitioned_by,
                        metadata={
                            'assignee': assignee.username,
                            'assignee_id': assignee.id,
                            'task_type': task_config['task_type'],
                            'document_id': document.id,
                            'document_uuid': str(document.uuid),
                            'document_number': document.document_number,
                            'document_title': document.title,
                            'workflow_id': workflow.id,
                            'workflow_uuid': str(workflow.uuid),
                            'state_code': to_state.code,
                            'transition_comment': comment,
                            'priority': task_config['priority'],
                            'due_date': due_date.isoformat(),
                            'assigned_by': transitioned_by.username,
                            'assigned_by_id': transitioned_by.id
                        }
                    )
                    print(f"✅ Created workflow task for {assignee.username}: {task_type}")
                    
                    # Notification is now handled separately to prevent transaction rollback
                else:
                    print(f"ℹ️ Task already exists for {assignee.username} on document {document.document_number}")
                    
        except Exception as e:
            print(f"❌ Failed to create workflow task: {e}")
            import traceback
            traceback.print_exc()

    def _send_task_assignment_notification_simple(self, task, assigned_by: User, assignee: User):
        """Send notification when a task is assigned."""
        try:
            from ..scheduler.notification_service import notification_service
            
            task_metadata = task_metadata
            due_date_str = task_metadata.get('due_date', timezone.now().isoformat())[:10]  # Get date part only
            
            subject = f"New Task Assigned: {task_type}"
            message = f"""
You have been assigned a new workflow task.

Task: {task_type}
Description: {task_type + " task"}
Priority: {task_metadata.get('priority', 'normal').upper()}
Due Date: {due_date_str}
Assigned by: {assigned_by.get_full_name()}

Please log into EDMS to complete this task:
{settings.FRONTEND_URL}/my-tasks

Document Details:
- Number: {task_metadata.get('document_number', 'N/A')}
- Title: {task_metadata.get('document_title', 'N/A')}
            """.strip()
            
            notification_service.send_immediate_notification(
                recipients=[assignee],
                subject=subject,
                message=message,
                notification_type='TASK_ASSIGNED'
            )
            print(f"📧 Sent task assignment notification to {assignee.username}")
        except Exception as e:
            print(f"❌ Failed to send task assignment notification: {e}")

    def _handle_post_transition(self, workflow: DocumentWorkflow, 
                              transition: DocumentTransition):
        """Handle actions after successful transition."""
        # Auto-complete versioning when new version becomes effective
        if (transition.to_state.code in ['EFFECTIVE'] and 
            workflow.document.supersedes):
            self.complete_versioning(workflow.document, transition.transitioned_by)
    
    def _calculate_due_date(self, workflow_type: WorkflowType):
        """Calculate due date based on workflow type."""
        if workflow_type.timeout_days:
            return timezone.now() + timezone.timedelta(days=workflow_type.timeout_days)
        return None

    def _send_task_assignment_notification_safe(self, task, assigned_by: User, assignee: User):
        """Send notification when a task is assigned - safe version that doesn't affect transactions."""
        try:
            # Import notification service
            from apps.scheduler.notification_service import notification_service
            
            # Get task details from the task parameter
            task_type = getattr(task, 'task_type', 'Workflow Task')
            
            # Create notification data
            notification_data = {
                'task_id': str(task.uuid) if hasattr(task, 'uuid') else 'unknown',
                'task_name': task_type,
                'task_description': task_type + " task",
                'document_number': task.task_data.get('document_number', 'Unknown') if hasattr(task, 'task_data') else 'Unknown',
                'document_uuid': task.task_data.get('document_uuid', '') if hasattr(task, 'task_data') else '',
                'assigned_by': assigned_by.get_full_name(),
                'due_date': task.due_date.isoformat() if hasattr(task, 'due_date') and task.due_date else None,
                'priority': getattr(task, 'priority', 'NORMAL')
            }
            
            # Send the notification - just send email, don't store in database to avoid field type issues
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = f"New Task Assigned: {task_type}"
            message = f"""You have been assigned a new workflow task.

Task: {task_type}
Description: {task_type + " task"}
Priority: {notification_data['priority']}
Due Date: {task.due_date or 'Not specified' if hasattr(task, 'due_date') else 'Not specified'}
Assigned by: {assigned_by.get_full_name()}

Please log into EDMS to complete this task:
{settings.FRONTEND_URL}/my-tasks

Document Details:
- Number: {notification_data['document_number']}
"""
            
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@edms-project.com'),
                [assignee.email],
                fail_silently=True
            )
            
            print(f"📧 Sent task assignment notification to {assignee.username}")
            
        except Exception as e:
            print(f"⚠️ Failed to send task assignment notification (non-critical): {e}")
            # Don't re-raise - notification failures shouldn't break workflow transitions
    
    def _send_task_notification_simple(self, task, assigned_by: User, assignee: User):
        """Send simple email notification without database storage to avoid transaction issues."""
        try:
            from apps.scheduler.notification_service import notification_service
            
            # Get task type from the task object
            task_type = getattr(task, 'task_type', 'Document Review')
            priority = getattr(task, 'priority', 'Normal')
            due_date = getattr(task, 'due_date', None)
            task_data = getattr(task, 'task_data', {})
            
            # Skip notification for states handled by author notification service
            # This prevents duplicate emails to the author
            action_required = task_data.get('action_required', '')
            
            # REVIEW_COMPLETED: author_notification_service sends detailed email
            # No need for generic "New Task Assigned" email
            if action_required == 'REVIEW_COMPLETED':
                print(f"⏭️ Skipping generic task notification for {action_required} - author notification service handles this")
                return
            
            # DRAFT (rejection): author_notification_service sends detailed email
            # No need for generic task email
            if action_required == 'DRAFT' or task_type == 'Revise Document':
                print(f"⏭️ Skipping generic task notification for rejection - author notification service handles this")
                return
            
            # Also skip if going back to DRAFT state (rejection scenario)
            # The author_notification_service.notify_author_review_completed() handles rejection emails
            if 'rejected' in task_type.lower() or 'revision' in task_type.lower():
                print(f"⏭️ Skipping task notification for rejection/revision - dedicated notification already sent")
                return
            
            subject = f"New Task Assigned: {task_type}"
            message = f"""You have been assigned a new workflow task.

Task: {task_type}
Description: {task_type} task
Priority: {priority}
Due Date: {due_date or 'Not specified'}
Assigned by: {assigned_by.get_full_name() or assigned_by.username}

Please log into EDMS to complete this task:
{settings.FRONTEND_URL}/my-tasks

Document Details:
- Number: {task_data.get('document_number', 'Unknown')}
"""
            
            # Use the correct notification service method signature
            success = notification_service.send_immediate_notification(
                recipients=[assignee],  # Pass list of User objects
                subject=subject,
                message=message,
                notification_type='TASK_ASSIGNMENT'
            )
            
            print(f"📧 Sent task notification to {assignee.username}: {success}")
            
        except Exception as e:
            print(f"⚠️ Failed to send task notification: {e}")
    
    def _complete_current_task_safe(self, current_assignee_id: int, document_number: str, completed_by_id: int):
        """Complete current assignee's task safely after transaction commits."""
        try:
            from .models import WorkflowTask
            from django.contrib.auth import get_user_model
            from django.utils import timezone
            
            User = get_user_model()
            current_assignee = User.objects.get(id=current_assignee_id)
            completed_by = User.objects.get(id=completed_by_id)
            
            # Find and complete the pending task for current assignee on this document
            pending_task = WorkflowTask.objects.filter(
                assigned_to=current_assignee,
                status='PENDING',
                task_data__document_number=document_number
            ).first()
            
            if pending_task:
                pending_task.status = 'COMPLETED'
                pending_task.completed_at = timezone.now()
                pending_task.completion_note = f'Task completed via workflow transition by {completed_by.username}'
                pending_task.save()
                print(f"✅ Marked existing task as COMPLETED for {current_assignee.username}")
            else:
                print(f"ℹ️ No pending task found for {current_assignee.username} on document {document_number}")
                
        except Exception as e:
            print(f"⚠️ Task completion failed (non-critical): {e}")

    def _create_workflow_task_safe(self, workflow_id: int, state_code: str, assignee_id: int, transitioned_by_id: int, comment: str):
        """Create workflow task safely after transaction commits."""
        try:
            from .models import DocumentWorkflow, DocumentState
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            workflow = DocumentWorkflow.objects.get(id=workflow_id)
            to_state = DocumentState.objects.get(code=state_code)
            assignee = User.objects.get(id=assignee_id)
            transitioned_by = User.objects.get(id=transitioned_by_id)
            
            # Create task without affecting the main transaction
            task = self._create_workflow_task_for_assignee(workflow, to_state, assignee, transitioned_by, comment)
            if task:
                print(f"✅ Post-commit task creation successful")
            
        except Exception as e:
            print(f"⚠️ Post-commit task creation failed (non-critical): {e}")
    
    def _create_workflow_task_for_assignee(self, workflow: DocumentWorkflow, to_state,
                                           assignee: User, transitioned_by: User, comment: str):
        """Create WorkflowTask when workflow is assigned to a user."""
        try:
            from .models import WorkflowTask, WorkflowInstance, WorkflowType
            from django.contrib.contenttypes.models import ContentType
            
            # Get or create WorkflowInstance to bridge DocumentWorkflow and WorkflowTask
            workflow_instance = self._get_or_create_workflow_instance(workflow, transitioned_by)
            
            # Determine task type based on state
            task_type_map = {
                'PENDING_REVIEW': 'REVIEW',
                'PENDING_APPROVAL': 'APPROVE', 
                'REVIEW_COMPLETED': 'REVIEW'
            }
            
            task_type = task_type_map.get(to_state.code, 'REVIEW')
            
            # Create the task with proper schema alignment
            task = WorkflowTask.objects.create(
                workflow_instance=workflow_instance,  # Required field
                name=f"Review Document - {workflow.document.document_number}",
                description=f"Review document {workflow.document.document_number} - {workflow.document.title}",
                task_type=task_type,
                assigned_to=assignee,
                assigned_by=transitioned_by,
                status='PENDING',
                priority='NORMAL',
                due_date=workflow.due_date,
                task_data={
                    'document_uuid': str(workflow.document.uuid),
                    'document_workflow_id': workflow.id,
                    'document_number': workflow.document.document_number,
                    'action_required': to_state.code,
                    'comment': comment
                },
                metadata={
                    'workflow_type': workflow.workflow_type,
                    'current_state': to_state.code,
                    'bridge_mode': 'document_workflow'  # Indicate this is bridged
                }
            )
            
            print(f"✅ Created workflow task {workflow_task.uuid} for {assignee.username}")
            
            # Send notification separately to avoid transaction rollback
            try:
                self._send_task_notification_simple(task, transitioned_by, assignee)
            except Exception as notif_error:
                print(f"⚠️ Task created but notification failed: {notif_error}")
            
            return task
            
        except Exception as e:
            print(f"❌ Failed to create workflow task: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_or_create_workflow_instance(self, workflow: DocumentWorkflow, user: User):
        """Get or create WorkflowInstance to bridge DocumentWorkflow and WorkflowTask systems."""
        try:
            from .models import WorkflowInstance, WorkflowType
            from django.contrib.contenttypes.models import ContentType
            
            # Try to find existing WorkflowInstance for this document
            document_ct = ContentType.objects.get_for_model(workflow.document)
            
            instance = WorkflowInstance.objects.filter(
                content_type=document_ct,
                object_id=str(workflow.document.uuid)
            ).first()
            
            if not instance:
                # Get or create workflow type
                workflow_type, created = WorkflowType.objects.get_or_create(
                    workflow_type='REVIEW',
                    defaults={
                        'name': 'Document Review Workflow',
                        'description': 'Standard document review workflow',
                        'created_by': user
                    }
                )
                
                # Create new WorkflowInstance
                instance = WorkflowInstance.objects.create(
                    workflow_type=workflow_type,
                    content_type=document_ct,
                    object_id=str(workflow.document.uuid),
                    initiated_by=user,
                    current_assignee=workflow.current_assignee,
                    state=workflow.current_state.code,
                    due_date=workflow.due_date,
                    workflow_data={
                        'document_workflow_id': workflow.id,
                        'bridge_mode': True
                    }
                )
                print(f"✅ Created WorkflowInstance bridge for document {workflow.document.document_number}")
            
            return instance
            
        except Exception as e:
            print(f"❌ Failed to create WorkflowInstance: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _can_review(self, document: Document, user: User) -> bool:
        """Check if user can review document."""
        # Segregation of Duties: Author cannot review their own document
        if document.author == user and not user.is_superuser:
            return False
        
        return (document.reviewer == user or
                user.user_roles.filter(
                    role__module='O1',
                    role__permission_level__in=['review', 'approve', 'admin'],
                    is_active=True
                ).exists() or
                user.is_superuser)
    
    def _can_approve(self, document: Document, user: User) -> bool:
        """Check if user can approve document."""
        # Segregation of Duties: Author cannot approve their own document
        if document.author == user and not user.is_superuser:
            return False
        
        return (document.approver == user or
                user.user_roles.filter(
                    role__module='O1', 
                    role__permission_level__in=['approve', 'admin'],
                    is_active=True
                ).exists() or
                user.is_superuser)
    
    def _determine_return_state(self, document: Document) -> str:
        """Determine state to return to when terminating workflow."""
        # Look for last non-workflow state or default to DRAFT
        if hasattr(document, 'approval_date') and document.approval_date:
            return 'APPROVED'
        elif document.status in ['EFFECTIVE']:
            return 'EFFECTIVE'
        else:
            return 'DRAFT'
    
    def _get_available_actions(self, document: Document, 
                             workflow: DocumentWorkflow = None) -> List[str]:
        """Get available actions for current document/workflow state."""
        if not workflow:
            if document.status == 'DRAFT':
                return ['start_review_workflow', 'start_version_workflow']
            elif document.status == 'EFFECTIVE':
                return ['start_version_workflow', 'start_obsolete_workflow']
            return []
        
        state = workflow.current_state.code
        actions = []
        
        if state == 'DRAFT':
            actions.append('submit_for_review')
        elif state == 'PENDING_REVIEW':
            actions.append('start_review')
        elif state == 'UNDER_REVIEW':
            actions.extend(['complete_review', 'reject_to_draft'])
        elif state == 'REVIEW_COMPLETED':
            actions.append('route_for_approval')
        elif state == 'PENDING_APPROVAL':
            if 'OBSOLETE' in workflow.workflow_type:
                actions.append('approve_obsolescence')
            else:
                actions.extend(['approve_document', 'reject_to_draft'])
        elif state == 'APPROVED':
            actions.append('make_effective')
        
        # Termination is always available for workflows not in terminal states
        if workflow and state not in ['EFFECTIVE', 'SUPERSEDED', 'OBSOLETE', 'TERMINATED']:
            actions.append('terminate_workflow')
        
        return actions
    
    def _copy_dependencies_smart(self, source_document: Document, target_document: Document, user: User):
        """
        Smart dependency copying for upversioning.
        Copies dependencies but automatically resolves to latest EFFECTIVE version of each dependency.
        """
        from apps.documents.models import DocumentDependency
        import re
        
        source_dependencies = DocumentDependency.objects.filter(document=source_document)
        
        for dep in source_dependencies:
            # Get the base document number of the dependency
            depends_on_doc = dep.depends_on
            base_number = re.sub(r'-v\d+\.\d+$', '', depends_on_doc.document_number)
            
            # Find the latest EFFECTIVE version of this document family
            latest_effective = self._find_latest_effective_version(base_number)
            
            if latest_effective:
                # Create dependency pointing to latest effective version
                DocumentDependency.objects.create(
                    document=target_document,
                    depends_on=latest_effective,
                    dependency_type=dep.dependency_type,
                    created_by=user,
                    description=f"Auto-copied from v{source_document.version_major}.{source_document.version_minor} (resolved to latest effective)",
                    is_critical=dep.is_critical
                )
            else:
                # Fallback: copy as-is if no effective version found
                DocumentDependency.objects.create(
                    document=target_document,
                    depends_on=depends_on_doc,
                    dependency_type=dep.dependency_type,
                    created_by=user,
                    description=f"Auto-copied from v{source_document.version_major}.{source_document.version_minor}",
                    is_critical=dep.is_critical
                )
    
    def _find_latest_effective_version(self, base_doc_number: str) -> Document:
        """
        Find the latest EFFECTIVE version of a document family.
        Returns None if no effective version exists.
        """
        # Find all documents with this base number that are EFFECTIVE
        effective_docs = Document.objects.filter(
            document_number__startswith=base_doc_number,
            status='EFFECTIVE'
        ).order_by('-version_major', '-version_minor')
        
        return effective_docs.first() if effective_docs.exists() else None


# Global service instance
_document_lifecycle_service = None

def get_document_lifecycle_service():
    """Get the global document lifecycle service instance."""
    global _document_lifecycle_service
    if _document_lifecycle_service is None:
        _document_lifecycle_service = DocumentLifecycleService()
    return _document_lifecycle_service