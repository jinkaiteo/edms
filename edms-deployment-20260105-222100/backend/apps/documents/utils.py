"""
Utility functions for Document Management (O1).

Provides helper functions for document operations, file handling,
access logging, and export functionality.
"""

import json
import csv
import os
import hashlib
from datetime import datetime
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import DocumentAccessLog


def log_document_access(document, user, access_type, request=None, success=True, 
                       failure_reason='', file_downloaded=False, metadata=None):
    """
    Log document access for audit trail and compliance.
    
    Args:
        document: Document instance
        user: User who accessed the document
        access_type: Type of access (VIEW, DOWNLOAD, EDIT, etc.)
        request: Django request object (optional)
        success: Whether the access was successful
        failure_reason: Reason for failure if not successful
        file_downloaded: Whether a file was downloaded
        metadata: Additional metadata dict
    
    Returns:
        DocumentAccessLog instance
    """
    # Extract request information if available
    ip_address = None
    user_agent = ''
    session_id = ''
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        session_id = request.session.session_key if hasattr(request, 'session') else ''
    
    # Create access log entry
    access_log = DocumentAccessLog.objects.create(
        document=document,
        user=user,
        access_type=access_type,
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id,
        success=success,
        failure_reason=failure_reason,
        document_version=document.version_string,
        file_downloaded=file_downloaded,
        metadata=metadata or {}
    )
    
    return access_log


def calculate_file_checksum(file_path):
    """
    Calculate SHA-256 checksum for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA-256 checksum as hex string, or empty string if error
    """
    if not file_path or not os.path.exists(file_path):
        return ''
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception:
        return ''


def verify_file_integrity(file_path, expected_checksum):
    """
    Verify file integrity using checksum comparison.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA-256 checksum
        
    Returns:
        True if checksums match, False otherwise
    """
    if not expected_checksum:
        return False
    
    current_checksum = calculate_file_checksum(file_path)
    return current_checksum == expected_checksum


def get_file_mime_type(file_path):
    """
    Get MIME type for a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string
    """
    import mimetypes
    
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'


def create_document_export(document, export_format='json', include_content=False):
    """
    Create document export in specified format.
    
    Args:
        document: Document instance to export
        export_format: Export format ('json', 'csv', 'xml')
        include_content: Whether to include file content
        
    Returns:
        Exported data as string or dict
    """
    # Prepare base document data
    export_data = {
        'document_number': document.document_number,
        'title': document.title,
        'description': document.description,
        'version': document.version_string,
        'status': document.status,
        'document_type': document.document_type.name if document.document_type else '',
        'document_source': document.document_source.name if document.document_source else '',
        'author': document.author.get_full_name() if document.author else '',
        'reviewer': document.reviewer.get_full_name() if document.reviewer else '',
        'approver': document.approver.get_full_name() if document.approver else '',
        'created_at': document.created_at.isoformat(),
        'updated_at': document.updated_at.isoformat(),
        'effective_date': document.effective_date.isoformat() if document.effective_date else '',
        'file_name': document.file_name,
        'file_size': document.file_size,
        'file_checksum': document.file_checksum,
        'keywords': document.keywords,
        'is_controlled': document.is_controlled,
        'requires_training': document.requires_training,
    }
    
    # Add dependencies
    export_data['dependencies'] = [
        {
            'depends_on': dep.depends_on.document_number,
            'dependency_type': dep.dependency_type,
            'is_critical': dep.is_critical
        }
        for dep in document.dependencies.filter(is_active=True)
    ]
    
    # Add comments
    export_data['comments'] = [
        {
            'author': comment.author.get_full_name(),
            'comment_type': comment.comment_type,
            'subject': comment.subject,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'is_resolved': comment.is_resolved
        }
        for comment in document.comments.all()
    ]
    
    # Add attachments
    export_data['attachments'] = [
        {
            'name': att.name,
            'attachment_type': att.attachment_type,
            'file_name': att.file_name,
            'file_size': att.file_size,
            'uploaded_at': att.uploaded_at.isoformat(),
            'uploaded_by': att.uploaded_by.get_full_name()
        }
        for att in document.attachments.filter(is_active=True)
    ]
    
    # Include file content if requested
    if include_content and document.file_path:
        file_path = document.full_file_path
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    import base64
                    export_data['file_content_base64'] = base64.b64encode(f.read()).decode('utf-8')
            except Exception:
                export_data['file_content_base64'] = None
    
    # Format output
    if export_format == 'json':
        return export_data
    elif export_format == 'csv':
        return _export_to_csv(export_data)
    elif export_format == 'xml':
        return _export_to_xml(export_data)
    else:
        return json.dumps(export_data, indent=2)


