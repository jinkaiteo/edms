# How to Generate PDF Documentation

## Overview

This guide explains how to convert EDMS markdown documentation into PDF format for printing and distribution.

---

## Quick Start

### Using the Automated Script (Recommended)

```bash
# From the project root directory
./scripts/generate-pdfs.sh
```

**What it does:**
- Checks for required dependencies
- Creates output directory
- Generates all PDFs automatically
- Shows summary of created files

**Output location:** `docs/printable/pdf/`

---

## Prerequisites

### Linux (Ubuntu/Debian)

```bash
# Install Pandoc
sudo apt-get update
sudo apt-get install pandoc

# Install LaTeX (for PDF generation)
sudo apt-get install texlive-xetex texlive-fonts-recommended texlive-fonts-extra

# Verify installation
pandoc --version
xelatex --version
```

### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Pandoc
brew install pandoc

# Install MacTeX (large download ~4GB)
brew install --cask mactex

# Or install BasicTeX (smaller, ~100MB)
brew install --cask basictex

# Verify installation
pandoc --version
xelatex --version
```

### Windows

1. **Install Pandoc**:
   - Download from: https://pandoc.org/installing.html
   - Run installer
   - Add to PATH

2. **Install MiKTeX** (LaTeX):
   - Download from: https://miktex.org/download
   - Run installer
   - Choose "Install missing packages automatically"

3. **Verify installation**:
   ```cmd
   pandoc --version
   xelatex --version
   ```

---

## Manual PDF Generation

### Method 1: Command Line (Individual Files)

#### Generate Quick Reference Card

```bash
pandoc docs/printable/EDMS_QUICK_REFERENCE_PRINTABLE.md \
  -o docs/printable/pdf/EDMS_Quick_Reference_Card.pdf \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=2 \
  -V geometry:margin=0.75in \
  -V fontsize=10pt \
  -V papersize=letter \
  -V colorlinks=true \
  -V linkcolor=blue \
  --metadata title="EDMS Quick Reference Guide"
```

#### Generate User Guide

```bash
pandoc EDMS_USER_GUIDE.md \
  -o docs/printable/pdf/EDMS_User_Guide.pdf \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=3 \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V papersize=letter \
  -V colorlinks=true \
  --metadata title="EDMS User Guide"
```

#### Generate Workflow Guide

```bash
pandoc EDMS_WORKFLOWS_EXPLAINED.md \
  -o docs/printable/pdf/EDMS_Workflows_Guide.pdf \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=2 \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V papersize=letter \
  -V colorlinks=true \
  --metadata title="EDMS Workflows Guide"
```

#### Generate Technical Reference

```bash
pandoc EDMS_WORKFLOWS_EXPLAINED_PART2.md \
  -o docs/printable/pdf/EDMS_Technical_Reference.pdf \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=2 \
  -V geometry:margin=1in \
  -V fontsize=10pt \
  -V papersize=letter \
  -V colorlinks=true \
  --metadata title="EDMS Technical Reference"
```

---

### Method 2: VS Code Extension

1. **Install Extension**:
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "Markdown PDF"
   - Install by "yzane"

2. **Generate PDF**:
   - Open markdown file
   - Press Ctrl+Shift+P
   - Type "Markdown PDF: Export (pdf)"
   - Select it
   - PDF created in same directory

**Settings** (Optional):
```json
{
  "markdown-pdf.format": "Letter",
  "markdown-pdf.margin.top": "1in",
  "markdown-pdf.margin.bottom": "1in",
  "markdown-pdf.margin.left": "1in",
  "markdown-pdf.margin.right": "1in"
}
```

---

### Method 3: Online Converters

**For quick conversions without installing software:**

#### Option A: Markdown to PDF
1. Go to: https://www.markdowntopdf.com/
2. Upload markdown file or paste content
3. Click "Convert"
4. Download PDF

#### Option B: Dillinger
1. Go to: https://dillinger.io/
2. Paste markdown content
3. Click "Export as" → "PDF"
4. Save file

#### Option C: Markdown PDF
1. Go to: https://md2pdf.netlify.app/
2. Paste markdown or upload file
3. Configure settings
4. Generate and download

**Note**: Online converters may not preserve all formatting. Use automated script for best results.

---

## Customization Options

### Page Size

```bash
# Letter (8.5" x 11")
-V papersize=letter

# A4 (210mm x 297mm)
-V papersize=a4

# Legal (8.5" x 14")
-V papersize=legal
```

### Margins

```bash
# All sides 1 inch
-V geometry:margin=1in

# Custom margins
-V geometry:top=1in,bottom=1in,left=1.25in,right=1.25in

# Narrow margins
-V geometry:margin=0.5in
```

### Font Size

```bash
# Small
-V fontsize=10pt

# Normal
-V fontsize=11pt

# Large
-V fontsize=12pt
```

### Colors

```bash
# Colored links
-V colorlinks=true
-V linkcolor=blue
-V urlcolor=blue

# Black and white (for B&W printers)
-V colorlinks=false
```

### Table of Contents

```bash
# Include TOC
--toc

# TOC depth (1-6)
--toc-depth=2

