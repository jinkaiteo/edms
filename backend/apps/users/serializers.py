"""
Serializers for User Management (S1).

Provides serialization for users, roles, and related models
with validation and security considerations.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User, Role, UserRole, MFADevice


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.SerializerMethodField()
    active_roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'uuid', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'employee_id', 'phone_number', 'department',
            'position', 'is_active', 'is_staff', 'is_superuser', 'is_validated', 'mfa_enabled',
            'date_joined', 'last_login', 'active_roles'
        ]
        read_only_fields = ['id', 'uuid', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        """Return the full name of the user."""
        return obj.get_full_name()
    
    def get_active_roles(self, obj):
        """Return active roles for the user."""
        # The related_name is correctly set to 'user_roles' in UserRole model
        active_roles = obj.user_roles.filter(is_active=True).select_related('role')
        return [
            {
                'id': ur.role.id,
                'name': ur.role.name,
                'module': ur.role.module,
                'permission_level': ur.role.permission_level,
                'assigned_at': ur.assigned_at
            }
            for ur in active_roles
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'employee_id', 'phone_number',
            'department', 'position'
        ]
    
    def validate(self, data):
        """Validate password confirmation."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate password strength
        try:
            validate_password(data['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        
        return data
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    user_count = serializers.SerializerMethodField()
    module_display = serializers.CharField(source='get_module_display', read_only=True)
    permission_level_display = serializers.CharField(
        source='get_permission_level_display', 
        read_only=True
    )
    
    class Meta:
        model = Role
        fields = [
            'id', 'uuid', 'name', 'description', 'module', 'module_display',
            'permission_level', 'permission_level_display', 'inherits_from',
            'is_active', 'is_system_role', 'user_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        """Return the number of active users with this role."""
        return obj.role_users.filter(is_active=True).count()


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole assignments."""
    
    user_display = serializers.CharField(source='user.username', read_only=True)
    role_display = serializers.CharField(source='role.name', read_only=True)
    assigned_by_display = serializers.CharField(
        source='assigned_by.username', 
        read_only=True
    )
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'uuid', 'user', 'user_display', 'role', 'role_display',
            'assigned_at', 'assigned_by', 'assigned_by_display',
            'expires_at', 'is_active', 'assignment_reason'
        ]
        read_only_fields = ['id', 'uuid', 'assigned_at', 'assigned_by']
    
    def create(self, validated_data):
        """Create user role assignment with current user as assigner."""
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)


class MFADeviceSerializer(serializers.ModelSerializer):
    """Serializer for MFA devices."""
    
    device_type_display = serializers.CharField(
        source='get_device_type_display', 
        read_only=True
    )
    
    class Meta:
        model = MFADevice
        fields = [
            'id', 'uuid', 'device_type', 'device_type_display', 'name',
            'phone_number', 'email_address', 'is_active', 'is_verified',
            'last_used_at', 'usage_count', 'created_at'
        ]
        read_only_fields = [
            'id', 'uuid', 'is_verified', 'last_used_at', 'usage_count', 'created_at'
        ]
        extra_kwargs = {
            'secret_key': {'write_only': True},
            'backup_codes': {'write_only': True},
        }


# UserSessionSerializer removed - UserSession model moved to audit app


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change requests."""
    
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['user']
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value
    
    def validate(self, data):
        """Validate new password."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        
        # Validate password strength
        try:
            validate_password(data['new_password'], self.context['user'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})
        
        return data


class SetupMFASerializer(serializers.ModelSerializer):
    """Serializer for MFA setup."""
    
    class Meta:
        model = MFADevice
        fields = ['device_type', 'name', 'phone_number', 'email_address']
    
    def validate(self, data):
        """Validate MFA setup data."""
        device_type = data['device_type']
        
        if device_type == 'sms' and not data.get('phone_number'):
            raise serializers.ValidationError(
                "Phone number is required for SMS MFA"
            )
        
        if device_type == 'email' and not data.get('email_address'):
            raise serializers.ValidationError(
                "Email address is required for email MFA"
            )
        
        return data
    
    def create(self, validated_data):
        """Create MFA device with proper configuration."""
        device_type = validated_data['device_type']
        
        # Generate secret key for TOTP devices
        if device_type == 'totp':
            import secrets
            validated_data['secret_key'] = secrets.token_hex(20)
        
        # Generate backup codes
        if device_type in ['totp', 'backup']:
            import secrets
            backup_codes = [secrets.token_hex(8) for _ in range(10)]
            validated_data['backup_codes'] = backup_codes
        
        return super().create(validated_data)