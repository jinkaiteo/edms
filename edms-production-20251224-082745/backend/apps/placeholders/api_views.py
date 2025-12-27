"""
Placeholder API Views
Provides missing endpoints for placeholder definitions and management.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PlaceholderDefinition


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def placeholder_definitions(request):
    """Get available placeholder definitions."""
    try:
        # Get all placeholder definitions with correct field names
        definitions = PlaceholderDefinition.objects.all().values(
            'id', 'name', 'display_name', 'description', 'placeholder_type', 
            'default_value', 'is_active', 'data_source'
        )
        
        # If no definitions exist, return all actual placeholders from annotation processor
        if not definitions:
            actual_placeholders = [
                # Document Information
                {'id': 1, 'name': 'DOC_NUMBER', 'display_name': 'Document Number', 'description': 'Unique document identifier', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 2, 'name': 'DOC_TITLE', 'display_name': 'Document Title', 'description': 'Document title or name', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 3, 'name': 'DOC_VERSION', 'display_name': 'Document Version', 'description': 'Document version (major.minor)', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 4, 'name': 'DOC_TYPE', 'display_name': 'Document Type', 'description': 'Document type (Policy, SOP, etc.)', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 5, 'name': 'DOC_SOURCE', 'display_name': 'Document Source', 'description': 'Document source type', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 6, 'name': 'DOC_STATUS', 'display_name': 'Document Status', 'description': 'Current document status', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 7, 'name': 'DOC_DESCRIPTION', 'display_name': 'Document Description', 'description': 'Document description or summary', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                
                # User Information
                {'id': 8, 'name': 'AUTHOR_NAME', 'display_name': 'Author Name', 'description': 'Document author full name', 'placeholder_type': 'USER', 'data_source': 'USER_MODEL'},
                {'id': 9, 'name': 'AUTHOR_EMAIL', 'display_name': 'Author Email', 'description': 'Document author email address', 'placeholder_type': 'USER', 'data_source': 'USER_MODEL'},
                {'id': 10, 'name': 'REVIEWER_NAME', 'display_name': 'Reviewer Name', 'description': 'Document reviewer full name', 'placeholder_type': 'USER', 'data_source': 'USER_MODEL'},
                {'id': 11, 'name': 'REVIEWER_EMAIL', 'display_name': 'Reviewer Email', 'description': 'Document reviewer email address', 'placeholder_type': 'USER', 'data_source': 'USER_MODEL'},
                {'id': 12, 'name': 'APPROVER_NAME', 'display_name': 'Approver Name', 'description': 'Document approver full name', 'placeholder_type': 'USER', 'data_source': 'USER_MODEL'},
                {'id': 13, 'name': 'APPROVER_EMAIL', 'display_name': 'Approver Email', 'description': 'Document approver email address', 'placeholder_type': 'USER', 'data_source': 'USER_MODEL'},
                
                # Date Information
                {'id': 14, 'name': 'CREATED_DATE', 'display_name': 'Created Date', 'description': 'Document creation date (YYYY-MM-DD)', 'placeholder_type': 'DATE', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 15, 'name': 'CREATED_DATE_LONG', 'display_name': 'Created Date (Long)', 'description': 'Document creation date (long format)', 'placeholder_type': 'DATE', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 16, 'name': 'APPROVAL_DATE', 'display_name': 'Approval Date', 'description': 'Document approval date (YYYY-MM-DD)', 'placeholder_type': 'DATE', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 17, 'name': 'APPROVAL_DATE_LONG', 'display_name': 'Approval Date (Long)', 'description': 'Document approval date (long format)', 'placeholder_type': 'DATE', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 18, 'name': 'EFFECTIVE_DATE', 'display_name': 'Effective Date', 'description': 'Document effective date (YYYY-MM-DD)', 'placeholder_type': 'DATE', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 19, 'name': 'EFFECTIVE_DATE_LONG', 'display_name': 'Effective Date (Long)', 'description': 'Document effective date (long format)', 'placeholder_type': 'DATE', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 20, 'name': 'DOWNLOAD_DATE', 'display_name': 'Download Date', 'description': 'Current download date (YYYY-MM-DD)', 'placeholder_type': 'DATE', 'data_source': 'COMPUTED'},
                {'id': 21, 'name': 'DOWNLOAD_DATETIME', 'display_name': 'Download DateTime', 'description': 'Current download date and time', 'placeholder_type': 'DATE', 'data_source': 'COMPUTED'},
                
                # File Information
                {'id': 22, 'name': 'FILE_NAME', 'display_name': 'File Name', 'description': 'Original file name', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 23, 'name': 'FILE_PATH', 'display_name': 'File Path', 'description': 'File storage path', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 24, 'name': 'FILE_SIZE', 'display_name': 'File Size', 'description': 'File size in bytes', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                {'id': 25, 'name': 'FILE_CHECKSUM', 'display_name': 'File Checksum', 'description': 'File integrity checksum', 'placeholder_type': 'DOCUMENT', 'data_source': 'DOCUMENT_MODEL'},
                
                # System Information
                {'id': 26, 'name': 'SYSTEM_NAME', 'display_name': 'System Name', 'description': 'EDMS system name', 'placeholder_type': 'SYSTEM', 'data_source': 'SYSTEM_CONFIG'},
                {'id': 27, 'name': 'COMPANY_NAME', 'display_name': 'Company Name', 'description': 'Organization/company name', 'placeholder_type': 'SYSTEM', 'data_source': 'SYSTEM_CONFIG'},
                {'id': 28, 'name': 'CURRENT_DATE', 'display_name': 'Current Date', 'description': 'Current system date', 'placeholder_type': 'DATE', 'data_source': 'COMPUTED'},
                {'id': 29, 'name': 'CURRENT_TIME', 'display_name': 'Current Time', 'description': 'Current system time', 'placeholder_type': 'DATE', 'data_source': 'COMPUTED'},
                {'id': 30, 'name': 'CURRENT_YEAR', 'display_name': 'Current Year', 'description': 'Current year (YYYY)', 'placeholder_type': 'DATE', 'data_source': 'COMPUTED'},
                
                # Conditional Placeholders
                {'id': 31, 'name': 'IS_CURRENT', 'display_name': 'Is Current', 'description': 'Whether document is current version', 'placeholder_type': 'CONDITIONAL', 'data_source': 'COMPUTED'},
                {'id': 32, 'name': 'IF_APPROVED', 'display_name': 'If Approved', 'description': 'Conditional display if document is approved', 'placeholder_type': 'CONDITIONAL', 'data_source': 'COMPUTED'},
                {'id': 33, 'name': 'IF_DRAFT', 'display_name': 'If Draft', 'description': 'Conditional display if document is draft', 'placeholder_type': 'CONDITIONAL', 'data_source': 'COMPUTED'},
                {'id': 34, 'name': 'IF_EFFECTIVE', 'display_name': 'If Effective', 'description': 'Conditional display if document is effective', 'placeholder_type': 'CONDITIONAL', 'data_source': 'COMPUTED'},
            ]
            
            # Add default values and active status
            for placeholder in actual_placeholders:
                placeholder['default_value'] = ''
                placeholder['is_active'] = True
            
            return Response(actual_placeholders)
        
        return Response(list(definitions))
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)