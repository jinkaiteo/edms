# Django-River Workflow Configuration

## Overview
This document provides the complete Django-River workflow configuration for the EDMS document lifecycle management, including states, transitions, permissions, and approval processes.

## Installation and Setup

### Requirements
```bash
# Add to requirements.txt
django-river==3.4.0
```

### Settings Configuration
```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # ... other apps
    'river',
    'edms.documents',  # Your document app
]

# River Configuration
RIVER_CONTENT_TYPES = ['documents.Document']
RIVER_INJECT_MODEL_ADMIN = True
```

## Document Model with River Integration

```python
# models.py
from django.db import models
from django.contrib.auth.models import User
from river.models.fields.state import StateField
import uuid

class Document(models.Model):
    # Document States
    DRAFT = 'draft'
    PENDING_REVIEW = 'pending_review'
    REVIEWED = 'reviewed'
    PENDING_APPROVAL = 'pending_approval'
    APPROVED_PENDING_EFFECTIVE = 'approved_pending_effective'
    APPROVED_EFFECTIVE = 'approved_effective'
    SUPERSEDED = 'superseded'
    PENDING_OBSOLETING = 'pending_obsoleting'
    OBSOLETE = 'obsolete'
    
    STATE_CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_REVIEW, 'Pending Review'),
        (REVIEWED, 'Reviewed'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED_PENDING_EFFECTIVE, 'Approved, Pending Effective'),
        (APPROVED_EFFECTIVE, 'Approved and Effective'),
        (SUPERSEDED, 'Superseded'),
        (PENDING_OBSOLETING, 'Pending Obsoleting'),
        (OBSOLETE, 'Obsolete'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    version_major = models.PositiveIntegerField(default=1)
    version_minor = models.PositiveIntegerField(default=0)
    
    # Workflow participants
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name='authored_documents')
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reviewed_documents', null=True, blank=True)
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='approved_documents', null=True, blank=True)
    
    # River state field
    status = StateField(default=DRAFT)
    
    # Additional fields
    approval_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    obsolete_date = models.DateField(null=True, blank=True)
    reason_for_change = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        permissions = [
            ('can_review_document', 'Can review documents'),
            ('can_approve_document', 'Can approve documents'),
            ('can_obsolete_document', 'Can obsolete documents'),
            ('can_terminate_workflow', 'Can terminate workflows'),
        ]
        
    def __str__(self):
        return f"{self.document_number} - {self.title} (v{self.version})"
        
    @property
    def version(self):
        return f"{self.version_major}.{self.version_minor}"
        
    @property
    def can_be_edited(self):
        return self.status in [self.DRAFT]
        
    @property
    def can_be_obsoleted(self):
        return self.status == self.APPROVED_EFFECTIVE and not self.has_dependencies()
        
    def has_dependencies(self):
        return DocumentDependency.objects.filter(depends_on=self).exists()
```

## Workflow States Setup

```python
# management/commands/setup_workflow.py
from django.core.management.base import BaseCommand
from river.models import State
from edms.documents.models import Document

class Command(BaseCommand):
    help = 'Setup workflow states for EDMS'
    
    def handle(self, *args, **options):
        # Create workflow states
        states = [
            ('draft', 'Draft'),
            ('pending_review', 'Pending Review'),
            ('reviewed', 'Reviewed'),
            ('pending_approval', 'Pending Approval'),
            ('approved_pending_effective', 'Approved, Pending Effective'),
            ('approved_effective', 'Approved and Effective'),
            ('superseded', 'Superseded'),
            ('pending_obsoleting', 'Pending Obsoleting'),
            ('obsolete', 'Obsolete'),
        ]
        
        for slug, label in states:
            state, created = State.objects.get_or_create(
                slug=slug,
                defaults={'label': label}
            )
            if created:
                self.stdout.write(f'Created state: {label}')
            else:
                self.stdout.write(f'State already exists: {label}')
```

## Workflow Transitions Configuration

