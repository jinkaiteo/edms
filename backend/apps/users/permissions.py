"""
Custom permissions for User Management (S1).

Implements EDMS-specific permission checks for role-based
access control and compliance requirements.
"""

from rest_framework import permissions


class CanManageUsers(permissions.BasePermission):
    """
    Permission to manage users.
    
    Allows users with 'admin' permission level in S1 module
    to manage other users.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to manage users."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check for S1 admin role
        return request.user.user_roles.filter(
            role__module='S1',
            role__permission_level='admin',
            is_active=True
        ).exists()
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        # Users can always view/edit their own profile
        if obj == request.user:
            return True
        
        # Otherwise check general permission
        return self.has_permission(request, view)


class CanManageRoles(permissions.BasePermission):
    """
    Permission to manage roles and role assignments.
    
    Allows users with 'admin' permission level in S1 module
    to manage roles and assignments.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to manage roles."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check for S1 admin role
        return request.user.user_roles.filter(
            role__module='S1',
            role__permission_level='admin',
            is_active=True
        ).exists()


class CanViewAuditTrail(permissions.BasePermission):
    """
    Permission to view audit trail information.
    
    Allows users with appropriate permissions to view
    audit logs and compliance information.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to view audit trail."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check for S2 (Audit Trail) permissions
        return request.user.user_roles.filter(
            role__module='S2',
            role__permission_level__in=['read', 'write', 'review', 'approve', 'admin'],
            is_active=True
        ).exists()


class CanManageDocuments(permissions.BasePermission):
    """
    Permission to manage documents in EDMS.
    
    Checks for appropriate O1 module permissions based
    on the required action level.
    """
    
    def has_permission(self, request, view):
        """Check basic document management permission."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check for O1 (Document Management) permissions
        return request.user.user_roles.filter(
            role__module='O1',
            role__permission_level__in=['read', 'write', 'review', 'approve', 'admin'],
            is_active=True
        ).exists()
    
    def has_object_permission(self, request, view, obj):
        """Check object-level document permissions."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Get user's O1 permission level
        user_role = request.user.user_roles.filter(
            role__module='O1',
            is_active=True
        ).select_related('role').first()
        
        if not user_role:
            return False
        
        permission_level = user_role.role.permission_level
        
        # Check action-specific permissions
        if view.action in ['list', 'retrieve']:
            # Read permission required
            return permission_level in ['read', 'write', 'review', 'approve', 'admin']
        
        elif view.action in ['create', 'update', 'partial_update']:
            # Write permission required
            return permission_level in ['write', 'review', 'approve', 'admin']
        
        elif view.action in ['review']:
            # Review permission required
            return permission_level in ['review', 'approve', 'admin']
        
        elif view.action in ['approve']:
            # Approve permission required
            return permission_level in ['approve', 'admin']
        
        elif view.action in ['destroy']:
            # Admin permission required
            return permission_level == 'admin'
        
        return False


class CanManageWorkflows(permissions.BasePermission):
    """
    Permission to manage workflows and workflow settings.
    
    Checks for appropriate S5 (Workflow Settings) permissions.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to manage workflows."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check for S5 (Workflow Settings) permissions
        return request.user.user_roles.filter(
            role__module='S5',
            role__permission_level__in=['read', 'write', 'review', 'approve', 'admin'],
            is_active=True
        ).exists()


class CanManagePlaceholders(permissions.BasePermission):
    """
    Permission to manage placeholders and document templates.
    
    Checks for appropriate S6 (Placeholder Management) permissions.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to manage placeholders."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check for S6 (Placeholder Management) permissions
        return request.user.user_roles.filter(
            role__module='S6',
            role__permission_level__in=['read', 'write', 'review', 'approve', 'admin'],
            is_active=True
        ).exists()


class CanManageSystem(permissions.BasePermission):
    """
    Permission to manage system settings and configurations.
    
    Checks for appropriate S7 (App Settings) permissions.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to manage system settings."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check for S7 (App Settings) permissions
        return request.user.user_roles.filter(
            role__module='S7',
            role__permission_level__in=['read', 'write', 'review', 'approve', 'admin'],
            is_active=True
        ).exists()