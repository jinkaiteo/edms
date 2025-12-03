"""
ZIP-based Document Processing for Non-DOCX Files
Creates professional metadata packages with VERSION_HISTORY tables for all document formats
"""

import os
import tempfile
import zipfile
from typing import Dict, Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Document
from .annotation_processor import annotation_processor

User = get_user_model()


class ZipDocumentProcessor:
    """
    Service class for creating ZIP packages with original documents plus metadata files
    for non-DOCX document formats
    """
    
    def create_annotated_zip(self, document: Document, user: User = None) -> Optional[str]:
        """
        Create ZIP package with original document + formatted metadata for annotation download
        Returns path to ZIP file or None if processing fails
        """
        if not document.file_path or not document.full_file_path:
            raise ValueError("Document has no attached file")
        
        if not os.path.exists(document.full_file_path):
            raise FileNotFoundError(f"Document file not found: {document.full_file_path}")
        
        try:
            # Get metadata for the document
            metadata = annotation_processor.get_document_metadata(document, user)
            
            # Create temporary ZIP file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add original document
                original_filename = document.file_name or f"{document.document_number}.{self._get_file_extension(document)}"
                zipf.write(document.full_file_path, original_filename)
                
                # Create and add metadata text file
                metadata_content = self._create_metadata_text_file(metadata, document, user)
                metadata_filename = f"{document.document_number}_metadata.txt"
                zipf.writestr(metadata_filename, metadata_content)
                
                # Create and add placeholder reference file
                placeholder_content = self._create_placeholder_reference_file(metadata, document)
                placeholder_filename = f"{document.document_number}_placeholders.txt"
                zipf.writestr(placeholder_filename, placeholder_content)
                
                # Add README file for user instructions
                readme_content = self._create_readme_file(document)
                zipf.writestr("README.txt", readme_content)
            
            # Verify ZIP was created successfully
            if not os.path.exists(temp_zip_path):
                raise RuntimeError("Failed to create ZIP file")
            
            file_size = os.path.getsize(temp_zip_path)
            if file_size == 0:
                raise RuntimeError("Generated ZIP file is empty")
            
            print(f"✅ ZIP package created successfully: {temp_zip_path} ({file_size} bytes)")
            return temp_zip_path
            
        except Exception as e:
            # Clean up on error
            if 'temp_zip_path' in locals() and os.path.exists(temp_zip_path):
                try:
                    os.unlink(temp_zip_path)
                except:
                    pass
            raise RuntimeError(f"Failed to create annotated ZIP package: {str(e)}")
    
    def create_official_pdf_zip(self, document: Document, user: User = None) -> Optional[str]:
        """
        Create ZIP package with PDF conversion + PDF metadata for official PDF download
        Returns path to ZIP file or None if processing fails
        """
        if not document.file_path or not document.full_file_path:
            raise ValueError("Document has no attached file")
        
        if not os.path.exists(document.full_file_path):
            raise FileNotFoundError(f"Document file not found: {document.full_file_path}")
        
        try:
            # Get metadata for the document
            metadata = annotation_processor.get_document_metadata(document, user)
            
            # Create temporary ZIP file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Convert original document to PDF using LibreOffice
                pdf_content = self._convert_to_pdf(document)
                pdf_filename = f"{document.document_number}.pdf"
                zipf.writestr(pdf_filename, pdf_content)
                
                # Create and add metadata PDF file
                metadata_pdf_content = self._create_metadata_pdf_file(metadata, document, user)
                metadata_pdf_filename = f"{document.document_number}_metadata.pdf"
                zipf.writestr(metadata_pdf_filename, metadata_pdf_content)
                
                # Create and add placeholder reference PDF
                placeholder_pdf_content = self._create_placeholder_reference_pdf(metadata, document)
                placeholder_pdf_filename = f"{document.document_number}_placeholders.pdf"
                zipf.writestr(placeholder_pdf_filename, placeholder_pdf_content)
                
                # Add README file for user instructions
                readme_content = self._create_readme_file(document, pdf_mode=True)
                zipf.writestr("README.txt", readme_content)
            
            # Verify ZIP was created successfully
            if not os.path.exists(temp_zip_path):
                raise RuntimeError("Failed to create ZIP file")
            
            file_size = os.path.getsize(temp_zip_path)
            if file_size == 0:
                raise RuntimeError("Generated ZIP file is empty")
            
            print(f"✅ Official PDF ZIP package created: {temp_zip_path} ({file_size} bytes)")
            return temp_zip_path
            
        except Exception as e:
            # Clean up on error
            if 'temp_zip_path' in locals() and os.path.exists(temp_zip_path):
                try:
                    os.unlink(temp_zip_path)
                except:
                    pass
            raise RuntimeError(f"Failed to create official PDF ZIP package: {str(e)}")
    
    def _create_metadata_text_file(self, metadata: Dict[str, Any], document: Document, user: User = None) -> str:
        """Create formatted metadata text file with professional VERSION_HISTORY table"""
        lines = []
        
        # Header
        lines.append(f"DOCUMENT METADATA - {document.document_number}")
        lines.append("=" * (len(f"DOCUMENT METADATA - {document.document_number}")))
        lines.append("")
        
        # Core metadata in organized sections
        lines.append("DOCUMENT INFORMATION")
        lines.append("-" * 20)
        lines.append(f"Document Number: {metadata.get('DOCUMENT_NUMBER', 'N/A')}")
        lines.append(f"Title: {metadata.get('DOCUMENT_TITLE', 'N/A')}")
        lines.append(f"Version: {metadata.get('VERSION_FULL', 'N/A')}")
        lines.append(f"Status: {metadata.get('DOC_STATUS', 'N/A')}")
        lines.append(f"Type: {metadata.get('DOCUMENT_TYPE', 'N/A')}")
        lines.append("")
        
        lines.append("PEOPLE & DATES")
        lines.append("-" * 15)
        lines.append(f"Author: {metadata.get('AUTHOR', 'N/A')}")
        lines.append(f"Reviewer: {metadata.get('REVIEWER', 'N/A')}")
        lines.append(f"Approver: {metadata.get('APPROVER', 'N/A')}")
        lines.append(f"Created: {metadata.get('CREATED_DATE', 'N/A')}")
        lines.append(f"Updated: {metadata.get('UPDATED_DATE', 'N/A')}")
        lines.append(f"Effective Date: {metadata.get('EFFECTIVE_DATE', 'N/A')}")
        lines.append(f"Approval Date: {metadata.get('APPROVAL_DATE', 'N/A')}")
        lines.append("")
        
        # Add VERSION_HISTORY using existing text formatting
        lines.append("VERSION HISTORY")
        lines.append("=" * 15)
        lines.append("")
        
        # Get version history from placeholder service
        from apps.placeholders.services import placeholder_service
        context = {'document': document}
        version_data = placeholder_service._get_version_history_data(document)
        
        if 'rows' in version_data and version_data['rows']:
            # Create professional text table
            lines.append("Version    | Date       | Author          | Status      | Comments")
            lines.append("-----------|------------|-----------------|-------------|------------------")
            
            for row in version_data['rows']:
                version = row['version'][:10].ljust(10)
                date = row['date'][:10].ljust(10)
                author = row['author'][:15].ljust(15)
                status = row['status'][:11].ljust(11)
                comments = row['comments'][:18] if len(row['comments']) <= 18 else row['comments'][:15] + "..."
                
                lines.append(f"{version} | {date} | {author} | {status} | {comments}")
            
            lines.append("")
            lines.append(f"Generated: {version_data['generated']}")
        else:
            lines.append("No version history available")
        
        lines.append("")
        lines.append("")
        
        # File information
        lines.append("FILE INFORMATION")
        lines.append("-" * 16)
        lines.append(f"File Name: {document.file_name or 'N/A'}")
        lines.append(f"File Size: {metadata.get('FILE_SIZE', 'N/A')}")
        lines.append(f"MIME Type: {metadata.get('MIME_TYPE', 'N/A')}")
        lines.append(f"Checksum: {metadata.get('FILE_CHECKSUM', 'N/A')}")
        lines.append("")
        
        # System information
        lines.append("SYSTEM INFORMATION")
        lines.append("-" * 18)
        lines.append(f"Generated By: {user.get_full_name() if user else 'System'}")
        lines.append(f"Generated On: {metadata.get('CURRENT_DATETIME', 'N/A')}")
        lines.append(f"System: {metadata.get('SYSTEM_NAME', 'EDMS')}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _create_placeholder_reference_file(self, metadata: Dict[str, Any], document: Document) -> str:
        """Create placeholder reference guide showing all available placeholders"""
        lines = []
        
        # Header
        lines.append(f"PLACEHOLDER REFERENCE - {document.document_number}")
        lines.append("=" * (len(f"PLACEHOLDER REFERENCE - {document.document_number}")))
        lines.append("")
        lines.append("This file shows all available placeholders and their current values for this document.")
        lines.append("Use these placeholders in templates by wrapping them in double curly braces: {{PLACEHOLDER_NAME}}")
        lines.append("")
        
        # Group placeholders by type
        placeholder_groups = {
            'Document Information': [
                'DOCUMENT_NUMBER', 'DOCUMENT_TITLE', 'DOC_STATUS', 'DOCUMENT_TYPE', 
                'VERSION_FULL', 'VERSION_MAJOR', 'VERSION_MINOR'
            ],
            'People & Roles': [
                'AUTHOR', 'REVIEWER', 'APPROVER', 'AUTHOR_EMAIL', 'REVIEWER_EMAIL', 'APPROVER_EMAIL'
            ],
            'Dates & Times': [
                'CREATED_DATE', 'UPDATED_DATE', 'EFFECTIVE_DATE', 'APPROVAL_DATE',
                'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_DATETIME'
            ],
            'File Information': [
                'FILE_NAME', 'FILE_SIZE', 'MIME_TYPE', 'FILE_CHECKSUM'
            ],
            'Version History': [
                'VERSION_HISTORY', 'REVISION_COUNT', 'PREVIOUS_VERSION'
            ],
            'System Information': [
                'ORGANIZATION', 'SYSTEM_NAME', 'DOWNLOAD_DATETIME'
            ]
        }
        
        for group_name, placeholder_names in placeholder_groups.items():
            lines.append(f"{group_name.upper()}")
            lines.append("-" * len(group_name))
            
            for placeholder in placeholder_names:
                value = metadata.get(placeholder, 'Not available')
                if placeholder == 'VERSION_HISTORY':
                    value = '[See VERSION HISTORY section in metadata file]'
                elif isinstance(value, str) and len(value) > 60:
                    value = value[:57] + "..."
                
                lines.append(f"{{{{{placeholder}}}}}")
                lines.append(f"  → {value}")
                lines.append("")
            
            lines.append("")
        
        # Usage examples
        lines.append("USAGE EXAMPLES")
        lines.append("-" * 14)
        lines.append("")
        lines.append("In a Word template:")
        lines.append("  Document: {{DOCUMENT_NUMBER}}")
        lines.append("  Title: {{DOCUMENT_TITLE}}")
        lines.append("  Version: {{VERSION_FULL}}")
        lines.append("  Author: {{AUTHOR}}")
        lines.append("")
        lines.append("In an HTML template:")
        lines.append("  <h1>{{DOCUMENT_TITLE}}</h1>")
        lines.append("  <p>Document Number: {{DOCUMENT_NUMBER}}</p>")
        lines.append("  <p>Status: {{DOC_STATUS}}</p>")
        lines.append("")
        lines.append("Version History Table:")
        lines.append("  {{VERSION_HISTORY}}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _create_readme_file(self, document: Document, pdf_mode: bool = False) -> str:
        """Create README file with user instructions"""
        lines = []
        
        format_type = "PDF" if pdf_mode else "Annotated"
        
        lines.append(f"{format_type.upper()} DOCUMENT PACKAGE - {document.document_number}")
        lines.append("=" * (len(f"{format_type.upper()} DOCUMENT PACKAGE - {document.document_number}")))
        lines.append("")
        lines.append("This ZIP package contains your document and professional metadata files.")
        lines.append("")
        
        lines.append("PACKAGE CONTENTS")
        lines.append("-" * 16)
        if pdf_mode:
            lines.append(f"• {document.document_number}.pdf - Official PDF version")
            lines.append(f"• {document.document_number}_metadata.pdf - Document metadata (PDF)")
            lines.append(f"• {document.document_number}_placeholders.pdf - Placeholder reference (PDF)")
        else:
            original_name = document.file_name or f"{document.document_number}.{self._get_file_extension(document)}"
            lines.append(f"• {original_name} - Original document file")
            lines.append(f"• {document.document_number}_metadata.txt - Document metadata")
            lines.append(f"• {document.document_number}_placeholders.txt - Placeholder reference")
        lines.append("• README.txt - This file")
        lines.append("")
        
        lines.append("METADATA FEATURES")
        lines.append("-" * 17)
        lines.append("✅ Professional VERSION HISTORY table with:")
        lines.append("   - Version numbers and dates")
        lines.append("   - Author information")
        lines.append("   - Status tracking") 
        lines.append("   - Change reasons")
        lines.append("✅ Complete document information")
        lines.append("✅ All placeholder values for template use")
        lines.append("✅ File and system information")
        lines.append("")
        
        lines.append("USAGE SCENARIOS")
        lines.append("-" * 15)
        if pdf_mode:
            lines.append("• Official distribution and archival")
            lines.append("• Regulatory submissions")
            lines.append("• Professional presentations")
            lines.append("• Document audit trails")
        else:
            lines.append("• Document review and collaboration")
            lines.append("• Template creation and testing")
            lines.append("• Document analysis and reporting")
            lines.append("• Metadata extraction for other systems")
        lines.append("")
        
        lines.append("GENERATED BY")
        lines.append("-" * 12)
        lines.append("Electronic Document Management System (EDMS)")
        lines.append("Professional document processing with compliance features")
        lines.append("")
        
        return "\n".join(lines)
    
    def _convert_to_pdf(self, document: Document) -> bytes:
        """Convert document to PDF using LibreOffice"""
        import subprocess
        import tempfile
        import shutil
        
        try:
            # Create temporary directory for conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy original file to temp directory
                temp_input = os.path.join(temp_dir, document.file_name)
                shutil.copy2(document.full_file_path, temp_input)
                
                # Convert to PDF using LibreOffice
                cmd = [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir,
                    temp_input
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
                
                # Find generated PDF
                pdf_name = os.path.splitext(document.file_name)[0] + '.pdf'
                pdf_path = os.path.join(temp_dir, pdf_name)
                
                if not os.path.exists(pdf_path):
                    raise RuntimeError(f"PDF file not generated: {pdf_path}")
                
                # Read PDF content
                with open(pdf_path, 'rb') as f:
                    return f.read()
                    
        except Exception as e:
            raise RuntimeError(f"Failed to convert document to PDF: {str(e)}")
    
    def _create_metadata_pdf_file(self, metadata: Dict[str, Any], document: Document, user: User = None) -> bytes:
        """Create PDF version of metadata file"""
        # Create HTML version first, then convert to PDF
        html_content = self._create_metadata_html(metadata, document, user)
        return self._convert_html_to_pdf(html_content)
    
    def _create_placeholder_reference_pdf(self, metadata: Dict[str, Any], document: Document) -> bytes:
        """Create PDF version of placeholder reference"""
        # Create HTML version first, then convert to PDF  
        html_content = self._create_placeholder_reference_html(metadata, document)
        return self._convert_html_to_pdf(html_content)
    
    def _create_metadata_html(self, metadata: Dict[str, Any], document: Document, user: User = None) -> str:
        """Create HTML version of metadata for PDF conversion"""
        html_parts = []
        
        html_parts.append("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Document Metadata</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; border-bottom: 2px solid #333; }
                h2 { color: #666; border-bottom: 1px solid #ccc; margin-top: 20px; }
                table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background-color: #f0f0f0; font-weight: bold; }
                .section { margin: 20px 0; }
                .info-table td:first-child { font-weight: bold; width: 200px; }
            </style>
        </head>
        <body>
        """)
        
        html_parts.append(f"<h1>Document Metadata - {document.document_number}</h1>")
        
        # Document information section
        html_parts.append("<div class='section'>")
        html_parts.append("<h2>Document Information</h2>")
        html_parts.append("<table class='info-table'>")
        info_items = [
            ("Document Number", metadata.get('DOCUMENT_NUMBER', 'N/A')),
            ("Title", metadata.get('DOCUMENT_TITLE', 'N/A')),
            ("Version", metadata.get('VERSION_FULL', 'N/A')),
            ("Status", metadata.get('DOC_STATUS', 'N/A')),
            ("Type", metadata.get('DOCUMENT_TYPE', 'N/A')),
            ("Author", metadata.get('AUTHOR', 'N/A')),
            ("Reviewer", metadata.get('REVIEWER', 'N/A')),
            ("Approver", metadata.get('APPROVER', 'N/A')),
            ("Created", metadata.get('CREATED_DATE', 'N/A')),
            ("Updated", metadata.get('UPDATED_DATE', 'N/A')),
            ("Effective Date", metadata.get('EFFECTIVE_DATE', 'N/A')),
        ]
        
        for label, value in info_items:
            html_parts.append(f"<tr><td>{label}</td><td>{value}</td></tr>")
        
        html_parts.append("</table>")
        html_parts.append("</div>")
        
        # Version history section with professional table
        html_parts.append("<div class='section'>")
        html_parts.append("<h2>Version History</h2>")
        
        # Get version history from placeholder service
        from apps.placeholders.services import placeholder_service
        version_data = placeholder_service._get_version_history_data(document)
        
        if 'rows' in version_data and version_data['rows']:
            html_parts.append("<table>")
            html_parts.append("<tr><th>Version</th><th>Date</th><th>Author</th><th>Status</th><th>Comments</th></tr>")
            
            for row in version_data['rows']:
                html_parts.append(f"<tr><td>{row['version']}</td><td>{row['date']}</td><td>{row['author']}</td><td>{row['status']}</td><td>{row['comments']}</td></tr>")
            
            html_parts.append("</table>")
            html_parts.append(f"<p><em>Generated: {version_data['generated']}</em></p>")
        else:
            html_parts.append("<p>No version history available</p>")
        
        html_parts.append("</div>")
        
        html_parts.append("</body></html>")
        
        return "\n".join(html_parts)
    
    def _create_placeholder_reference_html(self, metadata: Dict[str, Any], document: Document) -> str:
        """Create HTML version of placeholder reference for PDF conversion"""
        html_parts = []
        
        html_parts.append("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Placeholder Reference</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; border-bottom: 2px solid #333; }
                h2 { color: #666; margin-top: 20px; }
                .placeholder { font-family: monospace; background: #f5f5f5; padding: 2px 4px; }
                .value { margin-left: 20px; color: #666; }
                .section { margin: 15px 0; }
            </style>
        </head>
        <body>
        """)
        
        html_parts.append(f"<h1>Placeholder Reference - {document.document_number}</h1>")
        html_parts.append("<p>This document shows all available placeholders and their current values.</p>")
        
        # Group placeholders by type
        placeholder_groups = {
            'Document Information': [
                'DOCUMENT_NUMBER', 'DOCUMENT_TITLE', 'DOC_STATUS', 'VERSION_FULL'
            ],
            'People & Roles': [
                'AUTHOR', 'REVIEWER', 'APPROVER'
            ],
            'Version History': [
                'VERSION_HISTORY', 'REVISION_COUNT', 'PREVIOUS_VERSION'
            ],
            'Dates & Times': [
                'CREATED_DATE', 'EFFECTIVE_DATE', 'CURRENT_DATETIME'
            ]
        }
        
        for group_name, placeholder_names in placeholder_groups.items():
            html_parts.append(f"<h2>{group_name}</h2>")
            html_parts.append("<div class='section'>")
            
            for placeholder in placeholder_names:
                value = metadata.get(placeholder, 'Not available')
                if placeholder == 'VERSION_HISTORY':
                    value = '[See VERSION HISTORY section]'
                
                html_parts.append(f"<div><span class='placeholder'>{{{{{placeholder}}}}}</span></div>")
                html_parts.append(f"<div class='value'>→ {value}</div><br>")
            
            html_parts.append("</div>")
        
        html_parts.append("</body></html>")
        
        return "\n".join(html_parts)
    
    def _convert_html_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML content to PDF using LibreOffice"""
        import subprocess
        import tempfile
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write HTML to temporary file
                html_file = os.path.join(temp_dir, 'temp.html')
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Convert HTML to PDF using LibreOffice
                cmd = [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir,
                    html_file
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    raise RuntimeError(f"HTML to PDF conversion failed: {result.stderr}")
                
                # Read generated PDF
                pdf_file = os.path.join(temp_dir, 'temp.pdf')
                if not os.path.exists(pdf_file):
                    raise RuntimeError("PDF file not generated")
                
                with open(pdf_file, 'rb') as f:
                    return f.read()
                    
        except Exception as e:
            raise RuntimeError(f"Failed to convert HTML to PDF: {str(e)}")
    
    def _get_file_extension(self, document: Document) -> str:
        """Get file extension or default based on MIME type"""
        if document.file_name:
            return os.path.splitext(document.file_name)[1].lstrip('.')
        elif document.mime_type:
            # Basic MIME type to extension mapping
            mime_to_ext = {
                'application/pdf': 'pdf',
                'text/plain': 'txt',
                'text/html': 'html',
                'application/msword': 'doc',
                'application/vnd.ms-excel': 'xls',
                'application/vnd.ms-powerpoint': 'ppt',
                'image/jpeg': 'jpg',
                'image/png': 'png'
            }
            return mime_to_ext.get(document.mime_type, 'bin')
        else:
            return 'bin'


# Global instance for easy access
zip_processor = ZipDocumentProcessor()