def _export_to_csv(data):
    """Convert document data to CSV format."""
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers and basic data
    basic_fields = [
        'document_number', 'title', 'version', 'status', 'document_type',
        'author', 'created_at', 'effective_date', 'file_name'
    ]
    
    writer.writerow(basic_fields)
    writer.writerow([data.get(field, '') for field in basic_fields])
    
    # Add dependencies section
    if data.get('dependencies'):
        writer.writerow([])
        writer.writerow(['Dependencies'])
        writer.writerow(['Depends On', 'Type', 'Critical'])
        for dep in data['dependencies']:
            writer.writerow([
                dep['depends_on'],
                dep['dependency_type'],
                dep['is_critical']
            ])
    
    return output.getvalue()


def _export_to_xml(data):
    """Convert document data to XML format."""
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom
    
    root = Element('document')
    
    # Basic document information
    for key, value in data.items():
        if key not in ['dependencies', 'comments', 'attachments']:
            elem = SubElement(root, key)
            elem.text = str(value) if value is not None else ''
    
    # Dependencies
    if data.get('dependencies'):
        deps_elem = SubElement(root, 'dependencies')
        for dep in data['dependencies']:
            dep_elem = SubElement(deps_elem, 'dependency')
            for key, value in dep.items():
                sub_elem = SubElement(dep_elem, key)
                sub_elem.text = str(value)
    
    # Comments
    if data.get('comments'):
        comments_elem = SubElement(root, 'comments')
        for comment in data['comments']:
            comment_elem = SubElement(comments_elem, 'comment')
            for key, value in comment.items():
                sub_elem = SubElement(comment_elem, key)
                sub_elem.text = str(value) if value is not None else ''
    
    # Attachments
    if data.get('attachments'):
        attachments_elem = SubElement(root, 'attachments')
        for att in data['attachments']:
            att_elem = SubElement(attachments_elem, 'attachment')
            for key, value in att.items():
                sub_elem = SubElement(att_elem, key)
                sub_elem.text = str(value) if value is not None else ''
    
    # Pretty print XML
    rough_string = tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def generate_document_number(document_type, existing_numbers=None):
    """
    Generate a unique document number for a document type.
    
    Args:
        document_type: DocumentType instance
        existing_numbers: List of existing document numbers (optional)
        
    Returns:
        Generated document number string
    """
    year = timezone.now().year
    prefix = document_type.numbering_prefix or document_type.code
    
    # Find the next sequence number
    if existing_numbers:
        # Extract sequence numbers from existing numbers
        sequences = []
        for num in existing_numbers:
            if num.startswith(f"{prefix}-{year}-"):
                try:
                    seq = int(num.split('-')[-1])
                    sequences.append(seq)
                except (ValueError, IndexError):
                    continue
        
        next_seq = max(sequences) + 1 if sequences else 1
    else:
        # Query database for last document of this type
        from .models import Document
        
        last_doc = Document.objects.filter(
            document_type=document_type,
            document_number__startswith=f"{prefix}-{year}-"
        ).order_by('-document_number').first()
        
        if last_doc:
            try:
                last_seq = int(last_doc.document_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
    
    # Format using document type's numbering format
    return document_type.numbering_format.format(
        prefix=prefix,
        year=year,
        sequence=next_seq
    )


def validate_document_transition(document, new_status, user):
    """
    Validate if a document status transition is allowed.
    
    Args:
        document: Document instance
        new_status: Target status
        user: User attempting the transition
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    current_status = document.status
    
    # Define valid transitions
    valid_transitions = {
        'DRAFT': ['PENDING_REVIEW', 'TERMINATED'],
        'PENDING_REVIEW': ['UNDER_REVIEW', 'DRAFT'],
        'UNDER_REVIEW': ['REVIEW_COMPLETED', 'DRAFT'],
        'REVIEW_COMPLETED': ['PENDING_APPROVAL', 'DRAFT'],
        'PENDING_APPROVAL': ['UNDER_APPROVAL', 'REVIEW_COMPLETED'],
        'UNDER_APPROVAL': ['APPROVED', 'REVIEW_COMPLETED'],
        'APPROVED': ['EFFECTIVE'],
        'EFFECTIVE': ['SUPERSEDED', 'OBSOLETE'],
        'SUPERSEDED': [],  # No transitions from superseded
        'OBSOLETE': [],    # No transitions from obsolete
        'TERMINATED': [],  # No transitions from terminated
    }
    
    # Check if transition is valid
    if new_status not in valid_transitions.get(current_status, []):
        return False, f"Invalid transition from {current_status} to {new_status}"
    
    # Check user permissions for specific transitions
    if new_status in ['UNDER_REVIEW', 'REVIEW_COMPLETED']:
        if not document.can_review(user):
            return False, "You don't have permission to review this document"
    
    if new_status in ['UNDER_APPROVAL', 'APPROVED']:
        if not document.can_approve(user):
            return False, "You don't have permission to approve this document"
    
    if new_status == 'EFFECTIVE':
        if not document.can_approve(user):
            return False, "You don't have permission to make this document effective"
    
    return True, ""


def check_document_dependencies(document):
    """
    Check if document dependencies are satisfied.
    
    Args:
        document: Document instance
        
    Returns:
        Tuple of (dependencies_satisfied, missing_dependencies)
    """
    missing_deps = []
    
    for dependency in document.dependencies.filter(is_active=True, is_critical=True):
        dependent_doc = dependency.depends_on
        
        # Check if dependent document is in proper state
        if dependent_doc.status != 'EFFECTIVE':
            missing_deps.append({
                'document': dependent_doc.document_number,
                'title': dependent_doc.title,
                'status': dependent_doc.status,
                'dependency_type': dependency.dependency_type
            })
    
    return len(missing_deps) == 0, missing_deps


def get_document_impact_analysis(document):
    """
    Analyze the impact of changes to a document.
    
    Args:
        document: Document instance
        
    Returns:
        Dict containing impact analysis data
    """
    impact_data = {
        'dependent_documents': [],
        'affected_users': set(),
        'training_required': False,
        'approval_required': False
    }
    
    # Find documents that depend on this one
    for dependency in document.dependents.filter(is_active=True):
        dependent_doc = dependency.document
        impact_data['dependent_documents'].append({
            'document_number': dependent_doc.document_number,
            'title': dependent_doc.title,
            'author': dependent_doc.author.get_full_name(),
            'status': dependent_doc.status,
            'dependency_type': dependency.dependency_type,
            'is_critical': dependency.is_critical
        })
        
        # Add affected users
        impact_data['affected_users'].add(dependent_doc.author.get_full_name())
        if dependent_doc.reviewer:
            impact_data['affected_users'].add(dependent_doc.reviewer.get_full_name())
        if dependent_doc.approver:
            impact_data['affected_users'].add(dependent_doc.approver.get_full_name())
    
    # Convert set to list for JSON serialization
    impact_data['affected_users'] = list(impact_data['affected_users'])
    
    # Check if training is required
    impact_data['training_required'] = document.requires_training
    
    # Check if approval is required for changes
    impact_data['approval_required'] = (
        document.document_type.approval_required if document.document_type else True
    )
    
    return impact_data