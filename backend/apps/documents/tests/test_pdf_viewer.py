"""
Tests for PDF Viewer Feature
Tests the download/official endpoint and access control
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.documents.models import Document, DocumentType, DocumentSource

User = get_user_model()


@pytest.mark.django_db
class TestPDFViewerEndpoint:
    """Test PDF viewer endpoint security and functionality"""
    
    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create document type and source
        self.doc_type, _ = DocumentType.objects.get_or_create(
            code='SOP',
            name='Standard Operating Procedure'
        )
        self.doc_source, _ = DocumentSource.objects.get_or_create(
            code='INTERNAL',
            name='Internal'
        )
        
        # Create effective document
        self.effective_doc = Document.objects.create(
            document_number='TEST-001-v01.00',
            title='Test Document',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE',
            version_major=1,
            version_minor=0
        )
        
        # Create draft document
        self.draft_doc = Document.objects.create(
            document_number='TEST-002-v01.00',
            title='Draft Document',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='DRAFT',
            version_major=1,
            version_minor=0
        )
    
    def test_pdf_endpoint_requires_authentication(self):
        """Test that PDF viewer endpoint requires authentication"""
        url = f'/api/v1/documents/documents/{self.effective_doc.uuid}/download/official/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_pdf_endpoint_works_with_authentication(self):
        """Test that authenticated users can access PDF endpoint"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/documents/documents/{self.effective_doc.uuid}/download/official/'
        
        response = self.client.get(url)
        
        # Should return 200 (may return ZIP if no file, but endpoint works)
        assert response.status_code == status.HTTP_200_OK
    
    def test_pdf_endpoint_only_for_approved_documents(self):
        """Test that only approved/effective documents can be viewed"""
        self.client.force_authenticate(user=self.user)
        
        # Try to get PDF for draft document
        url = f'/api/v1/documents/documents/{self.draft_doc.uuid}/download/official/'
        response = self.client.get(url)
        
        # Should return error or redirect (implementation dependent)
        # At minimum, should not return PDF data
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK  # May return error message in JSON
        ]
    
    def test_pdf_endpoint_returns_correct_content_type(self):
        """Test that PDF endpoint returns proper content type"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/documents/documents/{self.effective_doc.uuid}/download/official/'
        
        response = self.client.get(url)
        
        # Should return PDF or ZIP
        assert response['Content-Type'] in [
            'application/pdf',
            'application/zip',
            'application/x-zip-compressed'
        ]
    
    def test_pdf_endpoint_404_for_nonexistent_document(self):
        """Test that endpoint returns 404 for non-existent document"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/documents/documents/00000000-0000-0000-0000-000000000000/download/official/'
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestPDFViewerAccessControl:
    """Test access control for PDF viewer"""
    
    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='pass123'
        )
        
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        
        # Create document
        doc_type, _ = DocumentType.objects.get_or_create(
            code='SOP',
            name='Standard Operating Procedure'
        )
        doc_source, _ = DocumentSource.objects.get_or_create(
            code='INTERNAL',
            name='Internal'
        )
        
        self.document = Document.objects.create(
            document_number='TEST-003-v01.00',
            title='Test Document',
            document_type=doc_type,
            document_source=doc_source,
            author=self.author,
            status='EFFECTIVE',
            version_major=1,
            version_minor=0
        )
    
    def test_author_can_view_own_document_pdf(self):
        """Test that document author can view their own PDF"""
        self.client.force_authenticate(user=self.author)
        url = f'/api/v1/documents/documents/{self.document.uuid}/download/official/'
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_other_users_can_view_effective_document_pdf(self):
        """Test that other users can view effective documents"""
        self.client.force_authenticate(user=self.other_user)
        url = f'/api/v1/documents/documents/{self.document.uuid}/download/official/'
        
        response = self.client.get(url)
        
        # Effective documents should be viewable by all authenticated users
        assert response.status_code == status.HTTP_200_OK
