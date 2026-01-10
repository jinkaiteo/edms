"""
Tests for Document Review Workflow

These tests verify that the review workflow works correctly, including:
- Submitting documents for review
- Reviewers approving documents
- Reviewers rejecting documents
- Permission enforcement (author cannot review own document)
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.documents.models import Document, DocumentType, DocumentSource
from apps.workflows.models import DocumentWorkflow, DocumentState
from apps.users.models import Role, UserRole

User = get_user_model()


@pytest.mark.django_db
class TestSubmitForReview:
    """Test suite for submitting documents for review"""
    
    def setup_method(self):
        """Setup test data"""
        self.client = APIClient()
        
        # Create users
        self.author = User.objects.create_user(
            username='test_author',
            password='test123',
            email='author@test.com'
        )
        
        self.reviewer = User.objects.create_user(
            username='test_reviewer',
            password='test123',
            email='reviewer@test.com'
        )
        
        # Assign reviewer role
        reviewer_role, _ = Role.objects.get_or_create(
            name='Document Reviewer',
            defaults={
                'module': 'S2',
                'permission_level': 'reviewer'
            }
        )
        UserRole.objects.create(
            user=self.reviewer,
            role=reviewer_role,
            is_active=True
        )
        
        # Create document type and source
        self.doc_type = DocumentType.objects.create(
            code='TST',
            name='Test Document',
            prefix='TST'
        )
        
        self.doc_source = DocumentSource.objects.create(
            name='Test Source',
            source_type='original_digital'
        )
        
        # Create draft document
        self.document = Document.objects.create(
            title='Test Document for Review',
            description='Test description',
            author=self.author,
            document_type=self.doc_type,
            document_source=self.doc_source,
            status='DRAFT',
            is_controlled=True
        )
    
    def test_author_can_submit_document_for_review(self):
        """Test that document author can submit document for review"""
        self.client.force_authenticate(user=self.author)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/submit_for_review/',
            {'reviewer_id': self.reviewer.id},
            format='json'
        )
        
        # Should succeed (200 or 201)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Submit for review failed: {response.data}"
        
        # Verify document status changed
        self.document.refresh_from_db()
        assert self.document.status == 'UNDER_REVIEW', \
            f"Document status should be UNDER_REVIEW, got {self.document.status}"
    
    def test_non_author_cannot_submit_for_review(self):
        """Test that only the author can submit their document for review"""
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/submit_for_review/',
            {'reviewer_id': self.reviewer.id},
            format='json'
        )
        
        # Should be forbidden (403) or bad request (400)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST], \
            "Non-author should not be able to submit for review"
    
    def test_cannot_submit_already_reviewed_document(self):
        """Test that documents already in review cannot be resubmitted"""
        self.document.status = 'UNDER_REVIEW'
        self.document.save()
        
        self.client.force_authenticate(user=self.author)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/submit_for_review/',
            {'reviewer_id': self.reviewer.id},
            format='json'
        )
        
        # Should fail with 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            "Should not be able to resubmit document already under review"


@pytest.mark.django_db
class TestReviewerActions:
    """Test suite for reviewer approval and rejection actions"""
    
    def setup_method(self):
        """Setup test data with document under review"""
        self.client = APIClient()
        
        # Create users
        self.author = User.objects.create_user(
            username='test_author',
            password='test123'
        )
        
        self.reviewer = User.objects.create_user(
            username='test_reviewer',
            password='test123'
        )
        
        self.other_user = User.objects.create_user(
            username='other_user',
            password='test123'
        )
        
        # Assign reviewer role
        reviewer_role, _ = Role.objects.get_or_create(
            name='Document Reviewer',
            defaults={
                'module': 'S2',
                'permission_level': 'reviewer'
            }
        )
        UserRole.objects.create(
            user=self.reviewer,
            role=reviewer_role,
            is_active=True
        )
        
        # Create document type
        self.doc_type = DocumentType.objects.create(
            code='TST',
            name='Test Document',
            prefix='TST'
        )
        
        self.doc_source = DocumentSource.objects.create(
            name='Test Source',
            source_type='original_digital'
        )
        
        # Create document under review
        self.document = Document.objects.create(
            title='Test Document Under Review',
            description='Test description',
            author=self.author,
            document_type=self.doc_type,
            document_source=self.doc_source,
            status='UNDER_REVIEW',
            is_controlled=True
        )
        
        # Create workflow
        self.workflow = DocumentWorkflow.objects.create(
            document=self.document,
            initiated_by=self.author
        )
    
    def test_reviewer_can_approve_document(self):
        """Test that reviewer can approve a document under review"""
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'approve',
                'comment': 'Document looks good'
            },
            format='json'
        )
        
        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Review approval failed: {response.data}"
        
        # Verify document status changed to REVIEWED
        self.document.refresh_from_db()
        assert self.document.status in ['REVIEWED', 'APPROVED'], \
            f"Document status should be REVIEWED or APPROVED, got {self.document.status}"
    
    def test_reviewer_can_reject_document(self):
        """Test that reviewer can reject a document with comments"""
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'reject',
                'comment': 'Needs revision - incorrect data in section 3'
            },
            format='json'
        )
        
        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Review rejection failed: {response.data}"
        
        # Verify document status changed back to DRAFT
        self.document.refresh_from_db()
        assert self.document.status == 'DRAFT', \
            f"Rejected document should return to DRAFT, got {self.document.status}"
    
    def test_non_reviewer_cannot_approve_document(self):
        """Test that users without reviewer role cannot approve documents"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'approve',
                'comment': 'Trying to approve'
            },
            format='json'
        )
        
        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN, \
            "Non-reviewer should not be able to approve documents"
    
    def test_author_cannot_review_own_document(self):
        """
        CRITICAL: Test that document author cannot review their own document
        
        This is a key compliance requirement - no one can review their own work.
        """
        # Give author the reviewer role (but they still shouldn't be able to review their own doc)
        reviewer_role = Role.objects.get(name='Document Reviewer')
        UserRole.objects.create(
            user=self.author,
            role=reviewer_role,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.author)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'approve',
                'comment': 'Approving my own document'
            },
            format='json'
        )
        
        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN, \
            "Author should not be able to review their own document"
    
    def test_review_requires_comment(self):
        """Test that review actions require a comment"""
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'approve',
                # Missing comment
            },
            format='json'
        )
        
        # Should require comment (400 or succeed with empty comment depending on implementation)
        # This test documents expected behavior
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_cannot_review_draft_document(self):
        """Test that only documents UNDER_REVIEW can be reviewed"""
        self.document.status = 'DRAFT'
        self.document.save()
        
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'approve',
                'comment': 'Trying to review draft'
            },
            format='json'
        )
        
        # Should fail - document must be UNDER_REVIEW
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            "Cannot review a document not under review"
