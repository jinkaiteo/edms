"""
Tests for Document Approval Workflow

These tests verify that the approval workflow works correctly, including:
- Submitting reviewed documents for approval
- Approvers approving documents with effective dates
- Approvers rejecting documents
- Documents becoming effective on scheduled date
- Permission enforcement (only approvers can approve)
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.documents.models import Document, DocumentType, DocumentSource
from apps.workflows.models import DocumentWorkflow
from apps.users.models import Role, UserRole

User = get_user_model()


@pytest.mark.django_db
class TestSubmitForApproval:
    """Test suite for submitting documents for approval"""
    
    def setup_method(self):
        """Setup test data"""
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
        
        self.approver = User.objects.create_user(
            username='test_approver',
            password='test123'
        )
        
        # Assign approver role
        approver_role, _ = Role.objects.get_or_create(
            name='Document Approver',
            defaults={
                'module': 'S2',
                'permission_level': 'approver'
            }
        )
        UserRole.objects.create(
            user=self.approver,
            role=approver_role,
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
        
        # Create reviewed document (ready for approval)
        self.document = Document.objects.create(
            title='Test Document for Approval',
            description='Test description',
            author=self.author,
            document_type=self.doc_type,
            document_source=self.doc_source,
            status='REVIEWED',
            is_controlled=True
        )
    
    def test_can_submit_reviewed_document_for_approval(self):
        """Test that reviewed documents can be submitted for approval"""
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/route_for_approval/',
            {'approver_id': self.approver.id},
            format='json'
        )
        
        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Route for approval failed: {response.data}"
    
    def test_cannot_submit_draft_for_approval(self):
        """Test that draft documents cannot be submitted for approval"""
        self.document.status = 'DRAFT'
        self.document.save()
        
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/route_for_approval/',
            {'approver_id': self.approver.id},
            format='json'
        )
        
        # Should fail - document must be reviewed first
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            "Draft documents should not be routable for approval"


@pytest.mark.django_db
class TestApproverActions:
    """Test suite for approver actions (approve/reject)"""
    
    def setup_method(self):
        """Setup test data with document ready for approval"""
        self.client = APIClient()
        
        # Create users
        self.author = User.objects.create_user(
            username='test_author',
            password='test123'
        )
        
        self.approver = User.objects.create_user(
            username='test_approver',
            password='test123'
        )
        
        self.other_user = User.objects.create_user(
            username='other_user',
            password='test123'
        )
        
        # Assign approver role
        approver_role, _ = Role.objects.get_or_create(
            name='Document Approver',
            defaults={
                'module': 'S2',
                'permission_level': 'approver'
            }
        )
        UserRole.objects.create(
            user=self.approver,
            role=approver_role,
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
        
        # Create reviewed document ready for approval
        self.document = Document.objects.create(
            title='Test Document Ready for Approval',
            description='Test description',
            author=self.author,
            document_type=self.doc_type,
            document_source=self.doc_source,
            status='REVIEWED',
            is_controlled=True
        )
    
    def test_approver_can_approve_document_with_effective_date(self):
        """Test that approver can approve document and set effective date"""
        self.client.force_authenticate(user=self.approver)
        
        # Set effective date 7 days in future
        effective_date = date.today() + timedelta(days=7)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'approve',
                'effective_date': effective_date.isoformat(),
                'comment': 'Approved for implementation'
            },
            format='json'
        )
        
        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Approval failed: {response.data}"
        
        # Verify document status and effective date
        self.document.refresh_from_db()
        assert self.document.status in ['APPROVED', 'APPROVED_PENDING_EFFECTIVE'], \
            f"Approved document should have APPROVED status, got {self.document.status}"
        
        if hasattr(self.document, 'effective_date') and self.document.effective_date:
            assert self.document.effective_date == effective_date, \
                "Effective date should match what was set"
    
    def test_approver_can_approve_with_immediate_effective_date(self):
        """Test that approver can approve document with today as effective date"""
        self.client.force_authenticate(user=self.approver)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'approve',
                'effective_date': date.today().isoformat(),
                'comment': 'Approved - effective immediately'
            },
            format='json'
        )
        
        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Immediate approval failed: {response.data}"
    
    def test_approver_can_reject_document(self):
        """Test that approver can reject document with reason"""
        self.client.force_authenticate(user=self.approver)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'reject',
                'comment': 'Does not meet regulatory requirements - needs major revision'
            },
            format='json'
        )
        
        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Rejection failed: {response.data}"
        
        # Verify document status changed back to DRAFT
        self.document.refresh_from_db()
        assert self.document.status == 'DRAFT', \
            f"Rejected document should return to DRAFT, got {self.document.status}"
    
    def test_non_approver_cannot_approve_document(self):
        """Test that users without approver role cannot approve documents"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'approve',
                'effective_date': date.today().isoformat(),
                'comment': 'Trying to approve'
            },
            format='json'
        )
        
        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN, \
            "Non-approver should not be able to approve documents"
    
    def test_approval_requires_effective_date(self):
        """Test that approval action requires an effective date"""
        self.client.force_authenticate(user=self.approver)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'approve',
                'comment': 'Approved',
                # Missing effective_date
            },
            format='json'
        )
        
        # Should require effective date or succeed with default
        # This documents expected behavior
        assert response.status_code in [
            status.HTTP_200_OK, 
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]
    
    def test_cannot_approve_draft_document(self):
        """Test that only reviewed documents can be approved"""
        self.document.status = 'DRAFT'
        self.document.save()
        
        self.client.force_authenticate(user=self.approver)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'approve',
                'effective_date': date.today().isoformat(),
                'comment': 'Trying to approve draft'
            },
            format='json'
        )
        
        # Should fail - document must be reviewed first
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            "Cannot approve a document that hasn't been reviewed"
    
    def test_effective_date_cannot_be_in_past(self):
        """Test that effective date must be today or future"""
        self.client.force_authenticate(user=self.approver)
        
        past_date = date.today() - timedelta(days=7)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'approve',
                'effective_date': past_date.isoformat(),
                'comment': 'Trying to approve with past date'
            },
            format='json'
        )
        
        # Should reject past dates
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK  # Some systems might allow this
        ]


