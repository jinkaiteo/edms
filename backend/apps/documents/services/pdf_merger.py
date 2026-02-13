"""
Enhanced PDF Merger
Merges cover page, content, and appendix with proper page numbering
"""
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from PyPDF2.generic import NameObject, NumberObject, ArrayObject, DictionaryObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import os


class EnhancedPDFMerger:
    """
    Merges PDFs and adds page numbers
    
    Page Numbering:
    - Cover: "Page i"
    - Content: "Page 1 of N", "Page 2 of N", ...
    - Appendix: "Page A-1 of A-X", "Page A-2 of A-X", ...
    """
    
    def __init__(self):
        self.buffer = BytesIO()
    
    def merge_with_cover_and_appendix(
        self,
        cover_pdf_bytes: bytes,
        content_pdf_bytes: bytes,
        appendix_pdf_bytes: bytes
    ) -> bytes:
        """
        Merge three PDFs with page numbering
        
        Args:
            cover_pdf_bytes: Cover page PDF
            content_pdf_bytes: Original document content PDF
            appendix_pdf_bytes: Version history appendix PDF
            
        Returns:
            bytes: Merged PDF with page numbers
        """
        # Create PdfWriter for output
        output = PdfWriter()
        
        # Read all PDFs
        cover_pdf = PdfReader(BytesIO(cover_pdf_bytes))
        content_pdf = PdfReader(BytesIO(content_pdf_bytes))
        appendix_pdf = PdfReader(BytesIO(appendix_pdf_bytes))
        
        # Get page counts
        cover_pages = len(cover_pdf.pages)
        content_pages = len(content_pdf.pages)
        appendix_pages = len(appendix_pdf.pages)
        
        print(f"Merging PDFs: Cover={cover_pages}, Content={content_pages}, Appendix={appendix_pages}")
        
        # Add cover page with page number "i"
        for i in range(cover_pages):
            page = cover_pdf.pages[i]
            # Cover already has "Page i" from generator, just add it
            output.add_page(page)
        
        # Add content pages with page numbers "1 of N", "2 of N", etc.
        for i in range(content_pages):
            page = content_pdf.pages[i]
            page_num = i + 1
            
            # Add page number overlay
            page_with_number = self._add_page_number_overlay(
                page,
                f"Page {page_num} of {content_pages}"
            )
            output.add_page(page_with_number)
        
        # Add appendix pages (already have "Page A-1", "Page A-2" from generator)
        for i in range(appendix_pages):
            page = appendix_pdf.pages[i]
            output.add_page(page)
        
        # Write to buffer
        output.write(self.buffer)
        
        # Get merged PDF bytes
        merged_pdf = self.buffer.getvalue()
        self.buffer.close()
        
        return merged_pdf
    
    def _add_page_number_overlay(self, page, page_text: str):
        """
        Add page number overlay to a PDF page
        
        Args:
            page: PyPDF2 page object
            page_text: Text to display (e.g., "Page 1 of 10")
            
        Returns:
            Modified page with page number
        """
        # Create overlay with page number
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # Draw page number at bottom center
        width, height = A4
        can.setFont('Helvetica', 10)
        can.drawCentredString(
            width / 2,
            15,  # 15 points from bottom
            page_text
        )
        can.save()
        
        # Read overlay PDF
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]
        
        # Merge overlay onto original page
        page.merge_page(overlay_page)
        
        return page
    
    def merge_two_pdfs(self, pdf1_bytes: bytes, pdf2_bytes: bytes) -> bytes:
        """
        Simple merge of two PDFs (utility method)
        
        Args:
            pdf1_bytes: First PDF
            pdf2_bytes: Second PDF
            
        Returns:
            bytes: Merged PDF
        """
        merger = PdfMerger()
        merger.append(BytesIO(pdf1_bytes))
        merger.append(BytesIO(pdf2_bytes))
        
        output = BytesIO()
        merger.write(output)
        merger.close()
        
        merged_pdf = output.getvalue()
        output.close()
        
        return merged_pdf
