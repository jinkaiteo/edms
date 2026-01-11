"""
Document Dependency Manager for EDMS Workflows.

Implements dependency checking and validation as required by EDMS_details_workflow.txt:
- Check for dependent documents before obsoleting
- Prevent obsoleting if dependencies exist
- Impact analysis for up-versioning workflows
"""

from django.db.models import Q
from apps.documents.models import Document, DocumentDependency


class DocumentDependencyManager:
    """Manages document dependencies for workflow operations."""
    
    @staticmethod
    def check_dependencies(document):
        """
        Check if other documents depend on the given document.
        
        Args:
            document: Document instance to check
            
        Returns:
            dict: {
                'has_dependencies': bool,
                'dependent_documents': QuerySet,
                'count': int
            }
        """
        # Find documents that reference this document as a dependency
        dependencies = DocumentDependency.objects.filter(
            dependency=document,
            dependent_document__status__in=['APPROVED_AND_EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
        ).select_related('dependent_document')
        
        dependent_documents = [dep.dependent_document for dep in dependencies]
        
        return {
            'has_dependencies': len(dependent_documents) > 0,
            'dependent_documents': dependent_documents,
            'count': len(dependent_documents)
        }
    
    @staticmethod
    def can_obsolete(document):
        """
        Check if a document can be obsoleted.
        Per specification: prevent obsoleting if dependencies exist.
        
        Args:
            document: Document to check for obsoleting
            
        Returns:
            dict: {
                'can_obsolete': bool,
                'blocking_dependencies': list,
                'reason': str
            }
        """
        if document.status not in ['APPROVED_AND_EFFECTIVE']:
            return {
                'can_obsolete': False,
                'blocking_dependencies': [],
                'reason': 'Document must be "Approved and Effective" to obsolete'
            }
        
        dependency_check = DocumentDependencyManager.check_dependencies(document)
        
        if dependency_check['has_dependencies']:
            return {
                'can_obsolete': False,
                'blocking_dependencies': dependency_check['dependent_documents'],
                'reason': f"{dependency_check['count']} approved documents depend on this document"
            }
        
        return {
            'can_obsolete': True,
            'blocking_dependencies': [],
            'reason': 'No blocking dependencies found'
        }
    
    @staticmethod
    def get_impact_analysis(document):
        """
        Get impact analysis for up-versioning a document.
        
        Args:
            document: Document being up-versioned
            
        Returns:
            dict: {
                'affected_documents': list,
                'notification_recipients': list,
                'impact_summary': str
            }
        """
        dependency_check = DocumentDependencyManager.check_dependencies(document)
        
        affected_documents = dependency_check['dependent_documents']
        
        # Get authors and approvers of affected documents for notification
        notification_recipients = set()
        for doc in affected_documents:
            if hasattr(doc, 'author') and doc.author:
                notification_recipients.add(doc.author)
            if hasattr(doc, 'approver') and doc.approver:
                notification_recipients.add(doc.approver)
        
        impact_summary = f"""
        Up-versioning impact analysis:
        - {len(affected_documents)} documents reference this document
        - {len(notification_recipients)} users will be notified to review impact
        - Affected documents may need revision after this document is updated
        """
        
        return {
            'affected_documents': affected_documents,
            'notification_recipients': list(notification_recipients),
            'impact_summary': impact_summary.strip()
        }
    
    @staticmethod
    def validate_obsoleting_workflow(document):
        """
        Validate obsoleting workflow before proceeding.
        Implements final dependency check as per specification.
        
        Args:
            document: Document in obsoleting workflow
            
        Returns:
            dict: {
                'valid': bool,
                'action': str,  # 'proceed' or 'terminate'
                'reason': str
            }
        """
        # Final check as per specification line 41-44
        final_check = DocumentDependencyManager.can_obsolete(document)
        
        if not final_check['can_obsolete']:
            return {
                'valid': False,
                'action': 'terminate',
                'reason': f"Final validation failed: {final_check['reason']}"
            }
        
        return {
            'valid': True,
            'action': 'proceed',
            'reason': 'Document can be safely obsoleted'
        }