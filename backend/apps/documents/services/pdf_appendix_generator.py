"""
PDF Appendix Generator
Generates version history and metadata appendix for PDF documents
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from io import BytesIO
from django.utils import timezone


class PDFAppendixGenerator:
    """
    Generates version history appendix for PDF documents
    """
    
    # Color scheme
    PRIMARY_COLOR = colors.HexColor('#1E3A8A')      # Professional Blue
    SECONDARY_COLOR = colors.HexColor('#64748B')    # Slate Gray
    HEADER_BG = colors.HexColor('#1E3A8A')          # Blue header
    ALT_ROW = colors.HexColor('#F9FAFB')            # Light gray alternating
    
    def __init__(self, document):
        """
        Initialize appendix generator
        
        Args:
            document: Document model instance
        """
        self.document = document
        self.buffer = BytesIO()
        self.width, self.height = A4
        
    def generate_version_history(self) -> bytes:
        """
        Generate version history appendix
        
        Returns:
            bytes: PDF appendix as bytes
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            leftMargin=25*mm,
            rightMargin=25*mm,
            topMargin=25*mm,
            bottomMargin=25*mm
        )
        
        # Build content
        story = []
        
        # Title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph("APPENDIX A: VERSION HISTORY", title_style))
        story.append(Spacer(1, 10*mm))
        
        # Get all versions
        versions = self._get_all_versions()
        
        if versions:
            # Create table
            table = self._create_version_table(versions)
            story.append(table)
        else:
            # No versions found
            story.append(Paragraph("No version history available.", styles['Normal']))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        # Get PDF bytes
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()
        
        return pdf_bytes
    
    def _get_all_versions(self):
        """
        Get all versions of the document
        
        Returns:
            list: List of version dictionaries
        """
        versions = []
        
        # Get all versions of this document
        # Documents with same document_number but different versions
        from apps.documents.models import Document
        
        all_versions = Document.objects.filter(
            document_number=self.document.document_number
        ).order_by('-version_major', '-version_minor')
        
        for doc in all_versions:
            # Get approver info
            approver = self._get_approver_for_document(doc)
            
            # Get changes summary
            changes = self._get_changes_summary(doc)
            
            versions.append({
                'version': f"v{doc.version_major:02d}.{doc.version_minor:02d}",
                'date': doc.effective_date.strftime('%Y-%m-%d') if doc.effective_date else 'Not set',
                'approver': approver,
                'status': doc.status,
                'changes': changes
            })
        
        return versions
    
    def _get_approver_for_document(self, doc):
        """Get approver name for a document version"""
        try:
            # Try to get from workflow approval
            # For now, use document author as fallback
            author = doc.author
            
            # Get user's role
            role = 'Author'
            if hasattr(author, 'userrole_set'):
                user_roles = author.userrole_set.filter(is_active=True)
                if user_roles.exists():
                    role = user_roles.first().role.role_name
            
            full_name = author.get_full_name() or author.username
            return f"{full_name} ({role})"
            
        except Exception as e:
            print(f"Warning: Could not get approver for version: {e}")
            return "N/A"
    
    def _get_changes_summary(self, doc):
        """Get summary of changes for a version"""
        # Check if document has version notes/comments
        if hasattr(doc, 'version_notes') and doc.version_notes:
            # Limit to 100 characters
            summary = doc.version_notes[:100]
            if len(doc.version_notes) > 100:
                summary += '...'
            return summary
        
        # Check if it's the first version
        if doc.version_major == 1 and doc.version_minor == 0:
            return "Initial release"
        
        # Generic update message
        if doc.version_minor == 0:
            return f"Major update from v{doc.version_major-1:02d}.xx"
        else:
            return f"Minor update from v{doc.version_major:02d}.{doc.version_minor-1:02d}"
    
    def _create_version_table(self, versions):
        """
        Create version history table
        
        Args:
            versions: List of version dictionaries
            
        Returns:
            Table: ReportLab Table object
        """
        # Table data
        data = [
            ['Version', 'Effective Date', 'Approved By', 'Status', 'Summary of Changes']
        ]
        
        # Add version rows
        for v in versions:
            data.append([
                v['version'],
                v['date'],
                v['approver'],
                v['status'],
                v['changes']
            ])
        
        # Column widths (total = 160mm for A4 with 25mm margins)
        col_widths = [20*mm, 25*mm, 40*mm, 25*mm, 50*mm]
        
        # Create table
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Table style
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Version column centered
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Date column centered
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Status column centered
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.white),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.ALT_ROW]),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        return table
    
    def _add_page_number(self, canvas, doc):
        """
        Add page number to appendix pages
        
        Args:
            canvas: ReportLab canvas
            doc: Document template
        """
        # Get current page number
        page_num = canvas.getPageNumber()
        
        # Format as A-1, A-2, etc.
        text = f"Page A-{page_num}"
        
        # Draw at bottom center
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(
            A4[0] / 2,
            15*mm,
            text
        )