# No TOC
# (omit --toc flag)
```

---

## PDF Settings for Different Uses

### For Screen Viewing

```bash
pandoc input.md -o output.pdf \
  --pdf-engine=xelatex \
  --toc \
  -V colorlinks=true \
  -V linkcolor=blue \
  -V fontsize=11pt \
  -V papersize=letter
```

### For B&W Printing

```bash
pandoc input.md -o output.pdf \
  --pdf-engine=xelatex \
  --toc \
  -V colorlinks=false \
  -V fontsize=11pt \
  -V papersize=letter \
  -V geometry:margin=1in
```

### For Mobile Reading

```bash
pandoc input.md -o output.pdf \
  --pdf-engine=xelatex \
  -V fontsize=12pt \
  -V papersize=a5 \
  -V geometry:margin=0.5in
```

### For Presentation Handouts

```bash
pandoc input.md -o output.pdf \
  --pdf-engine=xelatex \
  --toc \
  -V fontsize=10pt \
  -V papersize=letter \
  -V geometry:margin=0.75in
```

---

## Troubleshooting

### Error: "pandoc: command not found"

**Solution**: Install Pandoc (see Prerequisites section)

### Error: "xelatex not found"

**Solution**: Install LaTeX distribution
- Linux: `sudo apt-get install texlive-xetex`
- Mac: `brew install --cask mactex`
- Windows: Install MiKTeX

### Error: "Package X not found"

**Solution**: Install missing LaTeX packages
```bash
# Ubuntu/Debian
sudo apt-get install texlive-fonts-extra

# MiKTeX (Windows)
# Packages install automatically when needed
```

### PDF has broken formatting

**Solution**: Use XeLaTeX instead of PDFLaTeX
```bash
--pdf-engine=xelatex
```

### Unicode characters not displaying

**Solution**: Use XeLaTeX and ensure UTF-8 encoding
```bash
--pdf-engine=xelatex
-V mainfont="DejaVu Sans"
```

### Images not appearing

**Solution**: Ensure image paths are correct
- Use relative paths
- Check image files exist
- Verify image formats (PNG, JPG supported)

### Table formatting issues

**Solution**: Pandoc has limitations with complex tables
- Simplify table structure
- Consider using HTML tables in markdown
- Use `--columns=80` flag

---

## Batch Processing

### Generate All PDFs at Once

```bash
#!/bin/bash
# Save as batch-generate.sh

mkdir -p docs/printable/pdf

# List of files to convert
files=(
  "EDMS_USER_GUIDE.md"
  "EDMS_WORKFLOWS_EXPLAINED.md"
  "EDMS_WORKFLOWS_EXPLAINED_PART2.md"
  "EDMS_QUICK_REFERENCE_CARD.md"
)

# Convert each file
for file in "${files[@]}"; do
  basename="${file%.md}"
  echo "Converting $file..."
  pandoc "$file" -o "docs/printable/pdf/${basename}.pdf" \
    --pdf-engine=xelatex \
    --toc \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V papersize=letter
done

echo "Done! PDFs created in docs/printable/pdf/"
```

```bash
chmod +x batch-generate.sh
./batch-generate.sh
```

---

## Distribution

### For Internal Use

1. Generate PDFs using script
2. Upload to internal documentation server
3. Share links with team
4. Or email PDFs directly

### For External Distribution

1. Generate PDFs
2. Review for sensitive information
3. Add watermarks if needed
4. Distribute via secure channels

### For Training Sessions

1. Generate PDFs
2. Print required copies
3. Or share digitally before session
4. Provide as handouts

---

## Updating PDFs

### When to Regenerate

- After updating markdown documentation
- When releasing new version
- Before training sessions
- Quarterly review cycle

### Version Control

Include version information:
```markdown
**Version**: 1.0
**Date**: January 2026
**Status**: Approved
```

### Automation

Set up GitHub Action to auto-generate:
```yaml
# .github/workflows/generate-pdfs.yml
name: Generate PDFs
on:
  push:
    paths:
      - '*.md'
      - 'docs/printable/*.md'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Pandoc
        run: |
          sudo apt-get update
          sudo apt-get install pandoc texlive-xetex
      - name: Generate PDFs
        run: ./scripts/generate-pdfs.sh
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: pdfs
          path: docs/printable/pdf/
```

---

## Best Practices

### Do ✓

- Generate PDFs before each release
- Test print one copy before bulk printing
- Keep source markdown and PDFs in sync
- Version control generated PDFs
- Include metadata (date, version) in PDFs

### Don't ✗

- Edit PDFs directly (edit markdown instead)
- Print without preview
- Forget to update version numbers
- Skip testing PDF generation
- Ignore formatting issues

---

## Quick Reference

### Generate All PDFs
```bash
./scripts/generate-pdfs.sh
```

### Generate Single PDF
```bash
pandoc input.md -o output.pdf --pdf-engine=xelatex --toc
```

### Check Pandoc Version
```bash
pandoc --version
```

### Test LaTeX Installation
```bash
xelatex --version
```

---

## Support

**Issues with PDF generation?**
- Check Prerequisites section
- Review Troubleshooting section
- Contact IT Support
- Open GitHub issue

**Need custom formatting?**
- Review Customization Options
- Consult Pandoc documentation: https://pandoc.org/
- Contact documentation team

---

**For complete documentation, see the generated PDFs in `docs/printable/pdf/`**
