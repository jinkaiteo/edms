#!/bin/bash
################################################################################
# PDF Generation Script for EDMS Documentation
################################################################################
# This script converts markdown documentation to PDF format
# Requires: pandoc, xelatex (texlive-xetex)
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Output directory
OUTPUT_DIR="docs/printable/pdf"
SOURCE_DIR="docs/printable"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

################################################################################
# Check Dependencies
################################################################################

check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check for pandoc
    if command -v pandoc &> /dev/null; then
        PANDOC_VERSION=$(pandoc --version | head -n1)
        print_success "Pandoc found: $PANDOC_VERSION"
    else
        print_error "Pandoc not found"
        print_info "Install: sudo apt-get install pandoc (Linux) or brew install pandoc (Mac)"
        exit 1
    fi
    
    # Check for xelatex
    if command -v xelatex &> /dev/null; then
        print_success "XeLaTeX found"
    else
        print_warning "XeLaTeX not found - will try pdflatex"
        if command -v pdflatex &> /dev/null; then
            print_success "PDFLaTeX found"
            PDF_ENGINE="pdflatex"
        else
            print_error "No LaTeX engine found"
            print_info "Install: sudo apt-get install texlive-xetex (Linux)"
            exit 1
        fi
    fi
}

################################################################################
# Create Output Directory
################################################################################

setup_output_dir() {
    print_header "Setting Up Output Directory"
    
    mkdir -p "$OUTPUT_DIR"
    print_success "Output directory created: $OUTPUT_DIR"
}

################################################################################
# Generate PDFs
################################################################################

generate_pdf() {
    local source_file=$1
    local output_name=$2
    local title=$3
    
    print_info "Generating: $output_name"
    
    pandoc "$SOURCE_DIR/$source_file" \
        -o "$OUTPUT_DIR/$output_name" \
        --pdf-engine=xelatex \
        --toc \
        --toc-depth=2 \
        -V geometry:margin=1in \
        -V fontsize=11pt \
        -V papersize=letter \
        -V colorlinks=true \
        -V linkcolor=blue \
        -V urlcolor=blue \
        -V toccolor=black \
        --metadata title="$title" \
        --metadata date="$(date '+%B %Y')" \
        2>&1 | grep -v "Warning" || true
    
    if [ -f "$OUTPUT_DIR/$output_name" ]; then
        local size=$(du -h "$OUTPUT_DIR/$output_name" | cut -f1)
        print_success "Created: $output_name ($size)"
    else
        print_error "Failed to create: $output_name"
        return 1
    fi
}

################################################################################
# Main Process
################################################################################

main() {
    print_header "EDMS Documentation PDF Generator"
    
    # Check dependencies
    check_dependencies
    
    # Setup output directory
    setup_output_dir
    
    # Generate PDFs
    print_header "Generating PDF Documents"
    
    # Quick Reference Card
    if [ -f "$SOURCE_DIR/EDMS_QUICK_REFERENCE_PRINTABLE.md" ]; then
        generate_pdf \
            "EDMS_QUICK_REFERENCE_PRINTABLE.md" \
            "EDMS_Quick_Reference_Card.pdf" \
            "EDMS Quick Reference Guide"
    fi
    
    # User Guide (from root)
    if [ -f "EDMS_USER_GUIDE.md" ]; then
        print_info "Generating: EDMS_User_Guide.pdf"
        pandoc "EDMS_USER_GUIDE.md" \
            -o "$OUTPUT_DIR/EDMS_User_Guide.pdf" \
            --pdf-engine=xelatex \
            --toc \
            --toc-depth=3 \
            -V geometry:margin=1in \
            -V fontsize=11pt \
            -V papersize=letter \
            -V colorlinks=true \
            -V linkcolor=blue \
            --metadata title="EDMS User Guide" \
            --metadata date="$(date '+%B %Y')" \
            2>&1 | grep -v "Warning" || true
        
        if [ -f "$OUTPUT_DIR/EDMS_User_Guide.pdf" ]; then
            local size=$(du -h "$OUTPUT_DIR/EDMS_User_Guide.pdf" | cut -f1)
            print_success "Created: EDMS_User_Guide.pdf ($size)"
        fi
    fi
    
    # Workflow Guides (from root)
    if [ -f "EDMS_WORKFLOWS_EXPLAINED.md" ]; then
        print_info "Generating: EDMS_Workflows_Guide.pdf"
        pandoc "EDMS_WORKFLOWS_EXPLAINED.md" \
            -o "$OUTPUT_DIR/EDMS_Workflows_Guide.pdf" \
            --pdf-engine=xelatex \
            --toc \
            --toc-depth=2 \
            -V geometry:margin=1in \
            -V fontsize=11pt \
            -V papersize=letter \
            -V colorlinks=true \
            --metadata title="EDMS Workflows Guide" \
            --metadata date="$(date '+%B %Y')" \
            2>&1 | grep -v "Warning" || true
        
        if [ -f "$OUTPUT_DIR/EDMS_Workflows_Guide.pdf" ]; then
            local size=$(du -h "$OUTPUT_DIR/EDMS_Workflows_Guide.pdf" | cut -f1)
            print_success "Created: EDMS_Workflows_Guide.pdf ($size)"
        fi
    fi
    
    # Technical Reference
    if [ -f "EDMS_WORKFLOWS_EXPLAINED_PART2.md" ]; then
        print_info "Generating: EDMS_Technical_Reference.pdf"
        pandoc "EDMS_WORKFLOWS_EXPLAINED_PART2.md" \
            -o "$OUTPUT_DIR/EDMS_Technical_Reference.pdf" \
            --pdf-engine=xelatex \
            --toc \
            --toc-depth=2 \
            -V geometry:margin=1in \
            -V fontsize=10pt \
            -V papersize=letter \
            -V colorlinks=true \
            --metadata title="EDMS Technical Reference" \
            --metadata date="$(date '+%B %Y')" \
            2>&1 | grep -v "Warning" || true
        
        if [ -f "$OUTPUT_DIR/EDMS_Technical_Reference.pdf" ]; then
            local size=$(du -h "$OUTPUT_DIR/EDMS_Technical_Reference.pdf" | cut -f1)
            print_success "Created: EDMS_Technical_Reference.pdf ($size)"
        fi
    fi
    
    # Summary
    print_header "PDF Generation Complete"
    
    echo "Generated PDFs:"
    ls -lh "$OUTPUT_DIR" | tail -n +2 | awk '{print "  - " $9 " (" $5 ")"}'
    
    echo ""
    print_info "PDFs saved to: $OUTPUT_DIR"
    print_info "Total files: $(ls -1 $OUTPUT_DIR/*.pdf 2>/dev/null | wc -l)"
    
    # Calculate total size
    total_size=$(du -sh "$OUTPUT_DIR" | cut -f1)
    print_info "Total size: $total_size"
    
    echo ""
    print_success "All PDFs generated successfully!"
}

################################################################################
# Run
################################################################################

main "$@"
