"""
Tests for Superuser Management Feature
Tests grant/revoke superuser actions and protection logic
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestSuperuserProtection:
    """Test superuser protection (prevent locking out of admin)"""
    
    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.superuser.refresh_from_db()  # Ensure UUID is loaded
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='pass123'
        )
        self.regular_user.refresh_from_db()  # Ensure UUID is loaded
    
    def test_cannot_deactivate_last_superuser(self):
        """Test that system prevents deactivating the last superuser"""
        self.client.force_authenticate(user=self.superuser)
        
        # Try to deactivate the only superuser
        url = f'/api/v1/users/users/{self.superuser.uuid}/'
        response = self.client.patch(url, {'is_active': False})
        
        # Should be blocked
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'last superuser' in response.data.get('error', '').lower()
    
    def test_can_deactivate_superuser_when_multiple_exist(self):
        """Test that superuser can be deactivated when others exist"""
        # Create second superuser
        second_super = User.objects.create_superuser(
            username='admin2',
            email='admin2@example.com',
            password='admin123'
        )
        
        self.client.force_authenticate(user=self.superuser)
        
        # Now deactivation should work (2 superusers exist)
        url = f'/api/v1/users/users/{self.superuser.uuid}/'
        response = self.client.patch(url, {'is_active': False})
        
        # Should succeed
        assert response.status_code == status.HTTP_200_OK
        
        # Verify user is deactivated
        self.superuser.refresh_from_db()
        assert self.superuser.is_active is False
    
    def test_regular_users_see_active_users_only(self):
        """Test that regular users only see active users"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Create inactive user
        User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='pass123',
            is_active=False
        )
        
        url = '/api/v1/users/users/'
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Should only see active users
        usernames = [u['username'] for u in response.data['results']]
        assert 'inactive' not in usernames