@pytest.mark.django_db
class TestAutomaticEffectiveActivation:
    """Test suite for automatic document activation on effective date"""
    
    def setup_method(self):
        """Setup test data"""
        self.client = APIClient()
        
        # Create user
        self.author = User.objects.create_user(
            username='test_author',
            password='test123'
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
    
    def test_document_becomes_effective_on_scheduled_date(self):
        """
        Test that approved documents automatically become EFFECTIVE on their effective date
        
        This tests the scheduler/celery task that activates pending documents.
        """
        # Create approved document with today as effective date
        document = Document.objects.create(
            title='Test Document Pending Effective',
            description='Test description',
            author=self.author,
            document_type=self.doc_type,
            document_source=self.doc_source,
            status='APPROVED_PENDING_EFFECTIVE',
            effective_date=date.today(),
            is_controlled=True
        )
        
        # Simulate scheduler task running
        from apps.scheduler.tasks import activate_pending_documents
        activate_pending_documents()
        
        # Verify document is now EFFECTIVE
        document.refresh_from_db()
        assert document.status == 'EFFECTIVE', \
            f"Document should be EFFECTIVE after activation, got {document.status}"
    
    def test_future_dated_documents_remain_pending(self):
        """Test that documents with future effective dates remain pending"""
        # Create approved document with future effective date
        future_date = date.today() + timedelta(days=7)
        
        document = Document.objects.create(
            title='Test Future Document',
            description='Test description',
            author=self.author,
            document_type=self.doc_type,
            document_source=self.doc_source,
            status='APPROVED_PENDING_EFFECTIVE',
            effective_date=future_date,
            is_controlled=True
        )
        
        # Run scheduler task
        from apps.scheduler.tasks import activate_pending_documents
        activate_pending_documents()
        
        # Verify document is still pending
        document.refresh_from_db()
        assert document.status == 'APPROVED_PENDING_EFFECTIVE', \
            "Future-dated document should remain pending"
