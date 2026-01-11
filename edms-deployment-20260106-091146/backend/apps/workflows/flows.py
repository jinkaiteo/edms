"""
Viewflow workflow definitions for EDMS document management.
Implements document lifecycle flows with compliance and audit support.
"""

from viewflow import flow
from viewflow.base import this, Flow
from viewflow.contrib import celery
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import UpdateView
from django.contrib.auth import get_user_model

from .viewflow_models import DocumentProcess
from .views import (
    DocumentCreateView, DocumentReviewView, DocumentApprovalView,
    DocumentEffectiveView, DocumentRevisionView
)

User = get_user_model()


class DocumentReviewFlow(Flow):
    """
    Document Review and Approval Flow for EDMS.
    
    Flow: Create → Review → Approve → Effective
    Includes revision loops and compliance tracking.
    """
    
    class Meta:
        process_class = DocumentProcess
        task_class = 'viewflow.models.Task'
        
    # Start: Document Creation
    start = flow.Start(DocumentCreateView) \
        .Permission('documents.add_document') \
        .Next(this.assign_reviewer)
    
    # Automatic reviewer assignment
    assign_reviewer = flow.Function(this.assign_document_reviewer) \
        .Next(this.review)
    
    # Document Review Task
    review = flow.View(DocumentReviewView) \
        .Assign(lambda process: process.assigned_reviewer) \
        .Permission('documents.can_review') \
        .Next(this.check_review_decision)
    
    # Review Decision Gateway
    check_review_decision = flow.If(this.is_review_approved) \
        .Then(this.approve) \
        .Else(this.check_needs_revision)
    
    # Check if revision is needed or rejected
    check_needs_revision = flow.If(this.needs_revision) \
        .Then(this.revise) \
        .Else(this.reject)
    
    # Document Approval Task
    approve = flow.View(DocumentApprovalView) \
        .Assign(lambda process: process.assigned_approver) \
        .Permission('documents.can_approve') \
        .Next(this.check_approval_decision)
    
    # Approval Decision Gateway
    check_approval_decision = flow.If(this.is_approval_approved) \
        .Then(this.make_effective) \
        .Else(this.check_approval_revision)
    
    # Check if approval needs revision
    check_approval_revision = flow.If(this.needs_revision) \
        .Then(this.revise) \
        .Else(this.reject)
    
    # Make Document Effective
    make_effective = flow.View(DocumentEffectiveView) \
        .Permission('documents.can_make_effective') \
        .Next(this.end)
    
    # Document Revision
    revise = flow.View(DocumentRevisionView) \
        .Assign(this.start.owner) \
        .Next(this.review)
    
    # Document Rejection (Terminal)
    reject = flow.Function(this.mark_document_rejected) \
        .Next(this.end)
    
    # End of Flow
    end = flow.End()
    
    def assign_document_reviewer(self, activation):
        """Auto-assign reviewer based on document type and department."""
        process = activation.process
        document = process.document
        
        # Logic to assign reviewer based on document type
        if hasattr(document, 'document_type'):
            if document.document_type.code == 'SOP':
                # Assign to SOP reviewer
                process.assigned_reviewer = User.objects.filter(
                    groups__name='SOP_Reviewers'
                ).first()
            elif document.document_type.code in ['POLICY', 'MANUAL']:
                # Assign to policy reviewer
                process.assigned_reviewer = User.objects.filter(
                    groups__name='Policy_Reviewers'
                ).first()
            else:
                # Default reviewer
                process.assigned_reviewer = User.objects.filter(
                    groups__name='Document_Reviewers'
                ).first()
        
        # Assign approver based on document criticality
        if hasattr(document, 'criticality'):
            if document.criticality == 'HIGH':
                process.assigned_approver = User.objects.filter(
                    groups__name='Senior_Approvers'
                ).first()
            else:
                process.assigned_approver = User.objects.filter(
                    groups__name='Document_Approvers'
                ).first()
        
        process.save()
    
    def is_review_approved(self, activation):
        """Check if document review was approved."""
        return activation.process.review_decision == 'APPROVED'
    
    def is_approval_approved(self, activation):
        """Check if document approval was approved."""
        return activation.process.approval_decision == 'APPROVED'
    
    def needs_revision(self, activation):
        """Check if document needs revision (vs outright rejection)."""
        process = activation.process
        return process.review_decision == 'NEEDS_REVISION' or \
               process.approval_decision == 'NEEDS_REVISION'
    
    def mark_document_rejected(self, activation):
        """Mark document as rejected and update status."""
        process = activation.process
        process.document.status = 'REJECTED'
        process.document.save()
        process.final_decision = 'REJECTED'
        process.save()