@pytest.mark.django_db
class TestGrantSuperuserAction:
    """Test grant_superuser action"""
    
    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.superuser.refresh_from_db()  # Ensure UUID is loaded
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='pass123'
        )
        self.regular_user.refresh_from_db()  # Ensure UUID is loaded
    
    def test_superuser_can_grant_superuser_status(self):
        """Test that superuser can grant superuser status to another user"""
        self.client.force_authenticate(user=self.superuser)
        
        url = f'/api/v1/users/users/{self.regular_user.uuid}/grant_superuser/'
        response = self.client.post(url, {'reason': 'Promoting to admin team'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_superuser'] is True
        
        # Verify in database
        self.regular_user.refresh_from_db()
        assert self.regular_user.is_superuser is True
        assert self.regular_user.is_staff is True
    
    def test_regular_user_cannot_grant_superuser(self):
        """Test that regular users cannot grant superuser status"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Create another regular user
        target_user = User.objects.create_user(
            username='target',
            email='target@example.com',
            password='pass123'
        )
        
        url = f'/api/v1/users/users/{target_user.uuid}/grant_superuser/'
        response = self.client.post(url, {'reason': 'Trying to grant'})
        
        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_grant_superuser_to_existing_superuser(self):
        """Test granting superuser to someone who already is one"""
        self.client.force_authenticate(user=self.superuser)
        
        # Create another superuser
        another_super = User.objects.create_superuser(
            username='admin2',
            email='admin2@example.com',
            password='admin123'
        )
        
        url = f'/api/v1/users/users/{another_super.uuid}/grant_superuser/'
        response = self.client.post(url, {'reason': 'Already superuser'})
        
        # Should return error (already superuser)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already' in response.data.get('message', '').lower()
    
    def test_grant_superuser_requires_authentication(self):
        """Test that grant_superuser requires authentication"""
        url = f'/api/v1/users/users/{self.regular_user.uuid}/grant_superuser/'
        response = self.client.post(url, {'reason': 'No auth'})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRevokeSuperuserAction:
    """Test revoke_superuser action"""
    
    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create two superusers
        self.superuser1 = User.objects.create_superuser(
            username='admin1',
            email='admin1@example.com',
            password='admin123'
        )
        self.superuser1.refresh_from_db()  # Ensure UUID is loaded
        
        self.superuser2 = User.objects.create_superuser(
            username='admin2',
            email='admin2@example.com',
            password='admin123'
        )
        self.superuser2.refresh_from_db()  # Ensure UUID is loaded
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='pass123'
        )
        self.regular_user.refresh_from_db()  # Ensure UUID is loaded
    
    def test_can_revoke_superuser_when_multiple_exist(self):
        """Test revoking superuser when multiple superusers exist"""
        self.client.force_authenticate(user=self.superuser1)
        
        url = f'/api/v1/users/users/{self.superuser2.uuid}/revoke_superuser/'
        response = self.client.post(url, {'reason': 'Leaving admin team'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_superuser'] is False
        
        # Verify in database
        self.superuser2.refresh_from_db()
        assert self.superuser2.is_superuser is False
    
    def test_cannot_revoke_last_superuser(self):
        """Test protection against revoking the last superuser"""
        # Deactivate superuser2 to leave only one
        self.superuser2.is_active = False
        self.superuser2.save()
        
        self.client.force_authenticate(user=self.superuser1)
        
        url = f'/api/v1/users/users/{self.superuser1.uuid}/revoke_superuser/'
        response = self.client.post(url, {'reason': 'Trying to revoke last'})
        
        # Should be blocked
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'last' in response.data.get('error', '').lower()
        
        # Verify still superuser
        self.superuser1.refresh_from_db()
        assert self.superuser1.is_superuser is True
    
    def test_regular_user_cannot_revoke_superuser(self):
        """Test that regular users cannot revoke superuser status"""
        self.client.force_authenticate(user=self.regular_user)
        
        url = f'/api/v1/users/users/{self.superuser1.uuid}/revoke_superuser/'
        response = self.client.post(url, {'reason': 'Unauthorized attempt'})
        
        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_revoke_from_non_superuser(self):
        """Test revoking superuser from user who isn't one"""
        self.client.force_authenticate(user=self.superuser1)
        
        url = f'/api/v1/users/users/{self.regular_user.uuid}/revoke_superuser/'
        response = self.client.post(url, {'reason': 'Not a superuser'})
        
        # Should return error (not a superuser)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'not a superuser' in response.data.get('message', '').lower()


@pytest.mark.django_db
class TestSuperuserManagementIntegration:
    """Integration tests for superuser management workflow"""
    
    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create initial superuser
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.admin.refresh_from_db()  # Ensure UUID is loaded
        
        # Create users to promote
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user1.refresh_from_db()  # Ensure UUID is loaded
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.user2.refresh_from_db()  # Ensure UUID is loaded
    
    def test_safe_superuser_transition_workflow(self):
        """Test safe transfer of superuser duties"""
        self.client.force_authenticate(user=self.admin)
        
        # Step 1: Grant superuser to new admin
        url = f'/api/v1/users/users/{self.user1.uuid}/grant_superuser/'
        response = self.client.post(url, {'reason': 'New admin'})
        assert response.status_code == status.HTTP_200_OK
        
        # Step 2: Verify now have 2 superusers
        active_superusers = User.objects.filter(
            is_superuser=True,
            is_active=True
        ).count()
        assert active_superusers == 2
        
        # Step 3: Can now safely deactivate original admin
        url = f'/api/v1/users/users/{self.admin.uuid}/'
        response = self.client.patch(url, {'is_active': False})
        assert response.status_code == status.HTTP_200_OK
        
        # Step 4: Still have 1 active superuser
        active_superusers = User.objects.filter(
            is_superuser=True,
            is_active=True
        ).count()
        assert active_superusers == 1
    
    def test_multi_superuser_redundancy(self):
        """Test system with multiple superusers for redundancy"""
        self.client.force_authenticate(user=self.admin)
        
        # Create 3 superusers total
        for user in [self.user1, self.user2]:
            url = f'/api/v1/users/users/{user.uuid}/grant_superuser/'
            response = self.client.post(url, {'reason': 'Redundancy'})
            assert response.status_code == status.HTTP_200_OK
        
        # Verify 3 superusers
        superuser_count = User.objects.filter(
            is_superuser=True,
            is_active=True
        ).count()
        assert superuser_count == 3
        
        # Can deactivate any one of them
        url = f'/api/v1/users/users/{self.admin.uuid}/'
        response = self.client.patch(url, {'is_active': False})
        assert response.status_code == status.HTTP_200_OK
        
        # Still have 2 active superusers
        superuser_count = User.objects.filter(
            is_superuser=True,
            is_active=True
        ).count()
        assert superuser_count == 2