```python
# workflow_config.py
from river.models import State, Transition, TransitionApprovalMeta
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from edms.documents.models import Document

def setup_document_workflow():
    """Setup the complete document workflow with transitions and approvals"""
    
    # Get content type
    content_type = ContentType.objects.get_for_model(Document)
    
    # Get states
    states = {
        state.slug: state 
        for state in State.objects.all()
    }
    
    # Get groups
    authors_group = Group.objects.get_or_create(name='Document Authors')[0]
    reviewers_group = Group.objects.get_or_create(name='Document Reviewers')[0]
    approvers_group = Group.objects.get_or_create(name='Document Approvers')[0]
    admins_group = Group.objects.get_or_create(name='Document Administrators')[0]
    
    # Define transitions
    transitions = [
        # Review Workflow
        {
            'from': states['draft'],
            'to': states['pending_review'],
            'label': 'Submit for Review',
            'groups': [authors_group],
            'permissions': [],
        },
        {
            'from': states['pending_review'],
            'to': states['reviewed'],
            'label': 'Approve Review',
            'groups': [reviewers_group],
            'permissions': ['can_review_document'],
        },
        {
            'from': states['pending_review'],
            'to': states['draft'],
            'label': 'Reject Review',
            'groups': [reviewers_group],
            'permissions': ['can_review_document'],
        },
        {
            'from': states['reviewed'],
            'to': states['pending_approval'],
            'label': 'Submit for Approval',
            'groups': [authors_group],
            'permissions': [],
        },
        {
            'from': states['pending_approval'],
            'to': states['approved_pending_effective'],
            'label': 'Approve Document',
            'groups': [approvers_group],
            'permissions': ['can_approve_document'],
        },
        {
            'from': states['pending_approval'],
            'to': states['draft'],
            'label': 'Reject Approval',
            'groups': [approvers_group],
            'permissions': ['can_approve_document'],
        },
        {
            'from': states['approved_pending_effective'],
            'to': states['approved_effective'],
            'label': 'Make Effective',
            'groups': [admins_group],  # Automated by scheduler
            'permissions': [],
        },
        
        # Up-versioning Workflow
        {
            'from': states['approved_effective'],
            'to': states['superseded'],
            'label': 'Supersede with New Version',
            'groups': [admins_group],  # Automated
            'permissions': [],
        },
        
        # Obsolete Workflow
        {
            'from': states['approved_effective'],
            'to': states['pending_obsoleting'],
            'label': 'Start Obsolete Process',
            'groups': [authors_group, approvers_group],
            'permissions': ['can_obsolete_document'],
        },
        {
            'from': states['pending_obsoleting'],
            'to': states['obsolete'],
            'label': 'Complete Obsolete',
            'groups': [approvers_group],
            'permissions': ['can_obsolete_document'],
        },
        {
            'from': states['pending_obsoleting'],
            'to': states['approved_effective'],
            'label': 'Cancel Obsolete',
            'groups': [approvers_group],
            'permissions': ['can_obsolete_document'],
        },
        
        # Workflow Termination (from any state back to draft)
        {
            'from': states['pending_review'],
            'to': states['draft'],
            'label': 'Terminate Workflow',
            'groups': [authors_group, admins_group],
            'permissions': ['can_terminate_workflow'],
        },
        {
            'from': states['reviewed'],
            'to': states['draft'],
            'label': 'Terminate Workflow',
            'groups': [authors_group, admins_group],
            'permissions': ['can_terminate_workflow'],
        },
        {
            'from': states['pending_approval'],
            'to': states['draft'],
            'label': 'Terminate Workflow',
            'groups': [authors_group, admins_group],
            'permissions': ['can_terminate_workflow'],
        },
    ]
    
    # Create transitions
    for transition_data in transitions:
        transition = Transition.objects.create(
            content_type=content_type,
            source_state=transition_data['from'],
            destination_state=transition_data['to'],
        )
        
        # Create approval meta
        approval_meta = TransitionApprovalMeta.objects.create(
            transition=transition,
            priority=0,
        )
        
        # Assign groups and permissions
        for group in transition_data['groups']:
            approval_meta.groups.add(group)
            
        for permission_codename in transition_data['permissions']:
            try:
                permission = Permission.objects.get(
                    content_type=content_type,
                    codename=permission_codename
                )
                approval_meta.permissions.add(permission)
            except Permission.DoesNotExist:
                print(f"Permission {permission_codename} not found")
```

## Workflow Methods and Signals