class DocumentUpVersionFlow(Flow):
    """
    Document Up-versioning Flow for EDMS.
    
    Creates new versions of existing effective documents.
    """
    
    class Meta:
        process_class = DocumentProcess
        task_class = 'viewflow.models.Task'
    
    start = flow.Start(DocumentCreateView) \
        .Permission('documents.add_document') \
        .Next(this.validate_parent_document)
    
    validate_parent_document = flow.Function(this.validate_parent_effective) \
        .Next(this.review)
    
    review = flow.View(DocumentReviewView) \
        .Assign(lambda process: process.assigned_reviewer) \
        .Permission('documents.can_review') \
        .Next(this.check_review_decision)
    
    check_review_decision = flow.If(this.is_review_approved) \
        .Then(this.approve) \
        .Else(this.revise)
    
    approve = flow.View(DocumentApprovalView) \
        .Assign(lambda process: process.assigned_approver) \
        .Permission('documents.can_approve') \
        .Next(this.check_approval_decision)
    
    check_approval_decision = flow.If(this.is_approval_approved) \
        .Then(this.supersede_parent) \
        .Else(this.revise)
    
    supersede_parent = flow.Function(this.supersede_parent_document) \
        .Next(this.make_effective)
    
    make_effective = flow.View(DocumentEffectiveView) \
        .Permission('documents.can_make_effective') \
        .Next(this.end)
    
    revise = flow.View(DocumentRevisionView) \
        .Assign(this.start.owner) \
        .Next(this.review)
    
    end = flow.End()
    
    def validate_parent_effective(self, activation):
        """Validate that parent document is in effective state."""
        process = activation.process
        parent_doc = process.document.parent_document
        
        if not parent_doc or parent_doc.status != 'EFFECTIVE':
            raise ValueError("Parent document must be in EFFECTIVE status for up-versioning")
        
        # Auto-assign same reviewers as parent document
        if hasattr(parent_doc, 'last_workflow'):
            process.assigned_reviewer = parent_doc.last_workflow.assigned_reviewer
            process.assigned_approver = parent_doc.last_workflow.assigned_approver
        
        process.save()
    
    def supersede_parent_document(self, activation):
        """Mark parent document as superseded."""
        process = activation.process
        parent_doc = process.document.parent_document
        
        if parent_doc:
            parent_doc.status = 'SUPERSEDED'
            parent_doc.superseded_by = process.document
            parent_doc.superseded_at = timezone.now()
            parent_doc.save()
    
    def is_review_approved(self, activation):
        """Check if document review was approved."""
        return activation.process.review_decision == 'APPROVED'
    
    def is_approval_approved(self, activation):
        """Check if document approval was approved."""
        return activation.process.approval_decision == 'APPROVED'


class DocumentObsoleteFlow(Flow):
    """
    Document Obsolescence Flow for EDMS.
    
    Marks documents as obsolete when no longer needed.
    """
    
    class Meta:
        process_class = DocumentProcess
        task_class = 'viewflow.models.Task'
    
    start = flow.Start(DocumentCreateView) \
        .Permission('documents.can_obsolete') \
        .Next(this.validate_obsolescence)
    
    validate_obsolescence = flow.Function(this.validate_obsolescence_request) \
        .Next(this.review_obsolescence)
    
    review_obsolescence = flow.View(DocumentReviewView) \
        .Assign(lambda process: process.assigned_reviewer) \
        .Permission('documents.can_review') \
        .Next(this.check_review_decision)
    
    check_review_decision = flow.If(this.is_review_approved) \
        .Then(this.approve_obsolescence) \
        .Else(this.reject_obsolescence)
    
    approve_obsolescence = flow.View(DocumentApprovalView) \
        .Assign(lambda process: process.assigned_approver) \
        .Permission('documents.can_approve') \
        .Next(this.check_approval_decision)
    
    check_approval_decision = flow.If(this.is_approval_approved) \
        .Then(this.make_obsolete) \
        .Else(this.reject_obsolescence)
    
    make_obsolete = flow.Function(this.mark_document_obsolete) \
        .Next(this.end)
    
    reject_obsolescence = flow.Function(this.reject_obsolescence_request) \
        .Next(this.end)
    
    end = flow.End()
    
    def validate_obsolescence_request(self, activation):
        """Validate that document can be made obsolete."""
        process = activation.process
        document = process.target_document  # Document to be made obsolete
        
        if document.status not in ['EFFECTIVE', 'SUPERSEDED']:
            raise ValueError("Only EFFECTIVE or SUPERSEDED documents can be made obsolete")
        
        # Check for dependencies
        dependent_docs = document.referenced_by.filter(status='EFFECTIVE')
        if dependent_docs.exists():
            process.obsolescence_notes = f"Warning: {dependent_docs.count()} active documents reference this document"
        
        process.save()
    
    def mark_document_obsolete(self, activation):
        """Mark target document as obsolete."""
        process = activation.process
        document = process.target_document
        
        document.status = 'OBSOLETE'
        document.obsoleted_at = timezone.now()
        document.obsoleted_by = activation.task.owner
        document.save()
        
        process.final_decision = 'OBSOLETED'
        process.save()
    
    def reject_obsolescence_request(self, activation):
        """Reject obsolescence request."""
        process = activation.process
        process.final_decision = 'REJECTED'
        process.save()
    
    def is_review_approved(self, activation):
        """Check if obsolescence review was approved."""
        return activation.process.review_decision == 'APPROVED'
    
    def is_approval_approved(self, activation):
        """Check if obsolescence approval was approved."""
        return activation.process.approval_decision == 'APPROVED'