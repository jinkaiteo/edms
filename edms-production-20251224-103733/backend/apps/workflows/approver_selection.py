"""
Approver Selection Service

Provides filtered lists of eligible approvers based on permissions, 
document type, criticality level, and workload.
"""

from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.contrib.auth.models import Group
from typing import List, Dict, Any

from .models import DocumentWorkflow

User = get_user_model()


class ApproverSelectionService:
    """
    Service for selecting eligible approvers based on strict role validation.
    """
    
    def get_eligible_approvers(self, document_type: str = None, 
                             criticality: str = 'normal',
                             exclude_user: User = None) -> List[Dict[str, Any]]:
        """
        Get list of users eligible to approve documents.
        
        Args:
            document_type: Type of document (SOP, Policy, etc.)
            criticality: Document criticality level (normal, high, critical)
            exclude_user: User to exclude from results (e.g., document author)
            
        Returns:
            List of eligible approver data dictionaries
        """
        # Base query: Users who are in Document Approvers group OR have explicit approval permission
        approvers_query = User.objects.filter(
            Q(groups__name='Document Approvers') |
            Q(groups__name='Senior Document Approvers') |
            Q(user_permissions__codename='can_approve_document') |
            Q(is_superuser=True)
        ).filter(
            is_active=True
        ).distinct()
        
        # For high/critical documents, require senior approval permissions
        if criticality in ['high', 'critical']:
            approvers_query = approvers_query.filter(
                Q(groups__name='Senior Document Approvers') |
                Q(user_permissions__codename='can_senior_approve_document') |
                Q(is_superuser=True)
            )
        
        # Exclude specific user (e.g., document author)
        if exclude_user:
            approvers_query = approvers_query.exclude(id=exclude_user.id)
        
        # Add workload and availability information
        approver_data = []
        for user in approvers_query:
            # Count active approval tasks
            active_approvals = DocumentWorkflow.objects.filter(
                current_assignee=user,
                current_state__code__in=['UNDER_APPROVAL', 'PENDING_APPROVAL', 'REVIEWED']
            ).count()
            
            # Determine availability and workload status
            workload_status = self._calculate_workload_status(active_approvals)
            is_available = self._is_user_available(user, active_approvals)
            
            # Get user's approval level
            approval_level = self._get_approval_level(user)
            
            # Get department info if available
            department = getattr(user, 'department', None) or 'Unknown'
            
            approver_info = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'active_approvals': active_approvals,
                'workload_status': workload_status,
                'is_available': is_available,
                'approval_level': approval_level,
                'department': department,
                'can_approve_criticality': self._can_approve_criticality(user, criticality),
                'is_recommended': active_approvals <= 2 and is_available,
                # Additional metadata
                'user_groups': list(user.groups.values_list('name', flat=True)),
                'is_superuser': user.is_superuser,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            approver_data.append(approver_info)
        
        # Sort by recommendation, then availability, then workload
        approver_data.sort(key=lambda x: (
            not x['is_recommended'],  # Recommended first
            not x['is_available'],    # Available first  
            x['active_approvals'],    # Lower workload first
            x['full_name']           # Alphabetical by name
        ))
        
        return approver_data
    
    def get_eligible_reviewers(self, document_type: str = None,
                             exclude_user: User = None) -> List[Dict[str, Any]]:
        """
        Get list of users eligible to review documents.
        
        Args:
            document_type: Type of document (SOP, Policy, etc.)
            exclude_user: User to exclude from results (e.g., document author)
            
        Returns:
            List of eligible reviewer data dictionaries
        """
        # Base query: Users who are in Document Reviewers group OR have explicit review permission
        reviewers_query = User.objects.filter(
            Q(groups__name='Document Reviewers') |
            Q(groups__name='Document Approvers') |  # Approvers can also review
            Q(groups__name='Senior Document Approvers') |
            Q(user_permissions__codename='can_review_document') |
            Q(is_staff=True)  # Staff can review
        ).filter(
            is_active=True
        ).distinct()
        
        # Exclude specific user (e.g., document author)
        if exclude_user:
            reviewers_query = reviewers_query.exclude(id=exclude_user.id)
        
        # Add workload and availability information
        reviewer_data = []
        for user in reviewers_query:
            # Count active review tasks
            active_reviews = DocumentWorkflow.objects.filter(
                current_assignee=user,
                current_state__code__in=['UNDER_REVIEW', 'PENDING_REVIEW']
            ).count()
            
            # Determine availability and workload status
            workload_status = self._calculate_workload_status(active_reviews, task_type='review')
            is_available = self._is_user_available(user, active_reviews, task_type='review')
            
            # Get department info if available
            department = getattr(user, 'department', None) or 'Unknown'
            
            reviewer_info = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'active_reviews': active_reviews,
                'workload_status': workload_status,
                'is_available': is_available,
                'department': department,
                'is_recommended': active_reviews <= 3 and is_available,
                # Additional metadata
                'user_groups': list(user.groups.values_list('name', flat=True)),
                'is_staff': user.is_staff,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            reviewer_data.append(reviewer_info)
        
        # Sort by recommendation, then availability, then workload
        reviewer_data.sort(key=lambda x: (
            not x['is_recommended'],  # Recommended first
            not x['is_available'],    # Available first  
            x['active_reviews'],      # Lower workload first
            x['full_name']           # Alphabetical by name
        ))
        
        return reviewer_data
    
    def validate_approver_eligibility(self, user: User, criticality: str = 'normal') -> Dict[str, Any]:
        """
        Validate if a specific user can approve documents of given criticality.
        
        Args:
            user: User to validate
            criticality: Document criticality level
            
        Returns:
            Dictionary with eligibility status and details
        """
        if not user.is_active:
            return {
                'eligible': False,
                'reason': 'User account is not active',
                'approval_level': None
            }
        
        # Check if user has approval permissions
        has_approval_permission = (
            user.groups.filter(name__in=['Document Approvers', 'Senior Document Approvers']).exists() or
            user.user_permissions.filter(codename='can_approve_document').exists() or
            user.is_superuser
        )
        
        if not has_approval_permission:
            return {
                'eligible': False,
                'reason': 'User does not have document approval permissions',
                'approval_level': None
            }
        
        # Check criticality level requirements
        if criticality in ['high', 'critical']:
            has_senior_permission = (
                user.groups.filter(name='Senior Document Approvers').exists() or
                user.user_permissions.filter(codename='can_senior_approve_document').exists() or
                user.is_superuser
            )
            
            if not has_senior_permission:
                return {
                    'eligible': False,
                    'reason': f'User does not have permissions for {criticality} criticality documents',
                    'approval_level': 'standard'
                }
        
        approval_level = self._get_approval_level(user)
        
        return {
            'eligible': True,
            'reason': 'User has required approval permissions',
            'approval_level': approval_level,
            'can_approve_criticality': self._can_approve_criticality(user, criticality)
        }
    
    def _calculate_workload_status(self, active_tasks: int, task_type: str = 'approval') -> str:
        """Calculate workload status based on active task count."""
        if task_type == 'review':
            # Higher thresholds for review tasks
            if active_tasks > 7:
                return 'high'
            elif active_tasks > 3:
                return 'normal'
            else:
                return 'low'
        else:  # approval tasks
            # Lower thresholds for approval tasks (more critical)
            if active_tasks > 4:
                return 'high'
            elif active_tasks > 2:
                return 'normal'
            else:
                return 'low'
    
    def _is_user_available(self, user: User, active_tasks: int, task_type: str = 'approval') -> bool:
        """Determine if user is available for new assignments."""
        if task_type == 'review':
            return active_tasks < 10  # Max 10 concurrent reviews
        else:  # approval tasks
            return active_tasks < 6   # Max 6 concurrent approvals
    
    def _get_approval_level(self, user: User) -> str:
        """Get user's approval level based on groups and permissions."""
        if user.is_superuser:
            return 'superuser'
        elif user.groups.filter(name='Senior Document Approvers').exists():
            return 'senior'
        elif user.groups.filter(name='Document Approvers').exists():
            return 'standard'
        else:
            return 'none'
    
    def _can_approve_criticality(self, user: User, criticality: str) -> bool:
        """Check if user can approve documents of given criticality."""
        if criticality in ['high', 'critical']:
            return (
                user.groups.filter(name='Senior Document Approvers').exists() or
                user.user_permissions.filter(codename='can_senior_approve_document').exists() or
                user.is_superuser
            )
        else:  # normal criticality
            return (
                user.groups.filter(name__in=['Document Approvers', 'Senior Document Approvers']).exists() or
                user.user_permissions.filter(codename='can_approve_document').exists() or
                user.is_superuser
            )


# Service instance
approver_selection_service = ApproverSelectionService()