```python
# workflow_methods.py
from django.db import transaction
from django.contrib.auth.models import User
from river.services.proceeding import ProceedingService
from .models import Document, DocumentWorkflowHistory

class DocumentWorkflowService:
    
    @staticmethod
    def submit_for_review(document: Document, reviewer: User, comments: str = ""):
        """Submit document for review"""
        with transaction.atomic():
            document.reviewer = reviewer
            document.save()
            
            # Proceed with workflow
            proceeding_service = ProceedingService()
            proceeding_service.proceed(
                document,
                as_user=document.author,
                next_state=Document.PENDING_REVIEW
            )
            
            # Log workflow action
            DocumentWorkflowHistory.objects.create(
                document=document,
                from_state='draft',
                to_state=Document.PENDING_REVIEW,
                actor=document.author,
                comments=comments
            )
    
    @staticmethod
    def review_document(document: Document, reviewer: User, approved: bool, comments: str = "", approver: User = None):
        """Review document - approve or reject"""
        with transaction.atomic():
            if approved:
                if approver:
                    document.approver = approver
                    document.save()
                    next_state = Document.REVIEWED
                else:
                    raise ValueError("Approver required when approving review")
            else:
                next_state = Document.DRAFT
            
            proceeding_service = ProceedingService()
            proceeding_service.proceed(
                document,
                as_user=reviewer,
                next_state=next_state
            )
            
            DocumentWorkflowHistory.objects.create(
                document=document,
                from_state=Document.PENDING_REVIEW,
                to_state=next_state,
                actor=reviewer,
                comments=comments,
                approved=approved
            )
    
    @staticmethod
    def submit_for_approval(document: Document, comments: str = ""):
        """Submit reviewed document for approval"""
        with transaction.atomic():
            proceeding_service = ProceedingService()
            proceeding_service.proceed(
                document,
                as_user=document.author,
                next_state=Document.PENDING_APPROVAL
            )
            
            DocumentWorkflowHistory.objects.create(
                document=document,
                from_state=Document.REVIEWED,
                to_state=Document.PENDING_APPROVAL,
                actor=document.author,
                comments=comments
            )
    
    @staticmethod
    def approve_document(document: Document, approver: User, approved: bool, 
                        effective_date=None, comments: str = ""):
        """Final approval of document"""
        from datetime import date
        
        with transaction.atomic():
            if approved:
                document.approval_date = date.today()
                document.effective_date = effective_date or date.today()
                document.save()
                next_state = Document.APPROVED_PENDING_EFFECTIVE
            else:
                next_state = Document.DRAFT
            
            proceeding_service = ProceedingService()
            proceeding_service.proceed(
                document,
                as_user=approver,
                next_state=next_state
            )
            
            DocumentWorkflowHistory.objects.create(
                document=document,
                from_state=Document.PENDING_APPROVAL,
                to_state=next_state,
                actor=approver,
                comments=comments,
                approved=approved
            )
    
    @staticmethod
    def make_effective(document: Document):
        """Make approved document effective (usually automated)"""
        with transaction.atomic():
            proceeding_service = ProceedingService()
            proceeding_service.proceed(
                document,
                as_user=None,  # System action
                next_state=Document.APPROVED_EFFECTIVE
            )
            
            DocumentWorkflowHistory.objects.create(
                document=document,
                from_state=Document.APPROVED_PENDING_EFFECTIVE,
                to_state=Document.APPROVED_EFFECTIVE,
                actor=None,  # System
                comments="Automatically made effective by scheduler"
            )
    
    @staticmethod
    def start_obsolete_workflow(document: Document, user: User, reason: str, obsolete_date=None):
        """Start obsolete workflow"""
        from datetime import date
        
        if document.has_dependencies():
            raise ValueError("Cannot obsolete document with dependencies")
        
        with transaction.atomic():
            document.obsolete_date = obsolete_date or date.today()
            document.reason_for_change = reason
            document.save()
            
            proceeding_service = ProceedingService()
            proceeding_service.proceed(
                document,
                as_user=user,
                next_state=Document.PENDING_OBSOLETING
            )
            
            DocumentWorkflowHistory.objects.create(
                document=document,
                from_state=Document.APPROVED_EFFECTIVE,
                to_state=Document.PENDING_OBSOLETING,
                actor=user,
                comments=f"Started obsolete workflow: {reason}"
            )
    
    @staticmethod
    def terminate_workflow(document: Document, user: User, reason: str):
        """Terminate any ongoing workflow"""
        current_state = document.status
        
        with transaction.atomic():
            proceeding_service = ProceedingService()
            proceeding_service.proceed(
                document,
                as_user=user,
                next_state=Document.DRAFT
            )
            
            DocumentWorkflowHistory.objects.create(
                document=document,
                from_state=current_state,
                to_state=Document.DRAFT,
                actor=user,
                comments=f"Workflow terminated: {reason}"
            )

# Workflow History Model
class DocumentWorkflowHistory(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='workflow_history')
    from_state = models.CharField(max_length=50)
    to_state = models.CharField(max_length=50)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comments = models.TextField(blank=True)
    approved = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

## Workflow Signals and Hooks

```python
# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from river.signals import workflow_complete, pre_transition, post_transition
from .models import Document
from .services import NotificationService, AuditService

