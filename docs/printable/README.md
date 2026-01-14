# EDMS Printable Documentation

This folder contains PDF-friendly versions of EDMS documentation optimized for printing.

## Available Documents

### User Guides
- **EDMS_USER_GUIDE_PRINTABLE.md** - Complete user manual (PDF-friendly)
- **EDMS_QUICK_REFERENCE_PRINTABLE.md** - One-page reference card
- **EDMS_WORKFLOW_GUIDE_PRINTABLE.md** - Workflow visual guide

### Technical Documentation
- **EDMS_ADMIN_GUIDE_PRINTABLE.md** - Administrator guide
- **EDMS_TECHNICAL_REFERENCE_PRINTABLE.md** - Developer reference

## How to Generate PDFs

### Using Pandoc (Recommended)

```bash
# Install pandoc
sudo apt-get install pandoc  # Linux
brew install pandoc          # Mac

# Generate PDF
pandoc EDMS_USER_GUIDE_PRINTABLE.md -o EDMS_USER_GUIDE.pdf \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=2 \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V papersize=letter
```

### Using Markdown to PDF Converter

Many online converters available:
- https://www.markdowntopdf.com/
- https://md2pdf.netlify.app/
- GitHub Actions (see `.github/workflows/generate-docs.yml`)

### Using VS Code Extension

1. Install "Markdown PDF" extension
2. Open markdown file
3. Right-click → "Markdown PDF: Export (pdf)"

## Print Settings

- **Paper Size**: Letter (8.5" x 11") or A4
- **Margins**: 1 inch all sides
- **Font Size**: 11pt
- **Orientation**: Portrait
- **Color**: Color or B&W (both work)

## Document Versions

- **Version**: 1.0
- **Last Updated**: January 2026
- **Maintained By**: EDMS Development Team
