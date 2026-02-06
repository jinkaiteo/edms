"""
Watermark Processor for Sensitivity Labels and Document Status

Implements dual-layer watermark system:
1. Sensitivity Header Bar (top of page) - for CONFIDENTIAL+
2. Status Diagonal Watermark (center) - for non-EFFECTIVE documents
"""

from typing import Dict, Tuple, Optional
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, HexColor
from PyPDF2 import PdfReader, PdfWriter
import os


class WatermarkProcessor:
    """
    Handles adding watermarks to PDF documents based on sensitivity and status.
    
    Two-layer watermark system:
    - Layer 1: Sensitivity header bar (if CONFIDENTIAL+)
    - Layer 2: Status diagonal watermark (if not EFFECTIVE)
    """
    
    # Sensitivity configuration
    SENSITIVITY_CONFIG = {
        'PUBLIC': {
            'show_header': False,
            'header_text': '',
            'header_color': None,
        },
        'INTERNAL': {
            'show_header': False,  # Optional: set True if you want INTERNAL header
            'header_text': 'INTERNAL USE ONLY',
            'header_color': HexColor('#1e40af'),  # Blue
        },
        'CONFIDENTIAL': {
            'show_header': True,
            'header_text': 'CONFIDENTIAL',
            'header_color': HexColor('#ea580c'),  # Orange
        },
        'RESTRICTED': {
            'show_header': True,
            'header_text': 'RESTRICTED - REGULATORY/COMPLIANCE',
            'header_color': HexColor('#7c3aed'),  # Purple
        },
        'PROPRIETARY': {
            'show_header': True,
            'header_text': 'PROPRIETARY - TRADE SECRET',
            'header_color': HexColor('#dc2626'),  # Red
        },
    }
    
    # Status configuration - MATCHED TO ACTUAL DOCUMENT_STATUS_CHOICES
    STATUS_CONFIG = {
        'DRAFT': {
            'show_watermark': True,
            'watermark_text': 'DRAFT\nNOT FOR USE',
            'watermark_color': HexColor('#ef4444'),  # Red
            'watermark_opacity': 0.2,
        },
        'PENDING_REVIEW': {
            'show_watermark': True,
            'watermark_text': 'PENDING REVIEW',
            'watermark_color': HexColor('#f59e0b'),  # Yellow/Orange
            'watermark_opacity': 0.2,
        },
        'UNDER_REVIEW': {
            'show_watermark': True,
            'watermark_text': 'UNDER REVIEW',
            'watermark_color': HexColor('#f59e0b'),  # Yellow/Orange
            'watermark_opacity': 0.2,
        },
        'REVIEW_COMPLETED': {
            'show_watermark': True,
            'watermark_text': 'REVIEW COMPLETED\nPENDING APPROVAL',
            'watermark_color': HexColor('#10b981'),  # Green
            'watermark_opacity': 0.15,
        },
        'PENDING_APPROVAL': {
            'show_watermark': True,
            'watermark_text': 'PENDING APPROVAL',
            'watermark_color': HexColor('#3b82f6'),  # Blue
            'watermark_opacity': 0.2,
        },
        'UNDER_APPROVAL': {
            'show_watermark': True,
            'watermark_text': 'UNDER APPROVAL',
            'watermark_color': HexColor('#3b82f6'),  # Blue
            'watermark_opacity': 0.2,
        },
        'APPROVED': {
            'show_watermark': True,
            'watermark_text': 'APPROVED\nNOT YET EFFECTIVE',
            'watermark_color': HexColor('#3b82f6'),  # Blue
            'watermark_opacity': 0.15,
        },
        'APPROVED_PENDING_EFFECTIVE': {
            'show_watermark': True,
            'watermark_text': 'APPROVED\nPENDING EFFECTIVE',
            'watermark_color': HexColor('#3b82f6'),  # Blue
            'watermark_opacity': 0.15,
        },
        'EFFECTIVE': {
            'show_watermark': False,
            'watermark_text': '',
            'watermark_color': None,
            'watermark_opacity': 0,
        },
        'SCHEDULED_FOR_OBSOLESCENCE': {
            'show_watermark': True,
            'watermark_text': 'SCHEDULED FOR\nOBSOLESCENCE',
            'watermark_color': HexColor('#f59e0b'),  # Orange
            'watermark_opacity': 0.25,
        },
        'SUPERSEDED': {
            'show_watermark': True,
            'watermark_text': 'SUPERSEDED',
            'watermark_color': HexColor('#6b7280'),  # Gray
            'watermark_opacity': 0.25,
        },
        'OBSOLETE': {
            'show_watermark': True,
            'watermark_text': 'OBSOLETE\nDO NOT USE',
            'watermark_color': HexColor('#6b7280'),  # Gray
            'watermark_opacity': 0.3,
        },
        'TERMINATED': {
            'show_watermark': True,
            'watermark_text': 'TERMINATED',
            'watermark_color': HexColor('#dc2626'),  # Red
            'watermark_opacity': 0.3,
        },
    }
    
    def __init__(self):
        """Initialize watermark processor."""
        self.page_size = letter  # Default to US Letter, can be changed to A4
    
    def add_watermarks_to_pdf(self, input_pdf_path: str, output_pdf_path: str,
                              sensitivity_label: str, document_status: str) -> bool:
        """
        Add dual watermarks to PDF file.
        
        Args:
            input_pdf_path: Path to input PDF
            output_pdf_path: Path to save watermarked PDF
            sensitivity_label: Document sensitivity (PUBLIC, INTERNAL, etc.)
            document_status: Document status (DRAFT, EFFECTIVE, etc.)
            
        Returns:
            bool: True if successful
        """
        try:
            # Read input PDF
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()
            
            # Get configurations
            sensitivity_config = self.SENSITIVITY_CONFIG.get(sensitivity_label, {})
            status_config = self.STATUS_CONFIG.get(document_status, {})
            
            # Process each page
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                
                # Get page size
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)
                
                # Create watermark for this page
                watermark_buffer = self._create_watermark_page(
                    page_width, page_height,
                    sensitivity_config, status_config,
                    page_num + 1, len(reader.pages)
                )
                
                # Merge watermark with page
                if watermark_buffer:
                    watermark_reader = PdfReader(watermark_buffer)
                    watermark_page = watermark_reader.pages[0]
                    page.merge_page(watermark_page)
                
                writer.add_page(page)
            
            # Write output
            with open(output_pdf_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True
            
        except Exception as e:
            print(f"Error adding watermarks to PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_watermark_page(self, page_width: float, page_height: float,
                               sensitivity_config: Dict, status_config: Dict,
                               page_num: int, total_pages: int) -> Optional[BytesIO]:
        """
        Create watermark overlay for a single page.
        
        Args:
            page_width: Page width in points
            page_height: Page height in points
            sensitivity_config: Sensitivity configuration dict
            status_config: Status configuration dict
            page_num: Current page number (1-indexed)
            total_pages: Total number of pages
            
        Returns:
            BytesIO buffer with watermark PDF, or None if no watermark needed
        """
        # Check if any watermark is needed
        show_header = sensitivity_config.get('show_header', False)
        show_status = status_config.get('show_watermark', False)
        
        if not show_header and not show_status:
            return None
        
        # Create PDF buffer
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        
        # Layer 1: Sensitivity Header Bar
        if show_header:
            self._draw_sensitivity_header(
                c, page_width, page_height,
                sensitivity_config['header_text'],
                sensitivity_config['header_color']
            )
        
        # Layer 2: Status Diagonal Watermark
        if show_status:
            self._draw_status_watermark(
                c, page_width, page_height,
                status_config['watermark_text'],
                status_config['watermark_color'],
                status_config['watermark_opacity']
            )
        
        # Add page footer with page numbers (optional)
        # self._draw_footer(c, page_width, page_height, page_num, total_pages)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _draw_sensitivity_header(self, canvas_obj, page_width: float, page_height: float,
                                 header_text: str, header_color: Color):
        """
        Draw sensitivity label header bar at top of page.
        
        Creates a colored bar across the top with white text.
        """
        # Header dimensions
        header_height = 0.4 * inch  # 0.4 inch tall
        
        # Draw colored rectangle at top
        canvas_obj.setFillColor(header_color)
        canvas_obj.rect(0, page_height - header_height, page_width, header_height, fill=1, stroke=0)
        
        # Draw white text centered in header
        canvas_obj.setFillColor(HexColor('#ffffff'))  # White text
        canvas_obj.setFont('Helvetica-Bold', 14)
        
        # Center text horizontally
        text_width = canvas_obj.stringWidth(header_text, 'Helvetica-Bold', 14)
        x = (page_width - text_width) / 2
        y = page_height - header_height / 2 - 5  # Vertically centered with slight adjustment
        
        canvas_obj.drawString(x, y, header_text)
    
    def _draw_status_watermark(self, canvas_obj, page_width: float, page_height: float,
                               watermark_text: str, watermark_color: Color, opacity: float):
        """
        Draw diagonal status watermark in center of page.
        
        Creates a 45-degree rotated watermark across the page center.
        """
        # Save canvas state
        canvas_obj.saveState()
        
        # Set opacity
        canvas_obj.setFillColor(watermark_color)
        canvas_obj.setStrokeColor(watermark_color)
        canvas_obj.setFillAlpha(opacity)
        canvas_obj.setStrokeAlpha(opacity)
        
        # Move to center and rotate 45 degrees
        canvas_obj.translate(page_width / 2, page_height / 2)
        canvas_obj.rotate(45)
        
        # Draw watermark text
        canvas_obj.setFont('Helvetica-Bold', 60)
        
        # Handle multi-line text
        lines = watermark_text.split('\n')
        line_height = 65  # Spacing between lines
        
        # Calculate starting Y position for centered multi-line text
        total_height = len(lines) * line_height
        start_y = total_height / 2
        
        for i, line in enumerate(lines):
            text_width = canvas_obj.stringWidth(line, 'Helvetica-Bold', 60)
            x = -text_width / 2  # Center horizontally
            y = start_y - (i * line_height)
            canvas_obj.drawString(x, y, line)
        
        # Restore canvas state
        canvas_obj.restoreState()
    
    def _draw_footer(self, canvas_obj, page_width: float, page_height: float,
                     page_num: int, total_pages: int):
        """
        Draw footer with page numbers (optional).
        
        Not used by default but available if needed.
        """
        canvas_obj.saveState()
        
        canvas_obj.setFillColor(HexColor('#6b7280'))  # Gray
        canvas_obj.setFont('Helvetica', 8)
        
        footer_text = f"Page {page_num} of {total_pages}"
        text_width = canvas_obj.stringWidth(footer_text, 'Helvetica', 8)
        x = (page_width - text_width) / 2
        y = 0.3 * inch  # 0.3 inch from bottom
        
        canvas_obj.drawString(x, y, footer_text)
        
        canvas_obj.restoreState()
    
    def get_watermark_status(self, sensitivity_label: str, document_status: str) -> Dict[str, any]:
        """
        Get information about what watermarks will be applied.
        
        Args:
            sensitivity_label: Document sensitivity
            document_status: Document status
            
        Returns:
            Dict with watermark configuration info
        """
        sensitivity_config = self.SENSITIVITY_CONFIG.get(sensitivity_label, {})
        status_config = self.STATUS_CONFIG.get(document_status, {})
        
        return {
            'has_sensitivity_header': sensitivity_config.get('show_header', False),
            'sensitivity_header_text': sensitivity_config.get('header_text', ''),
            'has_status_watermark': status_config.get('show_watermark', False),
            'status_watermark_text': status_config.get('watermark_text', '').replace('\n', ' '),
            'requires_watermark': sensitivity_config.get('show_header', False) or status_config.get('show_watermark', False)
        }


# Global instance
watermark_processor = WatermarkProcessor()
