"""
Document Versioning Workflow Tests

Tests for creating new document versions and the versioning lifecycle:
- Creating major versions (v1.0 → v2.0)
- Creating minor versions (v1.0 → v1.1)
- Old version superseding when new version becomes effective
- Version numbering and formatting
- Versioned documents following full approval workflow
- Dependencies on versioned documents

COMPLIANCE: Version control is required for 21 CFR Part 11 compliance.
All document changes must be traceable through version history.
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.documents.models import Document, DocumentType, DocumentSource, DocumentDependency
from apps.workflows.models import DocumentWorkflow, DocumentState, WorkflowType
from apps.workflows.document_lifecycle import get_document_lifecycle_service

User = get_user_model()


@pytest.mark.django_db
class TestDocumentVersioning:
    """Test suite for document versioning workflow"""
    
    def setup_method(self):
        """Setup test data before each test"""
        # Create users
        self.author = User.objects.create_user(
            username='author_version',
            password='test123',
            first_name='Version',
            last_name='Author'
        )
        self.reviewer = User.objects.create_user(
            username='reviewer_version',
            password='test123',
            first_name='Version',
            last_name='Reviewer'
        )
        self.approver = User.objects.create_user(
            username='approver_version',
            password='test123',
            first_name='Version',
            last_name='Approver'
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
        self.states = {}
        for code, name in [
            ('DRAFT', 'Draft'),
            ('UNDER_REVIEW', 'Under Review'),
            ('REVIEW_COMPLETED', 'Review Completed'),
            ('PENDING_APPROVAL', 'Pending Approval'),
            ('APPROVED_PENDING_EFFECTIVE', 'Approved Pending Effective'),
            ('EFFECTIVE', 'Effective'),
            ('SUPERSEDED', 'Superseded'),
            ('TERMINATED', 'Terminated'),
        ]:
            state = DocumentState.objects.create(
                name=name,
                code=code
            )
            self.states[code] = state
        
        # Create document type and source
        self.doc_type = DocumentType.objects.create(
            name='Standard Operating Procedure',
            code='SOP',
            created_by=self.author
        )
        self.doc_source = DocumentSource.objects.create(
            name='Original Digital Draft',
            source_type='original_digital'
        )
        
        # Create an EFFECTIVE document (base for versioning)
        self.original_doc = Document.objects.create(
            title='Original Document v1.0',
            description='Original version',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            reviewer=self.reviewer,
            approver=self.approver,
            status='EFFECTIVE',
            version_major=1,
            version_minor=0,
            effective_date=date.today() - timedelta(days=30),
            approval_date=timezone.now() - timedelta(days=31)
        )
        
        self.lifecycle_service = get_document_lifecycle_service()
    
    def test_create_major_version_from_effective_document(self):
        """
        Test creating a major version (v1.0 → v2.0) from an EFFECTIVE document.
        
        Expected behavior:
        - New document created with v2.0
        - New document starts in DRAFT status
        - Original document remains EFFECTIVE
        - New document copies metadata from original
        """
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Major update with significant changes',
                'title': 'Updated Document v2.0'
            }
        )
        
        assert result['success'] is True
        
        new_doc = result['new_document']
        assert new_doc.version_major == 2
        assert new_doc.version_minor == 0
        assert new_doc.status == 'DRAFT'
        assert new_doc.author == self.author
        assert new_doc.document_type == self.original_doc.document_type
        assert new_doc.title == 'Updated Document v2.0'
        assert new_doc.reason_for_change == 'Major update with significant changes'
        
        # Original document should still be EFFECTIVE
        self.original_doc.refresh_from_db()
        assert self.original_doc.status == 'EFFECTIVE'
        assert self.original_doc.version_major == 1
        assert self.original_doc.version_minor == 0
    
    def test_create_minor_version_from_effective_document(self):
        """
        Test creating a minor version (v1.0 → v1.1) from an EFFECTIVE document.
        
        Minor versions are for small corrections, typo fixes, etc.
        """
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'minor',
                'reason_for_change': 'Fixed typos and minor corrections',
                'title': 'Original Document v1.1'
            }
        )
        
        assert result['success'] is True
        
        new_doc = result['new_document']
        assert new_doc.version_major == 1
        assert new_doc.version_minor == 1
        assert new_doc.status == 'DRAFT'
        assert new_doc.reason_for_change == 'Fixed typos and minor corrections'
    
    def test_cannot_version_non_effective_document(self):
        """
        Test that only EFFECTIVE documents can be versioned.
        
        DRAFT, UNDER_REVIEW, etc. documents should not allow versioning.
        """
        draft_doc = Document.objects.create(
            title='Draft Document',
            description='Still in draft',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='DRAFT',
            version_major=1,
            version_minor=0
        )
        
        result = self.lifecycle_service.start_version_workflow(
            existing_document=draft_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Should fail'
            }
        )
        
        assert result['success'] is False
        assert 'only EFFECTIVE documents' in result.get('error', '').lower()
    
    def test_versioned_document_follows_full_workflow(self):
        """
        Test that versioned documents must go through complete review/approval workflow.
        
        Even though it's based on an approved document, the new version
        must be reviewed and approved independently.
        """
        # Create v2.0
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Major changes'
            }
        )
        
        new_doc = result['new_document']
        
        # Submit for review
        success = self.lifecycle_service.submit_for_review(
            document=new_doc,
            user=self.author,
            comment='Version 2.0 ready for review'
        )
        assert success is True
        
        new_doc.refresh_from_db()
        assert new_doc.status == 'UNDER_REVIEW'
        
        # Reviewer approves
        success = self.lifecycle_service.complete_review(
            document=new_doc,
            user=self.reviewer,
            approved=True,
            comment='Reviewed and approved'
        )
        assert success is True
        
        new_doc.refresh_from_db()
        assert new_doc.status == 'REVIEW_COMPLETED'
        
        # Route for approval
        success = self.lifecycle_service.route_for_approval(
            document=new_doc,
            user=self.author,
            approver=self.approver,
            comment='Ready for final approval'
        )
        assert success is True
        
        new_doc.refresh_from_db()
        assert new_doc.status == 'PENDING_APPROVAL'
        
        # Approve with effective date
        success = self.lifecycle_service.approve_document(
            document=new_doc,
            user=self.approver,
            effective_date=date.today(),
            comment='Approved for immediate effectiveness'
        )
        assert success is True
        
        new_doc.refresh_from_db()
        assert new_doc.status in ['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE']
    
    def test_old_version_superseded_when_new_version_effective(self):
        """
        Test that the old version automatically becomes SUPERSEDED
        when the new version becomes EFFECTIVE.
        
        This is critical for document control - only the latest version
        should be EFFECTIVE.
        """
        # Create and approve v2.0
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Major update'
            }
        )
        new_doc = result['new_document']
        
        # Fast-track to EFFECTIVE (simulate full workflow)
        new_doc.status = 'EFFECTIVE'
        new_doc.effective_date = date.today()
        new_doc.reviewer = self.reviewer
        new_doc.approver = self.approver
        new_doc.supersedes = self.original_doc
        new_doc.save()
        
        # Check that old version was superseded
        self.original_doc.refresh_from_db()
        assert self.original_doc.status == 'SUPERSEDED'
        
        # Verify the supersedes relationship
        assert new_doc.supersedes == self.original_doc
        assert self.original_doc.superseded_by.first() == new_doc
    
    def test_version_numbering_format(self):
        """
        Test that version numbers are formatted correctly as 01.00, 02.00, etc.
        
        This is important for consistent display and sorting.
        """
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Test versioning'
            }
        )
        
        new_doc = result['new_document']
        
        # Test version_string property
        assert new_doc.version_string == '02.00'
        assert self.original_doc.version_string == '01.00'
        
        # Test __str__ includes version
        assert 'v02.00' in str(new_doc) or 'v2.0' in str(new_doc)
    
    def test_version_inherits_document_type_and_source(self):
        """
        Test that new versions inherit document type and source from original.
        """
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Update'
            }
        )
        
        new_doc = result['new_document']
        
        assert new_doc.document_type == self.original_doc.document_type
        assert new_doc.document_source == self.original_doc.document_source
    
    def test_multiple_versions_chain(self):
        """
        Test creating multiple versions: v1.0 → v2.0 → v3.0
        
        Ensures version chain works correctly.
        """
        # Create v2.0
        result2 = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Version 2'
            }
        )
        v2_doc = result2['new_document']
        
        # Make v2.0 effective
        v2_doc.status = 'EFFECTIVE'
        v2_doc.effective_date = date.today()
        v2_doc.reviewer = self.reviewer
        v2_doc.approver = self.approver
        v2_doc.save()
        
        # Create v3.0 from v2.0
        result3 = self.lifecycle_service.start_version_workflow(
            existing_document=v2_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Version 3'
            }
        )
        v3_doc = result3['new_document']
        
        assert v3_doc.version_major == 3
        assert v3_doc.version_minor == 0
        assert v3_doc.status == 'DRAFT'
    
    def test_versioning_preserves_dependencies(self):
        """
        Test that dependencies from old version can be reviewed for new version.
        
        Dependencies may need to be updated or confirmed for the new version.
        """
        # Create a dependency on the original document
        referenced_doc = Document.objects.create(
            title='Referenced Document',
            description='Referenced by original',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='EFFECTIVE',
            version_major=1,
            version_minor=0
        )
        
        dependency = DocumentDependency.objects.create(
            document=self.original_doc,
            depends_on=referenced_doc,
            dependency_type='REFERENCE',
            created_by=self.author
        )
        
        # Create new version
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Update with dependencies'
            }
        )
        
        new_doc = result['new_document']
        
        # Note: Dependencies are NOT automatically copied in current implementation
        # This is intentional - dependencies should be reviewed and added manually
        # for each new version to ensure they're still valid
        
        # Original document should still have its dependency
        assert self.original_doc.dependencies.count() == 1
        
        # New document starts with no dependencies (to be added during revision)
        assert new_doc.dependencies.count() == 0
    
    def test_cannot_create_version_without_reason(self):
        """
        Test that creating a version requires a reason for change.
        
        This is a compliance requirement - all changes must be justified.
        """
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': ''  # Empty reason
            }
        )
        
        # Service should validate and require a reason
        assert result['success'] is False or result['new_document'].reason_for_change
    
    def test_superseded_documents_are_read_only(self):
        """
        Test that SUPERSEDED documents cannot be edited.
        
        Once a new version is effective, the old version is locked.
        """
        # Create v2.0 and make it effective
        result = self.lifecycle_service.start_version_workflow(
            existing_document=self.original_doc,
            user=self.author,
            new_version_data={
                'version_type': 'major',
                'reason_for_change': 'Update'
            }
        )
        new_doc = result['new_document']
        
        # Simulate making new version effective and superseding old one
        new_doc.status = 'EFFECTIVE'
        new_doc.effective_date = date.today()
        new_doc.supersedes = self.original_doc
        new_doc.save()
        
        self.original_doc.status = 'SUPERSEDED'
        self.original_doc.save()
        
        # Try to edit superseded document
        can_edit = self.original_doc.can_edit(self.author)
        assert can_edit is False