@receiver(pre_transition)
def validate_workflow_transition(sender, workflow_object, field, source_state, 
                                destination_state, approving_user, **kwargs):
    """Validate workflow transition before it happens"""
    if isinstance(workflow_object, Document):
        # Business rule validations
        if destination_state.slug == 'pending_approval':
            if not workflow_object.reviewer:
                raise ValueError("Document must have a reviewer before approval")
        
        if destination_state.slug == 'approved_pending_effective':
            if not workflow_object.effective_date:
                raise ValueError("Effective date required for approval")

@receiver(post_transition)
def handle_workflow_transition(sender, workflow_object, field, source_state, 
                              destination_state, approving_user, **kwargs):
    """Handle post-transition actions"""
    if isinstance(workflow_object, Document):
        # Send notifications
        NotificationService.send_workflow_notification(
            workflow_object, source_state, destination_state, approving_user
        )
        
        # Log to audit trail
        AuditService.log_workflow_change(
            workflow_object, source_state, destination_state, approving_user
        )
        
        # Handle specific transitions
        if destination_state.slug == 'approved_effective':
            # Update dependent documents
            handle_document_effective(workflow_object)
        
        elif destination_state.slug == 'obsolete':
            # Clean up references
            handle_document_obsolete(workflow_object)

@receiver(workflow_complete)
def handle_workflow_complete(sender, workflow_object, field, **kwargs):
    """Handle workflow completion"""
    if isinstance(workflow_object, Document):
        # Final validations and cleanup
        pass

def handle_document_effective(document):
    """Actions when document becomes effective"""
    # Supersede previous version if this is an up-version
    if document.version_major > 1 or document.version_minor > 0:
        previous_versions = Document.objects.filter(
            document_number__startswith=document.document_number.split('-v')[0],
            status=Document.APPROVED_EFFECTIVE
        ).exclude(id=document.id)
        
        for prev_doc in previous_versions:
            if prev_doc.version != document.version:
                prev_doc.status = Document.SUPERSEDED
                prev_doc.save()

def handle_document_obsolete(document):
    """Actions when document becomes obsolete"""
    # Remove from active indexes
    # Update search indexes
    pass
```

## Scheduled Tasks for Workflow

```python
# tasks.py (Celery tasks)
from celery import shared_task
from datetime import date
from .models import Document
from .workflow_methods import DocumentWorkflowService

@shared_task
def make_documents_effective():
    """Make approved documents effective based on their effective date"""
    documents_to_activate = Document.objects.filter(
        status=Document.APPROVED_PENDING_EFFECTIVE,
        effective_date__lte=date.today()
    )
    
    for document in documents_to_activate:
        try:
            DocumentWorkflowService.make_effective(document)
            print(f"Made document {document.document_number} effective")
        except Exception as e:
            print(f"Error making document {document.document_number} effective: {e}")

@shared_task
def process_obsolete_documents():
    """Process documents that should become obsolete"""
    documents_to_obsolete = Document.objects.filter(
        status=Document.PENDING_OBSOLETING,
        obsolete_date__lte=date.today()
    )
    
    for document in documents_to_obsolete:
        if not document.has_dependencies():
            try:
                proceeding_service = ProceedingService()
                proceeding_service.proceed(
                    document,
                    as_user=None,  # System
                    next_state=Document.OBSOLETE
                )
                print(f"Obsoleted document {document.document_number}")
            except Exception as e:
                print(f"Error obsoleting document {document.document_number}: {e}")

@shared_task
def check_workflow_timeouts():
    """Check for workflow items that have been pending too long"""
    from datetime import timedelta
    
    timeout_threshold = date.today() - timedelta(days=30)
    
    # Find documents stuck in review
    stuck_reviews = Document.objects.filter(
        status=Document.PENDING_REVIEW,
        updated_at__date__lt=timeout_threshold
    )
    
    # Send notifications to administrators
    for document in stuck_reviews:
        NotificationService.send_timeout_notification(document)
```

This Django-River workflow configuration provides:

1. **Complete state machine** for document lifecycle
2. **Flexible transition rules** with proper permissions
3. **Automated workflow progression** through scheduled tasks
4. **Comprehensive validation** and business rule enforcement
5. **Audit trail integration** for compliance
6. **Notification system** for workflow participants
7. **Error handling** and rollback capabilities

The system supports all three main workflows (Review, Up-versioning, Obsolete) while maintaining 21 CFR Part 11 compliance through proper authorization, audit trails, and electronic signatures.