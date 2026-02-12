"""
Access Control System for Sensitivity Labels

This module implements role-based access control (RBAC) for documents
based on their sensitivity labels. It provides functions to check if a user
can view, download, or perform actions on documents with different sensitivity levels.
"""

from typing import Optional, Dict, List
from django.contrib.auth import get_user_model
from .sensitivity_labels import (
    SENSITIVITY_METADATA,
    get_access_control_config,
    requires_specific_role,
    get_minimum_roles,
    get_sensitivity_level,
    is_higher_sensitivity
)

User = get_user_model()


class SensitivityAccessControl:
    """
    Main access control class for sensitivity-based document access.
    
    Implements multi-level security checks:
    - Level 1: View access (can user see the document?)
    - Level 2: Download access (can user download the document?)
    - Level 3: Action access (can user approve/review this sensitivity level?)
    - Level 4: Audit logging (track access for high sensitivity)
    """
    
    @staticmethod
    def can_view_document(user: User, document) -> Dict[str, any]:
        """
        Check if user can view a document based on its sensitivity label.
        
        Args:
            user: User requesting access
            document: Document object with sensitivity_label field
            
        Returns:
            dict: {
                'allowed': bool,
                'reason': str,
                'requires_justification': bool,
                'log_access': bool
            }
        """
        if not user.is_authenticated:
            # Only PUBLIC documents can be viewed without authentication
            if document.sensitivity_label == 'PUBLIC':
                return {
                    'allowed': True,
                    'reason': 'Public document - no authentication required',
                    'requires_justification': False,
                    'log_access': False
                }
            return {
                'allowed': False,
                'reason': 'Authentication required',
                'requires_justification': False,
                'log_access': False
            }
        
        # Get access control config for this sensitivity level
        config = get_access_control_config(document.sensitivity_label)
        
        # Admin users can view everything
        if user.is_superuser:
            return {
                'allowed': True,
                'reason': 'Administrator access',
                'requires_justification': config.get('requires_justification', False),
                'log_access': config.get('log_views', False)
            }
        
        # Check if sensitivity level requires specific roles
        if config.get('requires_specific_role', False):
            # Check user has one of the minimum required permission levels
            has_required_role = SensitivityAccessControl._has_required_permission_level(
                user, 
                config.get('minimum_permission_levels', [])
            )
            
            if not has_required_role:
                return {
                    'allowed': False,
                    'reason': f'Insufficient permissions for {document.get_sensitivity_label_display()} documents',
                    'requires_justification': False,
                    'log_access': False
                }
        
        # RESTRICTED documents require approve-level permission
        if document.sensitivity_label == 'RESTRICTED':
            if not SensitivityAccessControl._has_permission_level(user, 'approve'):
                return {
                    'allowed': False,
                    'reason': 'Approver-level permission required for RESTRICTED documents',
                    'requires_justification': False,
                    'log_access': True
                }
        
        # PROPRIETARY documents require admin-level permission
        if document.sensitivity_label == 'PROPRIETARY':
            if not SensitivityAccessControl._has_permission_level(user, 'admin'):
                return {
                    'allowed': False,
                    'reason': 'Admin-level permission required for PROPRIETARY documents',
                    'requires_justification': False,
                    'log_access': True
                }
        
        # Access granted
        return {
            'allowed': True,
            'reason': 'Access granted',
            'requires_justification': config.get('requires_justification', False),
            'log_access': config.get('log_views', False),
            'alert_on_access': config.get('alert_on_access', False)
        }
    
    @staticmethod
    def can_download_document(user: User, document) -> Dict[str, any]:
        """
        Check if user can download a document based on its sensitivity label.
        
        Downloads have stricter requirements than viewing.
        
        Args:
            user: User requesting download
            document: Document object
            
        Returns:
            dict: {
                'allowed': bool,
                'reason': str,
                'requires_approval': bool,
                'log_download': bool
            }
        """
        # First check if user can view
        view_result = SensitivityAccessControl.can_view_document(user, document)
        if not view_result['allowed']:
            return {
                'allowed': False,
                'reason': view_result['reason'],
                'requires_approval': False,
                'log_download': True
            }
        
        config = get_access_control_config(document.sensitivity_label)
        
        # Check if printing/downloading is allowed for this sensitivity
        if not config.get('allow_printing', True):
            # RESTRICTED and PROPRIETARY documents may block downloads
            if not user.is_superuser:
                return {
                    'allowed': False,
                    'reason': f'{document.get_sensitivity_label_display()} documents cannot be downloaded without special approval',
                    'requires_approval': True,
                    'log_download': True
                }
        
        # All downloads are logged for CONFIDENTIAL and above
        log_download = config.get('log_downloads', False) or document.sensitivity_label in ['CONFIDENTIAL', 'RESTRICTED', 'PROPRIETARY']
        
        return {
            'allowed': True,
            'reason': 'Download authorized',
            'requires_approval': False,
            'log_download': log_download,
            'alert_on_access': config.get('alert_on_access', False)
        }
    
    @staticmethod
    def can_approve_sensitivity_level(user: User, sensitivity_label: str) -> Dict[str, any]:
        """
        Check if user can approve documents at a given sensitivity level.
        
        Higher sensitivity documents require higher-level approvers.
        
        Args:
            user: User who would be approving
            sensitivity_label: Sensitivity level to check
            
        Returns:
            dict: {
                'allowed': bool,
                'reason': str,
                'requires_additional_approval': bool
            }
        """
        if user.is_superuser:
            return {
                'allowed': True,
                'reason': 'Administrator can approve any sensitivity level',
                'requires_additional_approval': False
            }
        
        config = get_access_control_config(sensitivity_label)
        
        # Check if user has required permission level for this sensitivity
        if config.get('requires_specific_permission', False):
            has_permission = SensitivityAccessControl._has_required_permission_level(
                user,
                config.get('minimum_permission_levels', [])
            )
            
            if not has_permission:
                required_levels = config.get('minimum_permission_levels', [])
                return {
                    'allowed': False,
                    'reason': f'Insufficient permissions to approve {sensitivity_label} documents. Required: {", ".join(required_levels)}',
                    'requires_additional_approval': False
                }
        
        # RESTRICTED requires approve+ permission
        if sensitivity_label == 'RESTRICTED':
            if not SensitivityAccessControl._has_permission_level(user, 'approve'):
                return {
                    'allowed': False,
                    'reason': 'RESTRICTED documents require approve-level permission',
                    'requires_additional_approval': True
                }
        
        # PROPRIETARY requires admin permission
        if sensitivity_label == 'PROPRIETARY':
            if not SensitivityAccessControl._has_permission_level(user, 'admin'):
                return {
                    'allowed': False,
                    'reason': 'PROPRIETARY documents require admin-level permission',
                    'requires_additional_approval': True
                }
        
        return {
            'allowed': True,
            'reason': f'User authorized to approve {sensitivity_label} documents',
            'requires_additional_approval': False
        }
    
    @staticmethod
    def validate_sensitivity_change(old_label: str, new_label: str, user: User, reason: str = '') -> Dict[str, any]:
        """
        Validate if a user can change sensitivity label from old to new level.
        
        Args:
            old_label: Current sensitivity label
            new_label: Proposed new sensitivity label
            user: User making the change
            reason: Reason for change
            
        Returns:
            dict: {
                'allowed': bool,
                'reason': str,
                'requires_reason': bool,
                'severity': str  # 'upgrade', 'downgrade', or 'none'
            }
        """
        if old_label == new_label:
            return {
                'allowed': True,
                'reason': 'No change in sensitivity',
                'requires_reason': False,
                'severity': 'none'
            }
        
        # Determine if upgrade or downgrade
        old_level = get_sensitivity_level(old_label)
        new_level = get_sensitivity_level(new_label)
        
        is_upgrade = new_level > old_level
        severity = 'upgrade' if is_upgrade else 'downgrade'
        
        # Check if user can approve the NEW sensitivity level
        can_approve = SensitivityAccessControl.can_approve_sensitivity_level(user, new_label)
        if not can_approve['allowed']:
            return {
                'allowed': False,
                'reason': f'Cannot change to {new_label}: {can_approve["reason"]}',
                'requires_reason': True,
                'severity': severity
            }
        
        # Downgrades always require detailed reason
        if not is_upgrade:
            if not reason or len(reason.strip()) < 20:
                return {
                    'allowed': False,
                    'reason': 'Sensitivity downgrade requires detailed justification (minimum 20 characters)',
                    'requires_reason': True,
                    'severity': severity
                }
        
        # Upgrades also require reason for audit trail
        if is_upgrade and not reason:
            return {
                'allowed': False,
                'reason': 'Sensitivity upgrade requires justification for audit trail',
                'requires_reason': True,
                'severity': severity
            }
        
        return {
            'allowed': True,
            'reason': f'Authorized to change sensitivity from {old_label} to {new_label}',
            'requires_reason': True,
            'severity': severity
        }
    
    @staticmethod
    def get_user_accessible_sensitivity_levels(user: User) -> List[str]:
        """
        Get list of sensitivity levels user can access.
        
        Args:
            user: User to check
            
        Returns:
            List of sensitivity label codes user can access
        """
        if not user.is_authenticated:
            return ['PUBLIC']
        
        if user.is_superuser:
            return ['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', 'PROPRIETARY']
        
        accessible = ['PUBLIC', 'INTERNAL']  # Everyone can access these
        
        # Check for CONFIDENTIAL access (requires review+ permission)
        if SensitivityAccessControl._has_permission_level(user, 'review'):
            accessible.append('CONFIDENTIAL')
        
        # Check for RESTRICTED access (requires approve+ permission)
        if SensitivityAccessControl._has_permission_level(user, 'approve'):
            accessible.append('RESTRICTED')
        
        # Check for PROPRIETARY access (requires admin permission)
        if SensitivityAccessControl._has_permission_level(user, 'admin'):
            accessible.append('PROPRIETARY')
        
        return accessible
    
    # Helper methods for role checking
    
    @staticmethod
    def _has_required_role(user: User, required_roles: List[str]) -> bool:
        """
        Check if user has any of the required roles.
        
        Uses actual permission_level hierarchy from Role model:
        read < write < review < approve < admin
        """
        if not required_roles:
            return True
        
        # Check user's permission levels for O1 (Document Management) module
        user_permission_levels = user.user_roles.filter(
            role__module='O1',
            is_active=True
        ).values_list('role__permission_level', flat=True)
        
        # Check if user has any of the required permission levels
        return any(perm_level in required_roles for perm_level in user_permission_levels)
    
    @staticmethod
    def _has_permission_level(user: User, minimum_level: str) -> bool:
        """
        Check if user has at least the minimum permission level for O1 module.
        
        Permission hierarchy: read < write < review < approve < admin
        """
        PERMISSION_HIERARCHY = ['read', 'write', 'review', 'approve', 'admin']
        
        if minimum_level not in PERMISSION_HIERARCHY:
            return False
        
        min_index = PERMISSION_HIERARCHY.index(minimum_level)
        
        # Get user's permission levels for O1 module
        user_permission_levels = user.user_roles.filter(
            role__module='O1',
            is_active=True
        ).values_list('role__permission_level', flat=True)
        
        # Check if user has any permission level >= minimum_level
        for perm_level in user_permission_levels:
            if perm_level in PERMISSION_HIERARCHY:
                user_index = PERMISSION_HIERARCHY.index(perm_level)
                if user_index >= min_index:
                    return True
        
        return False
    
    @staticmethod
    def _has_required_permission_level(user: User, required_levels: List[str]) -> bool:
        """Check if user has any of the required permission levels."""
        if not required_levels:
            return True
        
        user_permission_levels = user.user_roles.filter(
            role__module='O1',
            is_active=True
        ).values_list('role__permission_level', flat=True)
        
        return any(perm_level in required_levels for perm_level in user_permission_levels)
    
    # Note: Manager/Executive approval methods removed
    # Access control is now based on permission_level hierarchy
    # Future enhancement: Add DocumentAccessApproval model for time-limited access grants


# Convenience functions for use in views and permissions

def can_user_view_document(user: User, document) -> bool:
    """Quick check if user can view document."""
    result = SensitivityAccessControl.can_view_document(user, document)
    return result['allowed']


def can_user_download_document(user: User, document) -> bool:
    """Quick check if user can download document."""
    result = SensitivityAccessControl.can_download_document(user, document)
    return result['allowed']


def can_user_approve_sensitivity(user: User, sensitivity_label: str) -> bool:
    """Quick check if user can approve documents at sensitivity level."""
    result = SensitivityAccessControl.can_approve_sensitivity_level(user, sensitivity_label)
    return result['allowed']


def should_log_document_access(document) -> bool:
    """Check if document access should be logged."""
    config = get_access_control_config(document.sensitivity_label)
    return config.get('log_views', False) or config.get('log_downloads', False)


def should_alert_on_access(document) -> bool:
    """Check if document access should trigger security alerts."""
    config = get_access_control_config(document.sensitivity_label)
    return config.get('alert_on_access', False)
