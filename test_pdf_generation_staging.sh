#!/bin/bash

# Test PDF Generation Pipeline on Staging
# Checks if placeholders are replaced in DOCX processing and PDF generation

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  TESTING PDF GENERATION PIPELINE                                 ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.models import Document
from apps.documents.annotation_processor import annotation_processor
from apps.documents.docx_processor import docx_processor
import os

print("=== STEP 1: Find a document with a DOCX file ===")
doc = Document.objects.filter(file_name__iendswith='.docx').first()

if not doc:
    print("❌ No DOCX documents found")
    print("Upload a DOCX document with placeholders to test")
    exit()

print(f"✅ Found document: {doc.document_number}")
print(f"   File: {doc.file_name}")
print(f"   Path: {doc.full_file_path}")
print(f"   File exists: {os.path.exists(doc.full_file_path)}")

print("\n=== STEP 2: Generate metadata ===")
metadata = annotation_processor.get_document_metadata(doc, doc.author)

print(f"✅ Metadata generated: {len(metadata)} keys")
print("\nChecking 5 placeholders in metadata:")
for key in ['DEPARTMENT', 'DIGITAL_SIGNATURE', 'DOWNLOADED_DATE', 'PREVIOUS_VERSION', 'REVISION_COUNT']:
    value = metadata.get(key, 'NOT FOUND')
    if isinstance(value, str):
        value = value[:50] + '...' if len(value) > 50 else value
    print(f"  {key}: {value}")

print("\n=== STEP 3: Test DOCX processing ===")
try:
    processed_file = docx_processor.process_docx_template(doc, doc.author)
    print(f"✅ DOCX processed: {processed_file}")
    print(f"   File exists: {os.path.exists(processed_file)}")
    print(f"   File size: {os.path.getsize(processed_file)} bytes")
    
    # Check if placeholders were replaced
    from docx import Document as DocxDocument
    import re
    
    processed_doc = DocxDocument(processed_file)
    text = '\n'.join([p.text for p in processed_doc.paragraphs])
    
    # Check for unreplaced placeholders
    unreplaced = re.findall(r'\{\{([A-Z_]+)\}\}', text)
    
    if unreplaced:
        print(f"\n❌ Found {len(set(unreplaced))} unreplaced placeholders:")
        for ph in list(set(unreplaced))[:10]:
            print(f"   • {ph}")
    else:
        print("\n✅ All {{PLACEHOLDER}} format replaced")
    
    # Check for the 5 specific values
    print("\n=== Checking if values are in processed DOCX ===")
    checks = {
        'DEPARTMENT': metadata.get('DEPARTMENT', ''),
        'DIGITAL_SIGNATURE': metadata.get('DIGITAL_SIGNATURE', ''),
        'PREVIOUS_VERSION': metadata.get('PREVIOUS_VERSION', ''),
        'REVISION_COUNT': metadata.get('REVISION_COUNT', '')
    }
    
    for name, value in checks.items():
        if value and str(value) in text:
            print(f"✅ {name} value found in DOCX")
        elif value:
            print(f"❌ {name} value NOT in DOCX (value: '{value}')")
        else:
            print(f"⚠️  {name} has empty value")
    
    # Cleanup
    os.unlink(processed_file)
    
except Exception as e:
    print(f"\n❌ DOCX processing failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== STEP 4: Test PDF generation ===")
try:
    from apps.documents.services.pdf_generator import OfficialPDFGenerator
    
    generator = OfficialPDFGenerator()
    pdf_content = generator.generate_official_pdf(doc, doc.author)
    
    print(f"✅ PDF generated: {len(pdf_content):,} bytes")
    
    # Save temporarily to check content
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(pdf_content)
        pdf_path = f.name
    
    print(f"   Saved to: {pdf_path}")
    
    # Try to extract text
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        pdf_text = ''
        for page in reader.pages:
            pdf_text += page.extract_text()
        
        # Check for unreplaced placeholders
        unreplaced_pdf = re.findall(r'\{\{([A-Z_]+)\}\}', pdf_text)
        
        if unreplaced_pdf:
            print(f"\n❌ PDF has {len(set(unreplaced_pdf))} unreplaced placeholders:")
            for ph in list(set(unreplaced_pdf))[:10]:
                print(f"   • {ph}")
        else:
            print("\n✅ PDF has no unreplaced {{PLACEHOLDER}} format")
        
        # Check for specific values
        print("\n=== Checking if values are in PDF ===")
        for name, value in checks.items():
            if value and str(value) in pdf_text:
                print(f"✅ {name} value found in PDF")
            elif value:
                print(f"❌ {name} value NOT in PDF")
        
    except Exception as e:
        print(f"⚠️  Could not extract PDF text: {e}")
    
    # Cleanup
    os.unlink(pdf_path)
    
except Exception as e:
    print(f"\n❌ PDF generation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n╔══════════════════════════════════════════════════════════════════╗")
print("║                                                                  ║")
print("║  TEST COMPLETE                                                   ║")
print("║                                                                  ║")
print("╚══════════════════════════════════════════════════════════════════╝")
PYEOF

