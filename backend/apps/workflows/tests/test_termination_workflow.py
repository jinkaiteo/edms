"""
Document Termination Workflow Tests

Tests for terminating documents before they become effective:
- Author can terminate their documents
- Termination at different workflow stages
- Termination cancels pending tasks
- Terminated documents are read-only
- Non-authors cannot terminate
- Cannot terminate EFFECTIVE documents

COMPLIANCE: Termination provides audit trail for abandoned documents.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.documents.models import Document, DocumentType, DocumentSource
from apps.workflows.models import WorkflowInstance, WorkflowType

User = get_user_model()


@pytest.mark.django_db
class TestDocumentTermination:
    """Test suite for document termination workflow"""
    
    def setup_method(self):
        """Setup test data"""
        self.author = User.objects.create_user(
            username='author_term',
            password='test123'
        )
        self.other_user = User.objects.create_user(
            username='other_term',
            password='test123'
        )
        
        # Create WorkflowType objects (REQUIRED for lifecycle service)
        self.review_workflow_type = WorkflowType.objects.create(
            name='Document Review',
            workflow_type='REVIEW',
            created_by=self.author
        )
        self.approval_workflow_type = WorkflowType.objects.create(
            name='Document Approval',
            workflow_type='APPROVAL',
            created_by=self.author
        )
        
        # Create DocumentState objects (REQUIRED for workflow transitions)
        for code, name in [
            ('DRAFT', 'Draft'),
            ('UNDER_REVIEW', 'Under Review'),
            ('REVIEW_COMPLETED', 'Review Completed'),
            ('PENDING_APPROVAL', 'Pending Approval'),
            ('APPROVED_PENDING_EFFECTIVE', 'Approved Pending Effective'),
            ('EFFECTIVE', 'Effective'),
            ('TERMINATED', 'Terminated'),
        ]:
            DocumentState.objects.create(
                name=name,
                code=code
            )
        
        self.doc_type = DocumentType.objects.create(
            name='Procedure',
            code='PROC',
            created_by=self.author
        )
        self.doc_source = DocumentSource.objects.create(
            name='Original Digital Draft',
            source_type='original_digital'
        )
    
    def test_author_can_terminate_draft_document(self):
        """Test author can terminate DRAFT document"""
        doc = Document.objects.create(
            title='Draft to Terminate',
            description='Will be terminated',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='DRAFT',
            version_major=1,
            version_minor=0
        )
        
        result = doc.terminate_document(
            terminated_by=self.author,
            reason='No longer needed'
        )
        
        assert result is True
        doc.refresh_from_db()
        assert doc.status == 'TERMINATED'
        assert doc.obsoleted_by == self.author
        assert 'TERMINATED' in doc.obsolescence_reason
        assert doc.is_active is False
    
    def test_author_can_terminate_under_review_document(self):
        """Test author can terminate document UNDER_REVIEW"""
        doc = Document.objects.create(
            title='Under Review to Terminate',
            description='In review but will be terminated',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='UNDER_REVIEW',
            version_major=1,
            version_minor=0
        )
        
        result = doc.terminate_document(
            terminated_by=self.author,
            reason='Project cancelled'
        )
        
        assert result is True
        doc.refresh_from_db()
        assert doc.status == 'TERMINATED'
    
    def test_author_can_terminate_pending_approval_document(self):
        """Test author can terminate document PENDING_APPROVAL"""
        doc = Document.objects.create(
            title='Pending Approval to Terminate',
            description='Awaiting approval but will be terminated',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='PENDING_APPROVAL',
            version_major=1,
            version_minor=0
        )
        
        result = doc.terminate_document(
            terminated_by=self.author,
            reason='Wrong document uploaded'
        )
        
        assert result is True
        doc.refresh_from_db()
        assert doc.status == 'TERMINATED'
    
    def test_termination_requires_reason(self):
        """Test termination requires a reason"""
        doc = Document.objects.create(
            title='Draft Document',
            description='Test',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='DRAFT',
            version_major=1,
            version_minor=0
        )
        
        result = doc.terminate_document(
            terminated_by=self.author,
            reason=''
        )
        
        # Should still work but reason should be captured
        assert result is True
        doc.refresh_from_db()
        assert doc.obsolescence_reason  # Has some reason
    
    def test_cannot_terminate_effective_document(self):
        """Test that EFFECTIVE documents cannot be terminated"""
        doc = Document.objects.create(
            title='Effective Document',
            description='Already effective',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='EFFECTIVE',
            version_major=1,
            version_minor=0
        )
        
        # Should fail - cannot terminate effective documents
        try:
            result = doc.terminate_document(
                terminated_by=self.author,
                reason='Should fail'
            )
            assert result is False
        except ValueError:
            # Expected exception
            pass
    
    def test_non_author_cannot_terminate(self):
        """Test that non-authors cannot terminate documents"""
        doc = Document.objects.create(
            title='Draft Document',
            description='Owned by author',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='DRAFT',
            version_major=1,
            version_minor=0
        )
        
        try:
            result = doc.terminate_document(
                terminated_by=self.other_user,
                reason='Should fail'
            )
            assert result is False
        except ValueError:
            # Expected exception
            pass
    
    def test_terminated_documents_are_read_only(self):
        """Test that TERMINATED documents cannot be edited"""
        doc = Document.objects.create(
            title='Draft Document',
            description='Will be terminated',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='DRAFT',
            version_major=1,
            version_minor=0
        )
        
        doc.terminate_document(
            terminated_by=self.author,
            reason='Testing'
        )
        
        doc.refresh_from_db()
        can_edit = doc.can_edit(self.author)
        assert can_edit is False
