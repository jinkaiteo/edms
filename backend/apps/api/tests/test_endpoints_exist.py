"""
API Endpoint Existence Tests

These tests verify that critical API endpoints exist and don't return 404.
They catch issues like ViewSets not being registered properly.

REGRESSION TESTS for issues fixed on 2026-01-10:
- Document types endpoint 404
- Document sources endpoint 404
- User role assignment endpoint 404
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCriticalEndpointsExist:
    """Test that all critical API endpoints are registered and accessible"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = APIClient()
        # Create a user for authenticated endpoints
        self.user = User.objects.create_user(
            username='test_user',
            password='test123'
        )
    
    def test_documents_endpoint_exists(self):
        """Test /api/v1/documents/ endpoint exists"""
        response = self.client.get('/api/v1/documents/')
        
        # Should not be 404 (may be 401 if authentication required)
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            "Documents endpoint returns 404 - ViewSet not registered!"
    
    def test_document_types_endpoint_exists(self):
        """
        REGRESSION TEST: /api/v1/document-types/ must exist
        
        This catches the bug we fixed on 2026-01-10 where
        DocumentTypeViewSet wasn't properly registered.
        """
        response = self.client.get('/api/v1/document-types/')
        
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            "Document types endpoint returns 404 - ViewSet not registered!"
    
    def test_document_sources_endpoint_exists(self):
        """
        REGRESSION TEST: /api/v1/document-sources/ must exist
        
        This catches the bug we fixed on 2026-01-10 where
        DocumentSourceViewSet wasn't registered at all.
        """
        response = self.client.get('/api/v1/document-sources/')
        
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            "Document sources endpoint returns 404 - ViewSet not registered!"
    
    def test_users_endpoint_exists(self):
        """Test /api/v1/users/ endpoint exists"""
        response = self.client.get('/api/v1/users/')
        
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            "Users endpoint returns 404 - ViewSet not registered!"
    
    def test_user_assign_role_action_exists(self):
        """
        REGRESSION TEST: /api/v1/users/{id}/assign_role/ must exist
        
        This catches the bug we fixed on 2026-01-07 where
        duplicate UserViewSet registration broke action methods.
        """
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/v1/users/{self.user.id}/assign_role/',
            {'role_id': 1},
            format='json'
        )
        
        # Should not be 404 (may be 400/403 due to invalid data/permissions)
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            "User assign_role action returns 404 - action not registered!"
    
    def test_user_remove_role_action_exists(self):
        """Test /api/v1/users/{id}/remove_role/ action exists"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/v1/users/{self.user.id}/remove_role/',
            {'role_id': 1},
            format='json'
        )
        
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            "User remove_role action returns 404 - action not registered!"
    
    def test_workflows_endpoint_exists(self):
        """Test /api/v1/workflows/ endpoint exists"""
        response = self.client.get('/api/v1/workflows/')
        
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            "Workflows endpoint returns 404 - ViewSet not registered!"
    
    def test_roles_endpoint_exists(self):
        """Test /api/v1/roles/ endpoint exists"""
        response = self.client.get('/api/v1/roles/')
        
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            "Roles endpoint returns 404 - ViewSet not registered!"


@pytest.mark.django_db
class TestNoOldDuplicateEndpoints:
    """Test that old incorrect endpoint paths are NOT accessible"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = APIClient()
    
    def test_old_document_types_path_not_exists(self):
        """
        Test that old incorrect path /api/v1/documents/types/ returns 404
        
        This was the wrong path that caused issues. We want to ensure
        it stays removed and doesn't get re-added accidentally.
        """
        response = self.client.get('/api/v1/documents/types/')
        
        # This SHOULD be 404 (the old wrong path)
        assert response.status_code == status.HTTP_404_NOT_FOUND, \
            "Old incorrect /documents/types/ path still exists! Should be /document-types/"
    
    def test_old_document_sources_path_not_exists(self):
        """Test that old incorrect path /api/v1/documents/sources/ returns 404"""
        response = self.client.get('/api/v1/documents/sources/')
        
        # This SHOULD be 404 (the old wrong path)
        assert response.status_code == status.HTTP_404_NOT_FOUND, \
            "Old incorrect /documents/sources/ path still exists! Should be /document-sources/"
    
    def test_duplicate_users_path_not_exists(self):
        """Test that duplicate /api/v1/users/users/ path doesn't exist"""
        response = self.client.get('/api/v1/users/users/')
        
        # This SHOULD be 404 (was a duplicate registration)
        assert response.status_code == status.HTTP_404_NOT_FOUND, \
            "Duplicate /users/users/ path exists! Should only be /users/"
