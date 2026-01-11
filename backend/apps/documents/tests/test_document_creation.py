"""
Tests for Document Creation Workflow

These tests verify that document creation works correctly and catches
regressions like the author field issue we fixed on 2026-01-10.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.documents.models import Document, DocumentType, DocumentSource

User = get_user_model()


@pytest.mark.django_db
class TestDocumentCreation:
    """Test suite for document creation functionality"""
    
    def setup_method(self):
        """Setup test data before each test"""
        self.client = APIClient()
        
        # Create test user
        self.author = User.objects.create_user(
            username='test_author',
            password='test123',
            email='author@test.com'
        )
        
        # Create document type
        self.doc_type = DocumentType.objects.create(
            code='TST',
            name='Test Document Type',
            description='For testing',
            prefix='TST'
        )
        
        # Create document source
        self.doc_source = DocumentSource.objects.create(
            name='Test Digital Source',
            source_type='original_digital'
        )
    
    def test_create_document_success(self):
        """Test successful document creation with all required fields"""
        self.client.force_authenticate(user=self.author)
        
        data = {
            'title': 'Test Document',
            'description': 'Test description',
            'document_type': self.doc_type.id,
            'document_source': self.doc_source.id,
            'author': self.author.id,
            'is_controlled': True
        }
        
        response = self.client.post('/api/v1/documents/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Test Document'
        assert response.data['author'] == self.author.id
        assert response.data['status'] == 'DRAFT'
    
    def test_create_document_missing_author_field(self):
        """
        REGRESSION TEST: Document creation must include author field
        
        This test catches the bug we fixed on 2026-01-10 where the frontend
        wasn't sending the author field, resulting in 400 Bad Request.
        """
        self.client.force_authenticate(user=self.author)
        
        data = {
            'title': 'Test Document',
            'description': 'Test description',
            'document_type': self.doc_type.id,
            'document_source': self.doc_source.id,
            # Missing 'author' field - this should fail
        }
        
        response = self.client.post('/api/v1/documents/', data, format='json')
        
        # Should return 400 with author field error
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'author' in response.data
    
    def test_create_document_missing_title(self):
        """Test document creation fails without title"""
        self.client.force_authenticate(user=self.author)
        
        data = {
            'description': 'Test description',
            'document_type': self.doc_type.id,
            'document_source': self.doc_source.id,
            'author': self.author.id,
        }
        
        response = self.client.post('/api/v1/documents/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data
    
    def test_create_document_invalid_document_type(self):
        """Test document creation fails with non-existent document type"""
        self.client.force_authenticate(user=self.author)
        
        data = {
            'title': 'Test Document',
            'description': 'Test description',
            'document_type': 9999,  # Non-existent ID
            'document_source': self.doc_source.id,
            'author': self.author.id,
        }
        
        response = self.client.post('/api/v1/documents/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_document_without_authentication(self):
        """Test document creation requires authentication"""
        data = {
            'title': 'Test Document',
            'document_type': self.doc_type.id,
            'document_source': self.doc_source.id,
            'author': self.author.id,
        }
        
        response = self.client.post('/api/v1/documents/', data, format='json')
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_document_defaults_after_creation(self):
        """Test that documents have correct default values after creation"""
        self.client.force_authenticate(user=self.author)
        
        data = {
            'title': 'Test Document',
            'description': 'Test description',
            'document_type': self.doc_type.id,
            'document_source': self.doc_source.id,
            'author': self.author.id,
            'is_controlled': True
        }
        
        response = self.client.post('/api/v1/documents/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check defaults
        assert response.data['status'] == 'DRAFT'
        assert response.data['version_major'] == 1
        assert response.data['version_minor'] == 0
        assert response.data['is_active'] is True
