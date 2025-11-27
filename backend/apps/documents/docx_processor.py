"""
DOCX Document Processing with Placeholder Replacement
Handles .docx template processing using python-docx-template
"""

import os
import tempfile
from typing import Dict, Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Document
from .annotation_processor import annotation_processor

User = get_user_model()

try:
    from docxtpl import DocxTemplate
    DOCX_TEMPLATE_AVAILABLE = True
except ImportError:
    DOCX_TEMPLATE_AVAILABLE = False
    DocxTemplate = None


class DocxTemplateProcessor:
    """
    Service class for processing .docx templates with placeholder replacement
    """
    
    def __init__(self):
        self.template_available = DOCX_TEMPLATE_AVAILABLE
        
    def is_available(self) -> bool:
        """Check if docx template processing is available"""
        return self.template_available
    
    def process_docx_template(self, document: Document, user: User = None) -> Optional[str]:
        """
        Process .docx file and replace placeholders with actual document metadata
        Returns path to processed file or None if processing fails
        """
        if not self.template_available:
            raise ImportError("python-docx-template is not installed. Run: pip install python-docx-template")
        
        if not document.file_path or not document.full_file_path:
            raise ValueError("Document has no attached file")
        
        if not os.path.exists(document.full_file_path):
            raise FileNotFoundError(f"Document file not found: {document.full_file_path}")
        
        # Check if file is a .docx file
        if not document.file_name.lower().endswith('.docx'):
            raise ValueError("File is not a .docx document")
        
        try:
            # Load the template
            doc_template = DocxTemplate(document.full_file_path)
            
            # Get metadata for placeholder replacement
            metadata = annotation_processor.get_document_metadata(document, user)
            
            # Add some additional formatting options
            context = self._prepare_template_context(metadata, document, user)
            
            # Render the template
            doc_template.render(context)
            
            # Create temporary file for the processed document
            processed_file = tempfile.NamedTemporaryFile(
                mode='wb',
                suffix='_processed.docx',
                delete=False
            )
            
            # Save the processed document
            doc_template.save(processed_file.name)
            processed_file.close()
            
            return processed_file.name
            
        except Exception as e:
            raise RuntimeError(f"Failed to process .docx template: {str(e)}")
    
    def _prepare_template_context(self, metadata: Dict[str, Any], document: Document, user: User = None) -> Dict[str, Any]:
        """
        Prepare template context with additional formatting and helper functions
        """
        context = metadata.copy()
        
        # Add document object for complex operations
        context['document'] = document
        context['user'] = user
        
        # Add formatting helpers
        context['today'] = metadata['CURRENT_DATE']
        context['now'] = metadata['CURRENT_DATETIME']
        
        # Add conditional helpers
        context['is_approved'] = 'APPROVED' in document.status
        context['is_draft'] = 'DRAFT' in document.status
        context['is_effective'] = 'EFFECTIVE' in document.status
        context['is_under_review'] = 'REVIEW' in document.status
        
        # Add workflow status helpers
        context['has_reviewer'] = document.reviewer is not None
        context['has_approver'] = document.approver is not None
        context['has_effective_date'] = document.effective_date is not None
        context['has_approval_date'] = document.approval_date is not None
        
        # Add file information helpers
        context['has_file'] = bool(document.file_name)
        context['file_extension'] = os.path.splitext(document.file_name)[1] if document.file_name else ''
        
        # Add user information if available
        if user:
            context['current_user_name'] = f"{user.first_name} {user.last_name}".strip() or user.username
            context['current_user_email'] = user.email
        
        # Add company/system information
        context['system_name'] = 'Electronic Document Management System (EDMS)'
        context['generated_by_system'] = True
        
        # Add common alternative placeholder names that might be in templates
        context.update({
            'DOCUMENT_TITLE': metadata.get('DOC_TITLE', 'Unknown'),
            'DOCUMENT_NUMBER': metadata.get('DOC_NUMBER', 'Unknown'),
            'DOCUMENT_STATUS': metadata.get('DOC_STATUS', 'Unknown'),
            'DOCUMENT_VERSION': metadata.get('DOC_VERSION', 'Unknown'),
            'AUTHOR': metadata.get('AUTHOR_NAME', 'Unknown'),
            'REVIEWER': metadata.get('REVIEWER_NAME', 'Unknown'),
            'APPROVER': metadata.get('APPROVER_NAME', 'Unknown'),
            'STATUS': metadata.get('DOC_STATUS', 'Unknown'),
            'VERSION': metadata.get('DOC_VERSION', 'Unknown'),
            'TITLE': metadata.get('DOC_TITLE', 'Unknown'),
            'NUMBER': metadata.get('DOC_NUMBER', 'Unknown'),
            'COMPANY': metadata.get('COMPANY_NAME', 'Your Company'),
            'ORGANIZATION': metadata.get('COMPANY_NAME', 'Your Company'),
            'DATE': metadata.get('CURRENT_DATE', ''),
            'TIME': metadata.get('CURRENT_TIME', ''),
            'DATETIME': metadata.get('CURRENT_DATETIME', ''),
            'CREATED': metadata.get('CREATED_DATE', ''),
            'MODIFIED': metadata.get('UPDATED_DATE', ''),
            'APPROVED': metadata.get('APPROVAL_DATE', ''),
            'EFFECTIVE': metadata.get('EFFECTIVE_DATE', ''),
        })
        
        return context
    
    def get_template_variables(self, document: Document) -> Dict[str, str]:
        """
        Extract template variables from a .docx file (if possible)
        This would scan the document for {{ }} patterns
        """
        if not self.template_available:
            return {}
        
        if not document.file_path or not os.path.exists(document.full_file_path):
            return {}
        
        try:
            # This is a simplified approach - full implementation would parse XML
            import re
            from docx import Document as DocxDocument
            
            doc = DocxDocument(document.full_file_path)
            variables = set()
            
            # Search for {{ }} patterns in paragraphs
            for paragraph in doc.paragraphs:
                matches = re.findall(r'\{\{([A-Z_]+)\}\}', paragraph.text)
                variables.update(matches)
            
            # Search in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        matches = re.findall(r'\{\{([A-Z_]+)\}\}', cell.text)
                        variables.update(matches)
            
            # Return as dictionary with descriptions
            result = {}
            metadata = annotation_processor.get_document_metadata(document)
            available_placeholders = annotation_processor.get_available_placeholders()
            
            for var in variables:
                if var in available_placeholders:
                    result[var] = available_placeholders[var]
                elif var in metadata:
                    result[var] = f"Document metadata: {var}"
                else:
                    result[var] = f"Unknown placeholder: {var}"
            
            return result
            
        except Exception as e:
            print(f"Error extracting template variables: {e}")
            return {}
    
    def validate_docx_template(self, document: Document) -> Dict[str, Any]:
        """
        Validate a .docx template and return information about placeholders found
        """
        validation_result = {
            'is_valid': False,
            'is_docx': False,
            'has_placeholders': False,
            'placeholders_found': [],
            'placeholders_available': [],
            'placeholders_missing': [],
            'errors': []
        }
        
        try:
            if not document.file_name:
                validation_result['errors'].append('No file attached to document')
                return validation_result
            
            if not document.file_name.lower().endswith('.docx'):
                validation_result['errors'].append('File is not a .docx document')
                return validation_result
                
            validation_result['is_docx'] = True
            
            if not document.file_path or not os.path.exists(document.full_file_path):
                validation_result['errors'].append('Document file not found on disk')
                return validation_result
            
            # Extract template variables
            template_vars = self.get_template_variables(document)
            available_placeholders = annotation_processor.get_available_placeholders()
            
            validation_result['placeholders_found'] = list(template_vars.keys())
            validation_result['placeholders_available'] = list(available_placeholders.keys())
            validation_result['has_placeholders'] = len(template_vars) > 0
            
            # Find missing placeholders
            missing = [var for var in template_vars.keys() if var not in available_placeholders]
            validation_result['placeholders_missing'] = missing
            
            if missing:
                validation_result['errors'].append(f'Unknown placeholders found: {", ".join(missing)}')
            
            validation_result['is_valid'] = (
                validation_result['is_docx'] and 
                len(validation_result['errors']) == 0
            )
            
        except Exception as e:
            validation_result['errors'].append(f'Validation error: {str(e)}')
        
        return validation_result


# Global instance for easy access
docx_processor = DocxTemplateProcessor()