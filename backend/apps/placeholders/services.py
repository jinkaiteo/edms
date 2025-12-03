"""
Placeholder Services for EDMS S6 Module.

Comprehensive services for template processing, placeholder replacement,
and document generation with python-docx-template integration.
"""

import os
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.cache import cache

from docx import Document as DocxDocument
from docxtpl import DocxTemplate

# Optional imports - not required for basic placeholder functionality
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

from .models import (
    PlaceholderDefinition, DocumentTemplate, TemplatePlaceholder,
    DocumentGeneration, PlaceholderCache
)
from apps.documents.models import Document
from apps.audit.services import audit_service

User = get_user_model()
logger = logging.getLogger(__name__)


class PlaceholderService:
    """
    Core service for placeholder management and replacement.
    
    Handles placeholder value resolution, caching, and validation
    for document template processing.
    """

    def __init__(self):
        self.cache_prefix = 'placeholder_'
        self.default_cache_timeout = 300  # 5 minutes

    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> str:
        """
        Get the value for a placeholder from context data.
        
        Args:
            placeholder_name: Name of the placeholder
            context: Context data containing document, user, workflow info
            
        Returns:
            Resolved placeholder value
        """
        try:
            placeholder = PlaceholderDefinition.objects.get(
                name=placeholder_name.upper(),
                is_active=True
            )
        except PlaceholderDefinition.DoesNotExist:
            logger.warning(f"Placeholder not found: {placeholder_name}")
            return f"[{placeholder_name}_NOT_FOUND]"

        # Check cache first
        if placeholder.cache_duration > 0:
            cache_key = self._generate_cache_key(placeholder, context)
            cached_value = self._get_cached_value(cache_key)
            if cached_value is not None:
                return cached_value

        # Resolve placeholder value
        try:
            value = self._resolve_placeholder_value(placeholder, context)
            formatted_value = self._format_placeholder_value(placeholder, value)
            
            # Cache the result if caching is enabled
            if placeholder.cache_duration > 0:
                self._cache_placeholder_value(cache_key, formatted_value, placeholder.cache_duration)
            
            return formatted_value
            
        except Exception as e:
            logger.error(f"Error resolving placeholder {placeholder_name}: {str(e)}")
            return placeholder.default_value or f"[{placeholder_name}_ERROR]"

    def resolve_all_placeholders(self, template: DocumentTemplate, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Resolve all placeholders for a template.
        
        Args:
            template: Document template
            context: Context data
            
        Returns:
            Dictionary of placeholder names to resolved values
        """
        resolved_placeholders = {}
        
        for template_placeholder in template.template_placeholders.all():
            placeholder = template_placeholder.placeholder
            
            # Check permissions
            if placeholder.requires_permission:
                user = context.get('user')
                if not self._check_placeholder_permission(user, placeholder):
                    continue
            
            # Use template-specific default if available
            template_context = context.copy()
            if template_placeholder.default_value:
                template_context['template_default'] = template_placeholder.default_value
            
            value = self.get_placeholder_value(placeholder.name, template_context)
            resolved_placeholders[placeholder.name] = value
            
        return resolved_placeholders

    def _resolve_placeholder_value(self, placeholder: PlaceholderDefinition, context: Dict[str, Any]) -> Any:
        """Resolve the raw value for a placeholder based on its data source."""
        
        if placeholder.data_source == 'DOCUMENT_MODEL':
            return self._resolve_document_field(placeholder.source_field, context)
        
        elif placeholder.data_source == 'USER_MODEL':
            return self._resolve_user_field(placeholder.source_field, context)
        
        elif placeholder.data_source == 'WORKFLOW_MODEL':
            return self._resolve_workflow_field(placeholder.source_field, context)
        
        elif placeholder.data_source == 'SYSTEM_CONFIG':
            return self._resolve_system_config(placeholder.source_field, context)
        
        elif placeholder.data_source == 'COMPUTED':
            return self._resolve_computed_value(placeholder.source_field, context)
        
        elif placeholder.data_source == 'JSONB_FIELD':
            return self._resolve_jsonb_field(placeholder.source_field, context)
        
        else:
            return placeholder.default_value

    def _resolve_document_field(self, field_name: str, context: Dict[str, Any]) -> Any:
        """Resolve document model field value."""
        document = context.get('document')
        if not document:
            return None
            
        # Handle nested field access (e.g., 'document_type.name')
        field_parts = field_name.split('.')
        value = document
        
        for part in field_parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
                
        return value

    def _resolve_user_field(self, field_name: str, context: Dict[str, Any]) -> Any:
        """Resolve user model field value."""
        # Try different user contexts
        for user_key in ['user', 'author', 'reviewer', 'approver']:
            user = context.get(user_key)
            if user and hasattr(user, field_name):
                return getattr(user, field_name)
        return None

    def _resolve_workflow_field(self, field_name: str, context: Dict[str, Any]) -> Any:
        """Resolve workflow model field value."""
        workflow = context.get('workflow')
        if workflow and hasattr(workflow, field_name):
            return getattr(workflow, field_name)
        return None

    def _resolve_system_config(self, config_key: str, context: Dict[str, Any]) -> Any:
        """Resolve system configuration value."""
        # Handle special system values
        if config_key == 'CURRENT_DATE':
            return timezone.now().date()
        elif config_key == 'CURRENT_TIME':
            return timezone.now().time()
        elif config_key == 'CURRENT_DATETIME':
            return timezone.now()
        elif config_key == 'CURRENT_YEAR':
            return timezone.now().year
        
        # Get from Django settings
        return getattr(settings, config_key, None)

    def _resolve_computed_value(self, computation: str, context: Dict[str, Any]) -> Any:
        """Resolve computed value using predefined computations."""
        computations = {
            'DEPENDENCY_COUNT': lambda ctx: len(ctx.get('document', {}).dependencies.all()) if ctx.get('document') else 0,
            'REVISION_COUNT': lambda ctx: self._get_revision_count(ctx.get('document')),
            'IS_CURRENT': lambda ctx: 'CURRENT' if ctx.get('document', {}).status == 'effective' else 'SUPERSEDED',
            'FILE_CHECKSUM': lambda ctx: ctx.get('document', {}).file_checksum if ctx.get('document') else '',
            'VERSION_HISTORY': lambda ctx: self._get_version_history_docx_table(ctx.get('document')),
            'PREVIOUS_VERSION': lambda ctx: self._get_previous_version(ctx.get('document')),
        }
        
        if computation in computations:
            return computations[computation](context)
        
        return None

    def _resolve_jsonb_field(self, field_path: str, context: Dict[str, Any]) -> Any:
        """Resolve JSONB metadata field value."""
        document = context.get('document')
        if not document or not hasattr(document, 'metadata'):
            return None
            
        # Navigate through JSON path (e.g., 'custom_fields.department')
        field_parts = field_path.split('.')
        value = document.metadata
        
        for part in field_parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
                
        return value

    def _format_placeholder_value(self, placeholder: PlaceholderDefinition, value: Any) -> str:
        """Format placeholder value according to its configuration."""
        if value is None:
            return placeholder.default_value or ''
        
        # Date formatting
        if placeholder.placeholder_type == 'DATE' and hasattr(value, 'strftime'):
            return value.strftime(placeholder.date_format)
        
        # Custom format string
        if placeholder.format_string:
            try:
                return placeholder.format_string.format(value)
            except (ValueError, TypeError):
                logger.warning(f"Format error for placeholder {placeholder.name}: {placeholder.format_string}")
        
        # Default string conversion
        return str(value)

    def _generate_cache_key(self, placeholder: PlaceholderDefinition, context: Dict[str, Any]) -> str:
        """Generate cache key for placeholder value."""
        # Create a hash of the relevant context
        context_str = json.dumps({
            'placeholder_id': str(placeholder.uuid),
            'document_id': context.get('document', {}).id if context.get('document') else None,
            'user_id': context.get('user', {}).id if context.get('user') else None,
            'timestamp': timezone.now().isoformat()[:10],  # Date only
        }, sort_keys=True)
        
        context_hash = hashlib.md5(context_str.encode()).hexdigest()
        return f"{self.cache_prefix}{placeholder.name}_{context_hash}"

    def _get_cached_value(self, cache_key: str) -> Optional[str]:
        """Get cached placeholder value."""
        return cache.get(cache_key)

    def _cache_placeholder_value(self, cache_key: str, value: str, duration: int):
        """Cache placeholder value."""
        cache.set(cache_key, value, duration)

    def _check_placeholder_permission(self, user: User, placeholder: PlaceholderDefinition) -> bool:
        """Check if user has permission to access placeholder value."""
        if not placeholder.requires_permission:
            return True
        
        if not user or not user.is_authenticated:
            return False
        
        # Check user roles for required permission
        from apps.users.workflow_permissions import workflow_permission_manager
        return workflow_permission_manager._has_permission_level(
            user, [placeholder.requires_permission]
        )

    def _get_revision_count(self, document) -> int:
        """Get the number of revisions for a document."""
        if not document:
            return 0
        
        try:
            # Get the base document number (without version suffix)
            if hasattr(document, 'document_number') and document.document_number:
                if '-v' in document.document_number:
                    base_number = document.document_number.split('-v')[0]
                else:
                    base_number = document.document_number
                
                # Find all versions of this document
                from apps.documents.models import Document
                all_versions = Document.objects.filter(
                    document_number__startswith=base_number + '-v'
                )
                return all_versions.count()
            return 1
        except Exception as e:
            logger.error(f"Error getting revision count: {str(e)}")
            return 0

    def _get_version_history_docx_table(self, document):
        """Get version history as structured data for native DOCX tables."""
        if not document:
            return []
        
        try:
            # Get structured data
            data = self._get_version_history_data(document)
            
            if 'error' in data:
                return []
            
            # Return data in format suitable for python-docx-template table creation
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
            logger.error(f"Error generating DOCX version history table: {str(e)}")
            return []

    def _get_version_history_data(self, document):
        """Get version history as structured data for native DOCX table rendering."""
        if not document:
            return {"error": "No document provided"}
        
        try:
            # Import here to avoid circular imports
            from apps.documents.models import Document
            
            # Get the base document number (without version suffix)
            if '-v' in document.document_number:
                base_number = document.document_number.split('-v')[0]
            else:
                base_number = document.document_number
            
            # Find all versions of this document
            all_versions = Document.objects.filter(
                document_number__startswith=base_number + '-v'
            ).order_by('version_major', 'version_minor')
            
            if not all_versions.exists():
                return {"error": "No version history available"}
            
            # Return structured data for DOCX table rendering
            version_data = []
            for version_doc in all_versions:
                version = f"v{version_doc.version_major:02d}.{version_doc.version_minor:02d}"
                date = version_doc.created_at.strftime('%m/%d/%Y') if version_doc.created_at else 'Unknown'
                
                # Get author name
                if version_doc.author:
                    author_name = version_doc.author.get_full_name().strip()
                    if not author_name:
                        author_name = version_doc.author.username
                else:
                    author_name = 'Unknown'
                
                status = version_doc.status.replace('_', ' ').title() if version_doc.status else 'Draft'
                
                # Get reason for change
                reason = self._get_version_change_reason(version_doc)
                
                version_data.append({
                    'version': version,
                    'date': date,
                    'author': author_name,
                    'status': status,
                    'comments': reason
                })
            
            return {
                'title': 'VERSION HISTORY',
                'headers': ['Version', 'Date', 'Author', 'Status', 'Comments'],
                'rows': version_data,
                'generated': timezone.now().strftime('%m/%d/%Y %I:%M %p'),
                'count': len(version_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating version history data: {str(e)}")
            return {"error": f"Error generating version history: {str(e)}"}


    def _get_previous_version(self, document) -> str:
        """Get the previous version number."""
        if not document:
            return "N/A"
        
        try:
            # Get the base document number (without version suffix)
            if hasattr(document, 'document_number') and document.document_number:
                if '-v' in document.document_number:
                    base_number = document.document_number.split('-v')[0]
                else:
                    base_number = document.document_number
                
                # Find all versions of this document ordered by version
                from apps.documents.models import Document
                all_versions = Document.objects.filter(
                    document_number__startswith=base_number + '-v'
                ).order_by('version_major', 'version_minor')
                
                # Find current document position and get previous
                current_index = None
                for i, version_doc in enumerate(all_versions):
                    if version_doc.id == document.id:
                        current_index = i
                        break
                
                if current_index and current_index > 0:
                    previous_doc = all_versions[current_index - 1]
                    return previous_doc.version_string or f"{previous_doc.version_major}.{previous_doc.version_minor}"
                else:
                    return "N/A (First version)"
            
            return "N/A"
        except Exception as e:
            logger.error(f"Error getting previous version: {str(e)}")
            return "Error"

    def _get_version_change_reason(self, document):
        """Extract the reason for change from appropriate workflow fields."""
        try:
            # For initial version (v1.0), always return "Initial creation"
            if document.version_major == 1 and document.version_minor == 0:
                return "Initial creation"
            
            # For subsequent versions, check specific workflow fields first
            
            # 1. Check for up-versioning reason (reason_for_change field)
            if hasattr(document, 'reason_for_change') and document.reason_for_change:
                reason = document.reason_for_change.strip()
                if reason:
                    return reason[:50] + '...' if len(reason) > 50 else reason
            
            # 2. Check for obsolescence reason (if document is obsolete)
            if document.status == 'OBSOLETE':
                if hasattr(document, 'obsolescence_reason') and document.obsolescence_reason:
                    reason = document.obsolescence_reason.strip()
                    if reason:
                        return reason[:50] + '...' if len(reason) > 50 else reason
            
            # 3. Check document description for version changes
            if document.description and any(keyword in document.description.lower() 
                                          for keyword in ['update', 'revision', 'change', 'modify', 'correct']):
                desc = document.description.strip()
                return desc[:50] + '...' if len(desc) > 50 else desc
            
            # 4. Fallback to workflow submission comments
            from apps.workflows.models import DocumentWorkflow, DocumentTransition
            
            workflows = DocumentWorkflow.objects.filter(document=document).order_by('created_at')
            
            if workflows.exists():
                first_workflow = workflows.first()
                
                # Get the first transition (submission comment)
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
                        return comment[:50] + '...' if len(comment) > 50 else comment
            
            # Final fallback for subsequent versions
            return "Version update"
                
        except Exception:
            # Ultimate fallback - check version to provide appropriate default
            try:
                if document.version_major == 1 and document.version_minor == 0:
                    return "Initial creation"
                else:
                    return "Document change"
            except:
                return "Version change"


class DocumentTemplateService:
    """
    Service for document template management and processing.
    
    Handles template operations, document generation from templates,
    and integration with various document formats.
    """

    def __init__(self):
        self.placeholder_service = PlaceholderService()
        self.supported_formats = ['docx', 'pdf', 'html', 'txt']

    def generate_document(self, template: DocumentTemplate, context: Dict[str, Any],
                         output_format: str = None, options: Dict[str, Any] = None) -> DocumentGeneration:
        """
        Generate a document from a template.
        
        Args:
            template: Document template to use
            context: Context data for placeholder replacement
            output_format: Output format (defaults to template's format)
            options: Additional generation options
            
        Returns:
            DocumentGeneration instance tracking the generation process
        """
        user = context.get('user')
        if not user:
            raise ValueError("User context is required for document generation")

        # Create generation record
        generation = DocumentGeneration.objects.create(
            template=template,
            source_document=context.get('document'),
            output_format=output_format or template.template_type,
            context_data=self._sanitize_context_for_storage(context),
            generation_options=options or {},
            requested_by=user
        )

        try:
            # Mark as processing
            generation.mark_processing()
            
            # Resolve placeholders
            resolved_placeholders = self.placeholder_service.resolve_all_placeholders(template, context)
            
            # Generate document based on template type
            if template.template_type == 'DOCX':
                output_path = self._generate_docx_document(template, resolved_placeholders, generation)
            elif template.template_type == 'PDF':
                output_path = self._generate_pdf_document(template, resolved_placeholders, generation)
            elif template.template_type == 'HTML':
                output_path = self._generate_html_document(template, resolved_placeholders, generation)
            elif template.template_type == 'TEXT':
                output_path = self._generate_text_document(template, resolved_placeholders, generation)
            else:
                raise ValueError(f"Unsupported template type: {template.template_type}")
            
            # Calculate file details
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            file_checksum = self._calculate_file_checksum(output_path)
            
            # Mark as completed
            generation.mark_completed(output_path, file_size, file_checksum)
            
            # Update template usage
            template.increment_usage()
            
            # Log audit trail
            audit_service.log_user_action(
                user=user,
                action='DOCUMENT_GENERATED',
                object_type='DocumentTemplate',
                object_id=template.id,
                description=f"Generated document from template {template.name}",
                additional_data={
                    'template_name': template.name,
                    'output_format': generation.output_format,
                    'file_size': file_size,
                    'generation_id': str(generation.uuid)
                }
            )
            
            return generation
            
        except Exception as e:
            # Mark as failed
            generation.mark_failed(str(e))
            
            # Log error
            audit_service.log_system_event(
                event_type='DOCUMENT_GENERATION_FAILED',
                object_type='DocumentTemplate',
                object_id=template.id,
                description=f"Document generation failed: {str(e)}",
                additional_data={
                    'template_name': template.name,
                    'generation_id': str(generation.uuid),
                    'error': str(e)
                }
            )
            
            raise

    def _generate_docx_document(self, template: DocumentTemplate, placeholders: Dict[str, str],
                               generation: DocumentGeneration) -> str:
        """Generate Word document using python-docx-template."""
        template_path = template.file_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Load template
        doc_template = DocxTemplate(template_path)
        
        # Render with placeholders
        doc_template.render(placeholders)
        
        # Generate output filename
        output_filename = template.get_output_filename(placeholders)
        if not output_filename.endswith('.docx'):
            output_filename += '.docx'
        
        # Save to output directory
        output_dir = self._get_output_directory(generation)
        output_path = os.path.join(output_dir, output_filename)
        
        os.makedirs(output_dir, exist_ok=True)
        doc_template.save(output_path)
        
        generation.output_filename = output_filename
        generation.save(update_fields=['output_filename'])
        
        return output_path

    def _generate_pdf_document(self, template: DocumentTemplate, placeholders: Dict[str, str],
                              generation: DocumentGeneration) -> str:
        """Generate PDF document."""
        # For PDF, we typically generate from a DOCX template first, then convert
        if template.template_type == 'DOCX':
            # Generate DOCX first
            docx_path = self._generate_docx_document(template, placeholders, generation)
            
            # Convert to PDF (requires additional libraries like python-docx2pdf)
            # For now, we'll just return the DOCX path
            # TODO: Implement PDF conversion
            return docx_path
        
        # For native PDF templates, use different approach
        raise NotImplementedError("Native PDF template processing not implemented yet")

    def _generate_html_document(self, template: DocumentTemplate, placeholders: Dict[str, str],
                               generation: DocumentGeneration) -> str:
        """Generate HTML document."""
        template_path = template.file_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Read template content
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Simple placeholder replacement for HTML
        for placeholder_name, value in placeholders.items():
            template_content = template_content.replace(f"{{{{{placeholder_name}}}}}", str(value))
        
        # Generate output filename
        output_filename = template.get_output_filename(placeholders)
        if not output_filename.endswith('.html'):
            output_filename += '.html'
        
        # Save to output directory
        output_dir = self._get_output_directory(generation)
        output_path = os.path.join(output_dir, output_filename)
        
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        generation.output_filename = output_filename
        generation.save(update_fields=['output_filename'])
        
        return output_path

    def _generate_text_document(self, template: DocumentTemplate, placeholders: Dict[str, str],
                               generation: DocumentGeneration) -> str:
        """Generate text document."""
        template_path = template.file_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Read template content
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Simple placeholder replacement
        for placeholder_name, value in placeholders.items():
            template_content = template_content.replace(f"{{{{{placeholder_name}}}}}", str(value))
        
        # Generate output filename
        output_filename = template.get_output_filename(placeholders)
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'
        
        # Save to output directory
        output_dir = self._get_output_directory(generation)
        output_path = os.path.join(output_dir, output_filename)
        
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        generation.output_filename = output_filename
        generation.save(update_fields=['output_filename'])
        
        return output_path

    def _get_output_directory(self, generation: DocumentGeneration) -> str:
        """Get output directory for generated documents."""
        base_dir = getattr(settings, 'GENERATED_DOCUMENTS_ROOT', '/tmp/edms_generated')
        date_dir = generation.created_at.strftime('%Y/%m/%d')
        return os.path.join(base_dir, date_dir, str(generation.uuid))

    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        if not os.path.exists(file_path):
            return ''
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _sanitize_context_for_storage(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize context data for JSON storage."""
        sanitized = {}
        
        for key, value in context.items():
            if key in ['document', 'user', 'workflow']:
                # Store only IDs for model instances
                if hasattr(value, 'id'):
                    sanitized[f"{key}_id"] = value.id
            elif isinstance(value, (str, int, float, bool, list, dict)):
                sanitized[key] = value
            else:
                # Convert to string for other types
                sanitized[key] = str(value)
        
        return sanitized


class OCRService:
    """
    OCR Service for document text extraction.
    
    Integrates with Tesseract for optical character recognition
    of scanned documents and images.
    """

    def __init__(self):
        self.supported_formats = ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif']

    def extract_text_from_image(self, image_path: str, language: str = 'eng') -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            language: OCR language (default: English)
            
        Returns:
            Extracted text
        """
        try:
            # Open and process image
            image = Image.open(image_path)
            
            # Perform OCR
            extracted_text = pytesseract.image_to_string(image, lang=language)
            
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
            return ""

    def extract_text_from_pdf_images(self, pdf_path: str, language: str = 'eng') -> List[str]:
        """
        Extract text from PDF by converting pages to images and running OCR.
        
        Args:
            pdf_path: Path to PDF file
            language: OCR language
            
        Returns:
            List of extracted text for each page
        """
        extracted_texts = []
        
        try:
            # This would require additional libraries like pdf2image
            # For now, return empty list
            logger.info(f"OCR extraction for PDF not implemented: {pdf_path}")
            return []
            
        except Exception as e:
            logger.error(f"PDF OCR extraction failed for {pdf_path}: {str(e)}")
            return []


# Global service instances
placeholder_service = PlaceholderService()
template_service = DocumentTemplateService()
ocr_service = OCRService()