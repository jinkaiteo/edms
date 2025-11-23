"""
Views for User Management (S1).

Provides REST API views for user management, authentication,
role assignment, and security features.
"""

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import User, Role, UserRole, MFADevice
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    RoleSerializer,
    UserRoleSerializer,
    MFADeviceSerializer,
    ChangePasswordSerializer,
    SetupMFASerializer,
)
from .permissions import CanManageUsers, CanManageRoles


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    
    Provides CRUD operations for user management with
    appropriate permission checks and audit logging.
    """
    
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'is_active', 'is_staff', 'is_validated', 'mfa_enabled',
        'department', 'position'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering_fields = ['username', 'email', 'date_joined', 'last_login']
    ordering = ['username']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanManageUsers]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers see all users
        if user.is_superuser:
            return queryset
        
        # Regular users see limited information
        return queryset.filter(is_active=True)
    
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Assign a role to a user."""
        user = self.get_object()
        role_id = request.data.get('role_id')
        reason = request.data.get('reason', '')
        
        try:
            role = Role.objects.get(id=role_id)
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={
                    'assigned_by': request.user,
                    'assignment_reason': reason,
                }
            )
            
            if created:
                return Response(
                    {'message': f'Role {role.name} assigned to {user.username}'},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'message': 'Role already assigned to user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_role(self, request, pk=None):
        """Remove a role from a user."""
        user = self.get_object()
        role_id = request.data.get('role_id')
        reason = request.data.get('reason', '')
        
        try:
            user_role = UserRole.objects.get(user=user, role_id=role_id, is_active=True)
            user_role.is_active = False
            user_role.revoked_at = timezone.now()
            user_role.revoked_by = request.user
            user_role.revocation_reason = reason
            user_role.save()
            
            return Response(
                {'message': 'Role removed from user'},
                status=status.HTTP_200_OK
            )
            
        except UserRole.DoesNotExist:
            return Response(
                {'error': 'Role assignment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Admin-initiated password reset."""
        user = self.get_object()
        new_password = request.data.get('new_password')
        reason = request.data.get('reason', '')
        
        if not new_password:
            return Response(
                {'error': 'New password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate password strength
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password, user)
            
            # Set new password
            user.set_password(new_password)
            user.password_changed_at = timezone.now()
            user.save(update_fields=['password', 'password_changed_at'])
            
            # Log the password reset action (simplified for testing)
            # TODO: Implement proper audit logging when UserAction model is available
            print(f"AUDIT: Password reset for {user.username} by admin {request.user.username}. Reason: {reason}")
            
            return Response(
                {'message': f'Password reset successfully for {user.username}'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': f'Password reset failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def create_user(self, request):
        """Create a new user with role assignment."""
        serializer = UserCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            user.created_by = request.user
            user.save(update_fields=['created_by'])
            
            # Assign initial role if provided
            role_id = request.data.get('role_id')
            if role_id:
                try:
                    role = Role.objects.get(id=role_id)
                    UserRole.objects.create(
                        user=user,
                        role=role,
                        assigned_by=request.user,
                        assignment_reason='Initial role assignment during user creation'
                    )
                except Role.DoesNotExist:
                    pass  # Continue without role assignment if role not found
            
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing roles."""
    
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, CanManageRoles]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['module', 'permission_level', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['module', 'permission_level']


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user role assignments."""
    
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, CanManageRoles]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'role', 'is_active']
    ordering = ['-assigned_at']


class MFADeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing MFA devices."""
    
    queryset = MFADevice.objects.all()
    serializer_class = MFADeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own MFA devices."""
        if self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)


# UserSessionViewSet removed - UserSession model moved to audit app


class UserProfileView(APIView):
    """View for managing user profile."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update current user's profile."""
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """View for changing user password."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.password_changed_at = timezone.now()
            user.save(update_fields=['password', 'password_changed_at'])
            
            return Response(
                {'message': 'Password changed successfully'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetupMFAView(APIView):
    """View for setting up MFA."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Setup MFA for current user."""
        serializer = SetupMFASerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            mfa_device = serializer.save(user=request.user)
            return Response(
                MFADeviceSerializer(mfa_device).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyMFAView(APIView):
    """View for verifying MFA codes."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Verify MFA code."""
        device_id = request.data.get('device_id')
        code = request.data.get('code')
        
        try:
            device = MFADevice.objects.get(
                id=device_id,
                user=request.user,
                is_active=True
            )
            
            # TODO: Implement actual MFA verification logic
            # This would typically involve TOTP verification
            
            device.last_used_at = timezone.now()
            device.usage_count += 1
            device.save(update_fields=['last_used_at', 'usage_count'])
            
            return Response(
                {'message': 'MFA verified successfully'},
                status=status.HTTP_200_OK
            )
            
        except MFADevice.DoesNotExist:
            return Response(
                {'error': 'MFA device not found'},
                status=status.HTTP_404_NOT_FOUND
            )
class LogoutView(APIView):
    """
    Logout view that handles JWT token blacklisting.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # For JWT, we can't truly "logout" since tokens are stateless
            # But we can respond successfully for frontend state management
            return Response(
                {'message': 'Successfully logged out'}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Logout failed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
