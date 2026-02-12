"""
PDF Cover Page Generator
Generates professional cover pages for PDF documents with company branding
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from io import BytesIO
from django.conf import settings
from apps.documents.models import SystemConfiguration
import os


class PDFCoverPageGenerator:
    """
    Generates professional cover pages for PDF documents
    """
    
    # Color scheme - Professional blue/gray
    PRIMARY_COLOR = colors.HexColor('#1E3A8A')      # Professional Blue
    SECONDARY_COLOR = colors.HexColor('#64748B')    # Slate Gray
    ACCENT_COLOR = colors.HexColor('#3B82F6')       # Light Blue
    
    # Status colors
    STATUS_COLORS = {
        'EFFECTIVE': colors.HexColor('#10B981'),    # Green
        'DRAFT': colors.HexColor('#F59E0B'),        # Amber
        'OBSOLETE': colors.HexColor('#EF4444'),     # Red
        'SUPERSEDED': colors.HexColor('#8B5CF6'),   # Purple
    }
    
    def __init__(self, document):
        """
        Initialize cover page generator
        
        Args:
            document: Document model instance
        """
        self.document = document
        self.config = SystemConfiguration.get_instance()
        self.buffer = BytesIO()
        self.width, self.height = A4
        
    def generate(self) -> bytes:
        """
        Generate cover page PDF
        
        Returns:
            bytes: PDF cover page as bytes
        """
        # Create PDF canvas
        c = canvas.Canvas(self.buffer, pagesize=A4)
        
        # Draw cover page elements
        self._draw_header(c)
        self._draw_title_section(c)
        self._draw_metadata_section(c)
        self._draw_footer(c)
        
        # Finalize page
        c.showPage()
        c.save()
        
        # Get PDF bytes
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()
        
        return pdf_bytes
    
    def _draw_header(self, canvas):
        """Draw header with logo and status badge"""
        y_position = self.height - 40*mm
        
        # Draw logo if exists
        if self.config.logo:
            try:
                logo_path = self.config.logo.path
                if os.path.exists(logo_path):
                    # Logo on left (max 60x20mm)
                    canvas.drawImage(
                        logo_path,
                        25*mm,  # Left margin
                        y_position,
                        width=60*mm,
                        height=20*mm,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
            except Exception as e:
                print(f"Warning: Could not load logo: {e}")
        
        # Status badge on right
        status = self.document.status
        status_color = self.STATUS_COLORS.get(status, self.SECONDARY_COLOR)
        
        # Draw rounded rectangle for status badge
        badge_x = self.width - 25*mm - 50*mm
        badge_y = y_position + 15*mm
        badge_width = 50*mm
        badge_height = 10*mm
        
        canvas.setFillColor(status_color)
        canvas.roundRect(
            badge_x, badge_y,
            badge_width, badge_height,
            5,  # Corner radius
            fill=1, stroke=0
        )
        
        # Status text (white)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 12)
        text_x = badge_x + badge_width / 2
        text_y = badge_y + 3*mm
        canvas.drawCentredString(text_x, text_y, status)
    
    def _draw_title_section(self, canvas):
        """Draw document title section"""
        y_position = self.height - 80*mm
        
        # Document number (large, prominent)
        canvas.setFillColor(self.PRIMARY_COLOR)
        canvas.setFont('Helvetica-Bold', 24)
        canvas.drawCentredString(
            self.width / 2,
            y_position,
            f"DOCUMENT NUMBER: {self.document.document_number}"
        )
        
        # Version
        y_position -= 10*mm
        canvas.setFont('Helvetica', 12)
        version_text = f"Version v{self.document.version_major:02d}.{self.document.version_minor:02d}"
        canvas.drawCentredString(self.width / 2, y_position, version_text)
        
        # Document title (wrapped if long)
        y_position -= 15*mm
        canvas.setFont('Helvetica-Bold', 16)
        
        # Simple text wrapping for long titles
        title = self.document.title
        if len(title) > 60:
            # Wrap at word boundary
            words = title.split()
            line1 = []
            line2 = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) < 60:
                    line1.append(word)
                    current_length += len(word) + 1
                else:
                    line2.append(word)
            
            canvas.drawCentredString(self.width / 2, y_position, ' '.join(line1))
            y_position -= 7*mm
            canvas.drawCentredString(self.width / 2, y_position, ' '.join(line2))
        else:
            canvas.drawCentredString(self.width / 2, y_position, title)
    
    def _draw_metadata_section(self, canvas):
        """Draw metadata section"""
        y_position = self.height - 140*mm
        x_left = 40*mm
        
        canvas.setFillColor(self.SECONDARY_COLOR)
        canvas.setFont('Helvetica', 11)
        
        # Metadata items
        metadata = [
            ('Effective Date:', self.document.effective_date.strftime('%Y-%m-%d') if self.document.effective_date else 'Not set'),
            ('Approved By:', self._get_approver_name()),
            ('Department:', self.document.author.department if hasattr(self.document.author, 'department') else 'N/A'),
        ]
        
        # Add next review date if exists
        if hasattr(self.document, 'next_review_date') and self.document.next_review_date:
            metadata.append(('Next Review:', self.document.next_review_date.strftime('%Y-%m-%d')))
        
        # Add sensitivity label if not PUBLIC
        if hasattr(self.document, 'sensitivity_label') and self.document.sensitivity_label and self.document.sensitivity_label != 'PUBLIC':
            metadata.append(('Classification:', self.document.sensitivity_label))
        
        # Draw metadata items
        line_height = 8*mm
        for label, value in metadata:
            canvas.setFont('Helvetica-Bold', 11)
            canvas.drawString(x_left, y_position, label)
            
            canvas.setFont('Helvetica', 11)
            canvas.drawString(x_left + 50*mm, y_position, value)
            
            y_position -= line_height
    
    def _draw_footer(self, canvas):
        """Draw footer"""
        y_position = 30*mm
        
        canvas.setFillColor(self.SECONDARY_COLOR)
        canvas.setFont('Helvetica', 9)
        
        # Generated by EDMS
        canvas.drawCentredString(
            self.width / 2,
            y_position,
            'Generated by Electronic Document Management System'
        )
        
        # Timestamp
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        canvas.drawCentredString(
            self.width / 2,
            y_position - 5*mm,
            f'Generated: {timestamp}'
        )
        
        # Page number (roman numeral i)
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(
            self.width / 2,
            15*mm,
            'Page i'
        )
    
    def _get_approver_name(self) -> str:
        """
        Get approver name from document workflow
        
        Returns:
            str: Approver name with role
        """
        try:
            # Get latest approval from workflow
            if hasattr(self.document, 'workflow') and self.document.workflow:
                # This will be implemented when integrating with workflow
                # For now, return author
                pass
            
            # Fallback to author
            author = self.document.author
            role = 'Author'
            
            # Try to get user's role
            if hasattr(author, 'userrole_set'):
                user_roles = author.userrole_set.filter(is_active=True)
                if user_roles.exists():
                    role = user_roles.first().role.role_name
            
            return f"{author.get_full_name() or author.username} ({role})"
            
        except Exception as e:
            print(f"Warning: Could not get approver: {e}")
            return "N/A"
