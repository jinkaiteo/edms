"""
Document Annotation Processor
Handles placeholder replacement and metadata annotation for documents
"""

import re
from datetime import datetime, date
from typing import Dict, Any
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import pytz
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
        
        # Extract base document number without version (e.g., PROC-2025-0001 from PROC-2025-0001-v01.00)
        if document.document_number and '-v' in document.document_number:
            metadata['DOC_BASE_NUMBER'] = document.document_number.split('-v')[0]
        else:
            metadata['DOC_BASE_NUMBER'] = document.document_number or 'Not Assigned'
            
        metadata['DOC_TITLE'] = document.title or 'Untitled Document'
        metadata['DOC_VERSION'] = document.version_string or '1.0'
        metadata['DOC_TYPE'] = document.document_type.name if document.document_type else 'Unknown'
        metadata['DOC_SOURCE'] = document.document_source.name if document.document_source else 'Unknown'
        metadata['DOC_DESCRIPTION'] = document.description or 'No description'
        metadata['DOC_UUID'] = str(document.uuid)
        
        # Version-specific placeholders
        metadata['VERSION'] = document.version_string or '1.0'
        metadata['VERSION_MAJOR'] = str(document.version_major) if document.version_major is not None else '1'
        metadata['VERSION_MINOR'] = str(document.version_minor) if document.version_minor is not None else '0'
        metadata['VERSION_FULL'] = document.version_string or '1.0'
        
        # Version history table
        # Create table data - let DOCX processor handle the table creation
        table_data = self._create_version_history_docx_table(document)
        metadata['VERSION_HISTORY_TABLE_DATA'] = table_data
        # Provide placeholder that DOCX processor can detect and replace
        metadata['VERSION_HISTORY'] = "VERSION_HISTORY_CREATE_TABLE"
        
        # Additional document metadata
        metadata['DOCUMENT_SOURCE'] = document.document_source.name if document.document_source else 'Unknown Source'
        metadata['DESCRIPTION'] = document.description or 'No description available'
        metadata['KEYWORDS'] = document.keywords or 'No keywords'
        
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
        metadata['CREATION_DATE'] = document.created_at.strftime('%Y-%m-%d') if document.created_at else 'Unknown'
        metadata['UPDATED_DATE'] = document.updated_at.strftime('%Y-%m-%d') if document.updated_at else 'Unknown'
        metadata['LAST_MODIFIED'] = document.updated_at.strftime('%Y-%m-%d') if document.updated_at else 'Unknown'
        metadata['MODIFIED_DATE'] = document.updated_at.strftime('%Y-%m-%d') if document.updated_at else 'Unknown'
        
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
        
        # Current date/time information (for download) - Using UTC timezone-aware datetime
        now_utc = timezone.now()  # UTC timezone-aware datetime
        today_utc = now_utc.date()    # UTC date
        
        # Get display timezone (Singapore)
        display_tz = pytz.timezone(getattr(settings, 'DISPLAY_TIMEZONE', 'Asia/Singapore'))
        now_local = now_utc.astimezone(display_tz)
        today_local = now_local.date()
        
        # Get timezone abbreviations
        utc_name = 'UTC'
        local_name = now_local.strftime('%Z')  # 'SGT' for Singapore Time
        
        metadata['DOWNLOAD_DATE'] = today_utc.strftime('%Y-%m-%d')
        metadata['DOWNLOAD_DATE_LONG'] = today_utc.strftime('%B %d, %Y')
        metadata['DOWNLOAD_TIME'] = f"{now_utc.strftime('%H:%M:%S')} UTC ({now_local.strftime('%H:%M:%S')} {local_name})"
        metadata['DOWNLOAD_DATETIME'] = f"{now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC ({now_local.strftime('%Y-%m-%d %H:%M:%S')} {local_name})"
        metadata['DOWNLOAD_DATETIME_ISO'] = now_utc.isoformat()  # ISO 8601 format with timezone
        metadata['CURRENT_DATE'] = today_utc.strftime('%Y-%m-%d')
        metadata['CURRENT_DATE_LONG'] = today_utc.strftime('%B %d, %Y')
        metadata['CURRENT_TIME'] = f"{now_utc.strftime('%H:%M:%S')} UTC ({now_local.strftime('%H:%M:%S')} {local_name})"
        metadata['CURRENT_DATETIME'] = f"{now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC ({now_local.strftime('%Y-%m-%d %H:%M:%S')} {local_name})"
        metadata['CURRENT_DATETIME_ISO'] = now_utc.isoformat()  # ISO 8601 format with timezone
        metadata['CURRENT_YEAR'] = str(today_utc.year)
        metadata['TIMEZONE'] = f"{utc_name} / {local_name}"  # Show both timezones
        
        # Status information
        metadata['DOC_STATUS'] = document.status.replace('_', ' ').title()
        metadata['DOC_STATUS_SHORT'] = document.status
        
        # Workflow status information
        try:
            from apps.workflows.models import DocumentWorkflow
            
            # Get active (non-terminated) workflow for this document
            active_workflow = DocumentWorkflow.objects.filter(
                document=document,
                is_terminated=False
            ).first()
            
            if active_workflow and hasattr(active_workflow, 'current_state') and active_workflow.current_state:
                # Get the current workflow state name
                state_name = active_workflow.current_state.name if hasattr(active_workflow.current_state, 'name') else str(active_workflow.current_state)
                metadata['WORKFLOW_STATUS'] = state_name
            else:
                # No active workflow - use document status as fallback
                metadata['WORKFLOW_STATUS'] = metadata['DOC_STATUS']
        except Exception:
            # Fallback to document status if workflow check fails
            metadata['WORKFLOW_STATUS'] = metadata['DOC_STATUS']
        
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
        
        # Common alternative placeholder names for backward compatibility with existing templates
        metadata.update({
            'DOCUMENT_NUMBER': metadata['DOC_NUMBER'],
            'DOCUMENT_TITLE': metadata['DOC_TITLE'],
            'DOCUMENT_STATUS': metadata['DOC_STATUS'],
            'DOCUMENT_VERSION': metadata['DOC_VERSION'],
            'DOCUMENT_TYPE': metadata['DOC_TYPE'],
            'AUTHOR': metadata['AUTHOR_NAME'],
            'REVIEWER': metadata['REVIEWER_NAME'],
            'APPROVER': metadata['APPROVER_NAME'],
            'STATUS': metadata['DOC_STATUS'],
            'VERSION': metadata['DOC_VERSION'],
            'TITLE': metadata['DOC_TITLE'],
            'NUMBER': metadata['DOC_NUMBER'],
            'COMPANY': metadata['COMPANY_NAME'],
            'ORGANIZATION': metadata['COMPANY_NAME'],
        })
        
        return metadata



    def _create_version_history_docx_table(self, document):
        """Create version history data for DOCX table using python-docx-template syntax."""
        try:
            # Get structured data
            from apps.placeholders.services import placeholder_service
            data = placeholder_service._get_version_history_data(document)
            
            if 'error' in data:
                return []
            
            # Return data in format suitable for python-docx-template table creation
            # Template should use: {%tr for row in VERSION_HISTORY_DOCX_TABLE %}
            table_data = []
            for row_data in data['rows']:
                table_data.append({
                    'version': row_data['version'],
                    'date': row_data['date'], 
                    'author': row_data['author'],
                    'status': row_data['status'],
                    'comments': row_data['comments']
                })
            
            return table_data
            
        except Exception as e:
            return []

    def _convert_table_data_to_text(self, table_data):
        """Convert table data back to formatted text for templates using {{VERSION_HISTORY}}."""
        if not table_data:
            return "No version history available"
        
        try:
            # Create formatted table text for DOCX templates that use {{VERSION_HISTORY}}
            lines = []
            lines.append("VERSION HISTORY")
            lines.append("")
            
            # Create table with proper formatting for DOCX
            lines.append("┌─────────┬────────────┬─────────────────┬─────────┬──────────────────────────┐")
            lines.append("│ Version │ Date       │ Author          │ Status  │ Comments                 │")
            lines.append("├─────────┼────────────┼─────────────────┼─────────┼──────────────────────────┤")
            
            for row in table_data:
                version = row['version'][:8].ljust(8)
                date = row['date'][:10].ljust(10)
                author = row['author'][:15].ljust(15)
                status = row['status'][:7].ljust(7)
                comments = row['comments'][:24].ljust(24)
                
                lines.append(f"│ {version} │ {date} │ {author} │ {status} │ {comments} │")
            
            lines.append("└─────────┴────────────┴─────────────────┴─────────┴──────────────────────────┘")
            lines.append("")
            lines.append(f"Generated: {self._get_current_timestamp()}")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error generating version history table: {str(e)}"

    def _get_current_timestamp(self):
        """Get current timestamp in a readable format with both UTC and local timezone."""
        now_utc = timezone.now()  # UTC timezone-aware datetime
        
        # Get display timezone (Singapore)
        display_tz = pytz.timezone(getattr(settings, 'DISPLAY_TIMEZONE', 'Asia/Singapore'))
        now_local = now_utc.astimezone(display_tz)
        local_name = now_local.strftime('%Z')  # 'SGT' for Singapore Time
        
        return f"{now_utc.strftime('%m/%d/%Y %I:%M %p')} UTC ({now_local.strftime('%I:%M %p')} {local_name})"
    
    def _get_version_change_reason(self, document):
        """Extract the reason for change from workflow comments or document description."""
        try:
            from apps.workflows.models import DocumentWorkflow, DocumentTransition
            
            # First, check if there's a specific reason in the document description
            if document.description and any(keyword in document.description.lower() 
                                          for keyword in ['update', 'revision', 'change', 'modify', 'correct']):
                return document.description[:18] + '...' if len(document.description) > 20 else document.description
            
            # Get the initial workflow submission comment
            workflows = DocumentWorkflow.objects.filter(document=document).order_by('created_at')
            
            if workflows.exists():
                first_workflow = workflows.first()
                
                # Get the first transition (submission comment) - try different field names
                try:
                    transitions = DocumentTransition.objects.filter(workflow=first_workflow).order_by('transitioned_at')
                except:
                    try:
                        transitions = DocumentTransition.objects.filter(workflow=first_workflow).order_by('created_at')
                    except:
                        transitions = DocumentTransition.objects.filter(workflow=first_workflow)
                
                if transitions.exists():
                    first_transition = transitions.first()
                    if first_transition.comment and first_transition.comment != 'No comment':
                        comment = first_transition.comment.strip()
                        # Clean up and truncate comment
                        if len(comment) > 18:
                            return comment[:18] + '...'
                        return comment
            
            # Fallback based on version
            if document.version_major == 1 and document.version_minor == 0:
                return "Initial version"
            else:
                return "Version update"
                
        except Exception:
            return "Update"
    
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
        Get all available placeholders - returns RUNTIME placeholders that are actually
        generated by get_document_metadata(), not just database placeholders.
        
        This includes both database-defined placeholders and code-generated aliases
        (e.g., both AUTHOR and AUTHOR_NAME).
        """
        placeholders = {}
        
        # Get sample metadata to see what placeholders are actually generated
        try:
            from .models import Document
            from apps.users.models import User
            
            # Try to get a real document for accurate metadata
            sample_doc = Document.objects.first()
            if sample_doc:
                metadata = self.get_document_metadata(sample_doc)
            else:
                # Create mock document if none exist
                class MockDocument:
                    document_number = "SAMPLE-001"
                    title = "Sample Document"
                    version_major = 1
                    version_minor = 0
                    version_string = "1.0"
                    document_type = type('obj', (object,), {'name': 'Policy'})
                    document_source = type('obj', (object,), {'name': 'Internal'})
                    description = "Sample description"
                    uuid = "00000000-0000-0000-0000-000000000000"
                    author = type('obj', (object,), {'first_name': 'John', 'last_name': 'Doe', 'username': 'jdoe', 'email': 'jdoe@example.com'})
                    reviewer = None
                    approver = None
                    created_at = timezone.now()  # UTC timezone-aware
                    updated_at = timezone.now()  # UTC timezone-aware
                    approval_date = None
                    effective_date = None
                    status = "DRAFT"
                    file_name = "sample.docx"
                    file_path = "/path/to/sample.docx"
                    file_size = 1024
                    file_checksum = "abc123"
                    keywords = "sample, test"
                
                metadata = self.get_document_metadata(MockDocument())
            
            # Use metadata keys as available placeholders
            # Add descriptions from database where available
            db_placeholders = {}
            try:
                for placeholder in PlaceholderDefinition.objects.filter(is_active=True):
                    db_placeholders[placeholder.name] = placeholder.description
            except:
                pass
            
            # Create placeholder list with descriptions
            for key in metadata.keys():
                if key in db_placeholders:
                    # Use database description
                    placeholders[key] = db_placeholders[key]
                else:
                    # Generate description from key name
                    description = key.replace('_', ' ').title()
                    placeholders[key] = description
                    
        except Exception as e:
            # Fallback to database placeholders if runtime extraction fails
            try:
                for placeholder in PlaceholderDefinition.objects.filter(is_active=True):
                    placeholders[placeholder.name] = placeholder.description
            except:
                # Ultimate fallback
                placeholders = {
                    'DOC_NUMBER': 'Document number',
                    'DOC_TITLE': 'Document title',
                    'DOC_VERSION': 'Document version',
                    'AUTHOR_NAME': 'Author full name',
                    'AUTHOR_EMAIL': 'Author email',
                    'REVIEWER_NAME': 'Reviewer full name',
                    'APPROVER_NAME': 'Approver full name',
                    'DOC_STATUS': 'Document status',
                    'DOWNLOAD_DATE': 'Download date',
                    'COMPANY_NAME': 'Company name'
                }
        
        return placeholders


# Global instance for easy access
annotation_processor = DocumentAnnotationProcessor()