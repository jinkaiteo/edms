"""
Document Handler for EDMS Workflows.

Implements document upload/download integration as required by 
EDMS_details_workflow.txt lines 5, 7, 12, 49-68.
"""

import os
from django.core.files.storage import default_storage
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from apps.documents.models import Document
from apps.placeholders.services import PlaceholderService
from .comment_manager import WorkflowCommentManager


class WorkflowDocumentHandler:
    """Handles document operations within workflow context."""
    
    @staticmethod
    def upload_document_to_workflow(workflow, uploaded_file, user):
        """
        Upload document during workflow creation.
        EDMS specification line 5.
        """
        document = workflow.document
        
        # Store original file
        file_path = f"documents/{document.id}/original/{uploaded_file.name}"
        saved_path = default_storage.save(file_path, uploaded_file)
        
        # Update document with file information
        document.file_path = saved_path
        document.file_name = uploaded_file.name
        document.file_size = uploaded_file.size
        document.uploaded_by = user
        document.uploaded_at = timezone.now()
        document.save()
        
        # Log upload in workflow data
        workflow.workflow_data['upload_history'] = workflow.workflow_data.get('upload_history', [])
        workflow.workflow_data['upload_history'].append({
            'timestamp': timezone.now().isoformat(),
            'filename': uploaded_file.name,
            'size': uploaded_file.size,
            'uploaded_by': user.username
        })
        workflow.save()
        
        return document
    
    @staticmethod
    def download_original_document(workflow, user):
        """
        Download original unmodified document.
        EDMS specification line 50.
        """
        document = workflow.document
        
        if not document.file_path or not default_storage.exists(document.file_path):
            raise Http404("Document file not found")
        
        # Log download
        workflow.workflow_data['download_history'] = workflow.workflow_data.get('download_history', [])
        workflow.workflow_data['download_history'].append({
            'timestamp': timezone.now().isoformat(),
            'type': 'original',
            'downloaded_by': user.username
        })
        workflow.save()
        
        # Return file response
        file_content = default_storage.open(document.file_path).read()
        response = HttpResponse(file_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'
        
        return response
    
    @staticmethod
    def download_annotated_document(workflow, user):
        """
        Download document with appended metadata.
        EDMS specification lines 51, 56-60.
        """
        document = workflow.document
        
        if document.file_name.endswith('.docx'):
            # For .docx files: replace placeholders with metadata
            annotated_content = WorkflowDocumentHandler._create_annotated_docx(workflow)
            response = HttpResponse(annotated_content, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            filename = f"{os.path.splitext(document.file_name)[0]}_annotated.docx"
        else:
            # For other files: provide original + metadata text file
            original_content = default_storage.open(document.file_path).read()
            metadata_content = WorkflowDocumentHandler._create_metadata_text(workflow)
            
            # Create ZIP with both files
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                zip_file.writestr(document.file_name, original_content)
                zip_file.writestr('metadata.txt', metadata_content)
            
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            filename = f"{os.path.splitext(document.file_name)[0]}_with_metadata.zip"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Log download
        workflow.workflow_data['download_history'] = workflow.workflow_data.get('download_history', [])
        workflow.workflow_data['download_history'].append({
            'timestamp': timezone.now().isoformat(),
            'type': 'annotated',
            'downloaded_by': user.username
        })
        workflow.save()
        
        return response
    
    @staticmethod
    def download_official_pdf(workflow, user):
        """
        Download digitally signed official PDF.
        EDMS specification lines 52, 61-68.
        """
        document = workflow.document
        
        # Only allow for approved and effective documents
        if workflow.current_state_id != DocumentState.APPROVED_AND_EFFECTIVE:
            raise ValueError("Official PDF only available for approved and effective documents")
        
        if document.file_name.endswith('.docx'):
            # Generate annotated document then convert to PDF
            pdf_content = WorkflowDocumentHandler._create_signed_pdf_from_docx(workflow)
        else:
            # Convert file to PDF, annotate, then sign
            pdf_content = WorkflowDocumentHandler._create_signed_pdf_from_other(workflow)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"{os.path.splitext(document.file_name)[0]}_official.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Log download
        workflow.workflow_data['download_history'] = workflow.workflow_data.get('download_history', [])
        workflow.workflow_data['download_history'].append({
            'timestamp': timezone.now().isoformat(),
            'type': 'official_pdf',
            'downloaded_by': user.username
        })
        workflow.save()
        
        return response
    
    @staticmethod
    def _create_annotated_docx(workflow):
        """Create .docx with replaced placeholders."""
        document = workflow.document
        
        # Get document metadata
        metadata = WorkflowDocumentHandler._get_document_metadata(workflow)
        
        # Use placeholder service to replace placeholders
        placeholder_service = PlaceholderService()
        annotated_content = placeholder_service.replace_placeholders_in_docx(
            document.file_path,
            metadata
        )
        
        return annotated_content
    
    @staticmethod
    def _create_metadata_text(workflow):
        """Create metadata text file for non-.docx documents."""
        metadata = WorkflowDocumentHandler._get_document_metadata(workflow)
        
        metadata_text = "EDMS Document Metadata\n"
        metadata_text += "=" * 30 + "\n\n"
        
        for key, value in metadata.items():
            metadata_text += f"{key}: {value}\n"
        
        # Add workflow comments
        comments = WorkflowCommentManager.get_all_comments(workflow)
        if comments:
            metadata_text += "\nWorkflow Comments:\n"
            metadata_text += "-" * 20 + "\n"
            for comment in comments:
                metadata_text += f"{comment.user.username} ({comment.comment_type}): {comment.comment}\n"
        
        return metadata_text
    
    @staticmethod
    def _get_document_metadata(workflow):
        """Get complete document metadata for annotations."""
        from django.utils import timezone
        
        document = workflow.document
        
        # Get reviewer and approver from workflow
        reviewer = workflow.selected_reviewer or "Not assigned"
        approver = workflow.selected_approver or "Not assigned"
        
        # Get review and approval comments
        review_comments = WorkflowCommentManager.get_review_comments(workflow)
        approval_comments = WorkflowCommentManager.get_approval_comments(workflow)
        
        metadata = {
            'document_number': document.document_number or "TBD",
            'document_title': document.title,
            'version': document.version or "1.0",
            'document_type': document.document_type.name if document.document_type else "Unknown",
            'document_source': getattr(document, 'source', 'Original Digital Draft'),
            'author': document.author.get_full_name() if document.author else "Unknown",
            'reviewer': reviewer.get_full_name() if hasattr(reviewer, 'get_full_name') else str(reviewer),
            'approver': approver.get_full_name() if hasattr(approver, 'get_full_name') else str(approver),
            'approval_date': workflow.effective_date.strftime('%Y-%m-%d') if workflow.effective_date else "TBD",
            'effective_date': workflow.effective_date.strftime('%Y-%m-%d') if workflow.effective_date else "TBD",
            'current_status': workflow.current_state.name if workflow.current_state else "Unknown",
            'download_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'workflow_type': workflow.get_workflow_type_display(),
            'review_comments_count': review_comments.count(),
            'approval_comments_count': approval_comments.count(),
        }
        
        # Add revision history
        transitions = workflow.transitions.all().order_by('transitioned_at')
        revision_history = []
        for transition in transitions:
            revision_history.append(f"{transition.transitioned_at.strftime('%Y-%m-%d')}: {transition.from_state.name} → {transition.to_state.name}")
        
        metadata['revision_history'] = "; ".join(revision_history) if revision_history else "Initial version"
        
        return metadata
    
    @staticmethod
    def _create_signed_pdf_from_docx(workflow):
        """Create digitally signed PDF from .docx file."""
        # This would integrate with digital signature service
        # For now, return placeholder
        return b"Digital signature PDF creation not yet implemented"
    
    @staticmethod
    def _create_signed_pdf_from_other(workflow):
        """Create digitally signed PDF from other file types."""
        # This would convert file to PDF, add metadata, and sign
        # For now, return placeholder
        return b"Digital signature PDF creation not yet implemented"