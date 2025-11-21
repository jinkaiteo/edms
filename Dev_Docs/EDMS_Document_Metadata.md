# EDMS Document Metadata

Based on the EDMS Development Roadmap and Requirements Architecture Setup documentation, here is the comprehensive list of metadata available for documents in the EDMS system:

## Document Metadata Available in the EDMS

### Core Document Information
1. **Document Number** - Auto-generated unique identifier
2. **Version Number** - Format: major.minor (e.g., 1.0, 1.1, 2.0)
3. **Document Title** - User-defined title
4. **Document Type** - Categories include:
   - Policy
   - Manual
   - Procedures
   - Work Instructions (SOP)
   - Forms and Templates
   - Records

5. **Document Source** - Origin classification:
   - Original Digital Draft
   - Scanned Original
   - Scanned Copy

### Workflow & Status Information
6. **Document Dependencies** - References to other approved and effective documents
7. **Author** - Document creator/owner
8. **Reviewer** - Person assigned to review the document
9. **Approver** - Person assigned to approve the document
10. **Approval Date** - When the document was approved
11. **Effective Date** - When the document becomes effective
12. **Document Status** - Current workflow state:
    - DRAFT
    - Pending Review
    - Reviewed
    - Pending Approval
    - Approved, Pending Effective
    - Approved and Effective
    - Superseded
    - Pending Obsoleting
    - Obsolete

### Additional Tracking Information
13. **Download Date** - Timestamp of when document was downloaded
14. **Revision History** - Complete history of document changes and versions

### Technical Metadata (Database Level)
15. **File Path** - Storage location of the document file
16. **File Checksum** - SHA-256 hash for file integrity verification
17. **Metadata JSONB** - Additional flexible metadata stored in JSON format
18. **Created At** - Document creation timestamp
19. **Updated At** - Last modification timestamp
20. **UUID** - Unique identifier for database records

### Placeholder System
The EDMS includes a **Placeholder Management** system (S6 module) that allows administrators to define custom placeholder text that can be automatically replaced with corresponding document metadata when generating annotated documents or official PDFs. This enables dynamic document generation with current metadata values.

## Compliance & Standards
This metadata structure supports the 21 CFR Part 11 compliance requirements and ALCOA principles (Attributable, Legible, Contemporaneous, Original, Accurate) required for pharmaceutical and regulated industries.

## Usage in Document Processing
- **Document Annotation**: Metadata is used to replace placeholders in .docx files using python-docx-template
- **Official PDF Generation**: Metadata is embedded when creating digitally signed official PDFs
- **Audit Trail**: All metadata changes are tracked for compliance purposes
- **Search & Filtering**: PostgreSQL full-text search enables searching across all metadata fields