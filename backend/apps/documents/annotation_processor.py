"""
Document Annotation Processor
Handles placeholder replacement and metadata annotation for documents
"""

import re
from datetime import datetime, date
from typing import Dict, Any
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Document
from apps.placeholders.models import PlaceholderDefinition

User = get_user_model()


class DocumentAnnotationProcessor:
    """
    Service class for processing document placeholders and generating annotated versions
    """
    
    def __init__(self):
        self.placeholder_pattern = re.compile(r'\{\{([A-Z_]+)\}\}')
        
    def get_document_metadata(self, document: Document, user: User = None) -> Dict[str, Any]:
        """
        Extract metadata from document for placeholder replacement
        """
        metadata = {}
        
        # Core document information
        metadata['DOC_NUMBER'] = document.document_number or 'Not Assigned'
        metadata['DOC_TITLE'] = document.title or 'Untitled Document'
        metadata['DOC_VERSION'] = document.version_string or '1.0'
        metadata['DOC_TYPE'] = document.document_type.name if document.document_type else 'Unknown'
        metadata['DOC_SOURCE'] = document.document_source.name if document.document_source else 'Unknown'
        metadata['DOC_DESCRIPTION'] = document.description or 'No description'
        metadata['DOC_UUID'] = str(document.uuid)
        
        # People information
        if document.author:
            metadata['AUTHOR_NAME'] = f"{document.author.first_name} {document.author.last_name}".strip() or document.author.username
            metadata['AUTHOR_EMAIL'] = document.author.email
        else:
            metadata['AUTHOR_NAME'] = 'Unknown Author'
            metadata['AUTHOR_EMAIL'] = 'unknown@example.com'
            
        if document.reviewer:
            metadata['REVIEWER_NAME'] = f"{document.reviewer.first_name} {document.reviewer.last_name}".strip() or document.reviewer.username
            metadata['REVIEWER_EMAIL'] = document.reviewer.email
        else:
            metadata['REVIEWER_NAME'] = 'Not Assigned'
            metadata['REVIEWER_EMAIL'] = 'not.assigned@example.com'
            
        if document.approver:
            metadata['APPROVER_NAME'] = f"{document.approver.first_name} {document.approver.last_name}".strip() or document.approver.username
            metadata['APPROVER_EMAIL'] = document.approver.email
        else:
            metadata['APPROVER_NAME'] = 'Not Assigned'
            metadata['APPROVER_EMAIL'] = 'not.assigned@example.com'
        
        # Date information
        metadata['CREATED_DATE'] = document.created_at.strftime('%Y-%m-%d') if document.created_at else 'Unknown'
        metadata['CREATED_DATE_LONG'] = document.created_at.strftime('%B %d, %Y') if document.created_at else 'Unknown'
        metadata['UPDATED_DATE'] = document.updated_at.strftime('%Y-%m-%d') if document.updated_at else 'Unknown'
        
        if document.approval_date:
            metadata['APPROVAL_DATE'] = document.approval_date.strftime('%Y-%m-%d')
            metadata['APPROVAL_DATE_LONG'] = document.approval_date.strftime('%B %d, %Y')
        else:
            metadata['APPROVAL_DATE'] = 'Not Approved'
            metadata['APPROVAL_DATE_LONG'] = 'Not Approved'
            
        if document.effective_date:
            metadata['EFFECTIVE_DATE'] = document.effective_date.strftime('%Y-%m-%d')
            metadata['EFFECTIVE_DATE_LONG'] = document.effective_date.strftime('%B %d, %Y')
        else:
            metadata['EFFECTIVE_DATE'] = 'Not Set'
            metadata['EFFECTIVE_DATE_LONG'] = 'Not Set'
        
        # Current date/time information (for download)
        now = datetime.now()
        today = date.today()
        metadata['DOWNLOAD_DATE'] = today.strftime('%Y-%m-%d')
        metadata['DOWNLOAD_DATE_LONG'] = today.strftime('%B %d, %Y')
        metadata['DOWNLOAD_TIME'] = now.strftime('%H:%M:%S')
        metadata['DOWNLOAD_DATETIME'] = now.strftime('%Y-%m-%d %H:%M:%S')
        metadata['CURRENT_DATE'] = today.strftime('%Y-%m-%d')
        metadata['CURRENT_DATE_LONG'] = today.strftime('%B %d, %Y')
        metadata['CURRENT_TIME'] = now.strftime('%H:%M:%S')
        metadata['CURRENT_DATETIME'] = now.strftime('%Y-%m-%d %H:%M:%S')
        metadata['CURRENT_YEAR'] = str(today.year)
        
        # Status information
        metadata['DOC_STATUS'] = document.status.replace('_', ' ').title()
        metadata['DOC_STATUS_SHORT'] = document.status
        
        # File information
        if document.file_name:
            metadata['FILE_NAME'] = document.file_name
            metadata['FILE_PATH'] = document.file_path or 'Not stored'
            metadata['FILE_SIZE'] = str(document.file_size) if document.file_size else '0'
            metadata['FILE_CHECKSUM'] = document.file_checksum[:16] + '...' if document.file_checksum else 'Not calculated'
        else:
            metadata['FILE_NAME'] = 'No file attached'
            metadata['FILE_PATH'] = 'No file attached'
            metadata['FILE_SIZE'] = '0'
            metadata['FILE_CHECKSUM'] = 'No file attached'
        
        # System information
        metadata['SYSTEM_NAME'] = 'Electronic Document Management System (EDMS)'
        metadata['COMPANY_NAME'] = getattr(settings, 'COMPANY_NAME', 'Your Company')
        
        # Conditional placeholders
        metadata['IF_APPROVED'] = 'APPROVED DOCUMENT' if 'APPROVED' in document.status else ''
        metadata['IF_DRAFT'] = 'DRAFT - NOT FOR USE' if 'DRAFT' in document.status else ''
        metadata['IF_EFFECTIVE'] = 'CURRENT VERSION' if 'EFFECTIVE' in document.status else ''
        
        # Additional technical information
        metadata['IS_CURRENT'] = 'CURRENT' if 'EFFECTIVE' in document.status else 'NOT CURRENT'
        
        return metadata
    
    def generate_annotated_document_content(self, document: Document, user: User = None) -> str:
        """
        Generate annotated document content with metadata overlay
        """
        metadata = self.get_document_metadata(document, user)
        
        # Get available placeholders from database
        available_placeholders = {}
        try:
            for placeholder in PlaceholderDefinition.objects.filter(is_active=True):
                available_placeholders[placeholder.name] = placeholder.description
        except Exception:
            # Fallback if placeholders not available
            available_placeholders = {
                'DOC_NUMBER': 'Document Number',
                'DOC_TITLE': 'Document Title',
                'AUTHOR_NAME': 'Author Name',
                'DOC_STATUS': 'Document Status'
            }
        
        # Create annotation content
        annotation_content = f"""
=== DOCUMENT METADATA ANNOTATION ===
Generated on: {metadata['DOWNLOAD_DATETIME']}
Generated by: {user.username if user else 'System'}
Document UUID: {metadata['DOC_UUID']}

DOCUMENT INFORMATION:
---------------------
{{{{DOC_NUMBER}}}} = {metadata['DOC_NUMBER']}
{{{{DOC_TITLE}}}} = {metadata['DOC_TITLE']}
{{{{DOC_VERSION}}}} = {metadata['DOC_VERSION']}
{{{{DOC_TYPE}}}} = {metadata['DOC_TYPE']}
{{{{DOC_SOURCE}}}} = {metadata['DOC_SOURCE']}
{{{{DOC_STATUS}}}} = {metadata['DOC_STATUS']}
{{{{DOC_DESCRIPTION}}}} = {metadata['DOC_DESCRIPTION']}

PEOPLE INFORMATION:
-------------------
{{{{AUTHOR_NAME}}}} = {metadata['AUTHOR_NAME']}
{{{{AUTHOR_EMAIL}}}} = {metadata['AUTHOR_EMAIL']}
{{{{REVIEWER_NAME}}}} = {metadata['REVIEWER_NAME']}
{{{{REVIEWER_EMAIL}}}} = {metadata['REVIEWER_EMAIL']}
{{{{APPROVER_NAME}}}} = {metadata['APPROVER_NAME']}
{{{{APPROVER_EMAIL}}}} = {metadata['APPROVER_EMAIL']}

DATE INFORMATION:
-----------------
{{{{CREATED_DATE}}}} = {metadata['CREATED_DATE']}
{{{{CREATED_DATE_LONG}}}} = {metadata['CREATED_DATE_LONG']}
{{{{APPROVAL_DATE}}}} = {metadata['APPROVAL_DATE']}
{{{{APPROVAL_DATE_LONG}}}} = {metadata['APPROVAL_DATE_LONG']}
{{{{EFFECTIVE_DATE}}}} = {metadata['EFFECTIVE_DATE']}
{{{{EFFECTIVE_DATE_LONG}}}} = {metadata['EFFECTIVE_DATE_LONG']}
{{{{DOWNLOAD_DATE}}}} = {metadata['DOWNLOAD_DATE']}
{{{{DOWNLOAD_DATETIME}}}} = {metadata['DOWNLOAD_DATETIME']}

FILE INFORMATION:
-----------------
{{{{FILE_NAME}}}} = {metadata['FILE_NAME']}
{{{{FILE_PATH}}}} = {metadata['FILE_PATH']}
{{{{FILE_SIZE}}}} = {metadata['FILE_SIZE']} bytes
{{{{FILE_CHECKSUM}}}} = {metadata['FILE_CHECKSUM']}

SYSTEM INFORMATION:
-------------------
{{{{SYSTEM_NAME}}}} = {metadata['SYSTEM_NAME']}
{{{{COMPANY_NAME}}}} = {metadata['COMPANY_NAME']}
{{{{CURRENT_DATE}}}} = {metadata['CURRENT_DATE']}
{{{{CURRENT_TIME}}}} = {metadata['CURRENT_TIME']}
{{{{CURRENT_YEAR}}}} = {metadata['CURRENT_YEAR']}

STATUS INDICATORS:
------------------
{{{{IS_CURRENT}}}} = {metadata['IS_CURRENT']}
{{{{IF_APPROVED}}}} = {metadata['IF_APPROVED']}
{{{{IF_DRAFT}}}} = {metadata['IF_DRAFT']}
{{{{IF_EFFECTIVE}}}} = {metadata['IF_EFFECTIVE']}

AVAILABLE PLACEHOLDERS:
-----------------------"""

        # Add available placeholders list
        for placeholder_name, description in sorted(available_placeholders.items()):
            value = metadata.get(placeholder_name, 'Not Available')
            annotation_content += f"\n{{{{{placeholder_name}}}}} = {value} ({description})"

        annotation_content += f"""

=== PLACEHOLDER REPLACEMENT EXAMPLE ===

If your original document contains:
"This document {{{{DOC_TITLE}}}} was created by {{{{AUTHOR_NAME}}}} on {{{{CREATED_DATE_LONG}}}}."

It would be replaced with:
"This document {metadata['DOC_TITLE']} was created by {metadata['AUTHOR_NAME']} on {metadata['CREATED_DATE_LONG']}."

=== END METADATA ANNOTATION ===
"""
        return annotation_content
    
    def get_available_placeholders(self) -> Dict[str, str]:
        """
        Get all available placeholders from the database
        """
        placeholders = {}
        try:
            for placeholder in PlaceholderDefinition.objects.filter(is_active=True):
                placeholders[placeholder.name] = placeholder.description
        except Exception:
            # Fallback placeholders if database not available
            placeholders = {
                'DOC_NUMBER': 'Document number',
                'DOC_TITLE': 'Document title',
                'DOC_VERSION': 'Document version',
                'AUTHOR_NAME': 'Author full name',
                'AUTHOR_EMAIL': 'Author email',
                'DOC_STATUS': 'Document status',
                'DOWNLOAD_DATE': 'Download date',
                'COMPANY_NAME': 'Company name'
            }
        return placeholders


# Global instance for easy access
annotation_processor = DocumentAnnotationProcessor()