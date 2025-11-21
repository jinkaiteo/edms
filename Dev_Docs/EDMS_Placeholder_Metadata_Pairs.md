# EDMS Placeholder and Metadata Pairs

This document defines the placeholder text patterns and their corresponding metadata mappings for automated replacement in EDMS documents using python-docx-template and document processing.

## Placeholder Format Convention

Placeholders use the format: `{{PLACEHOLDER_NAME}}` or `[PLACEHOLDER_NAME]`

## Core Document Information Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{DOC_NUMBER}}` | Document Number | Auto-generated unique identifier | DOC-2024-001 |
| `{{DOC_VERSION}}` | Version Number | Major.minor version format | 1.2 |
| `{{DOC_TITLE}}` | Document Title | User-defined document title | Quality Management System Manual |
| `{{DOC_TYPE}}` | Document Type | Document category | Standard Operating Procedure |
| `{{DOC_SOURCE}}` | Document Source | Origin classification | Original Digital Draft |
| `{{DOC_DESCRIPTION}}` | Description | Document description/summary | This document describes the quality management procedures |

## Workflow and People Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{AUTHOR_NAME}}` | Author | Document creator full name | David Brown |
| `{{AUTHOR_EMAIL}}` | Author Email | Document creator email | david.brown@company.com |
| `{{REVIEWER_NAME}}` | Reviewer | Document reviewer full name | Henry Taylor |
| `{{REVIEWER_EMAIL}}` | Reviewer Email | Document reviewer email | henry.taylor@company.com |
| `{{APPROVER_NAME}}` | Approver | Document approver full name | Karen White |
| `{{APPROVER_EMAIL}}` | Approver Email | Document approver email | karen.white@company.com |

## Date and Time Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{APPROVAL_DATE}}` | Approval Date | When document was approved | 2024-01-15 |
| `{{APPROVAL_DATE_LONG}}` | Approval Date | Formatted approval date | January 15, 2024 |
| `{{EFFECTIVE_DATE}}` | Effective Date | When document becomes effective | 2024-01-20 |
| `{{EFFECTIVE_DATE_LONG}}` | Effective Date | Formatted effective date | January 20, 2024 |
| `{{DOWNLOAD_DATE}}` | Download Date | When document was downloaded | 2024-01-25 |
| `{{DOWNLOAD_DATE_LONG}}` | Download Date | Formatted download date | January 25, 2024 |
| `{{DOWNLOAD_TIME}}` | Download Date | Download timestamp | 2024-01-25 14:30:15 |
| `{{CREATED_DATE}}` | Created At | Document creation date | 2024-01-10 |
| `{{UPDATED_DATE}}` | Updated At | Last modification date | 2024-01-18 |

## Status and Control Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{DOC_STATUS}}` | Document Status | Current workflow state | Approved and Effective |
| `{{DOC_STATUS_SHORT}}` | Document Status | Abbreviated status | APPROVED |
| `{{IS_CURRENT}}` | Document Status | Current version indicator | CURRENT |
| `{{FILE_CHECKSUM}}` | File Checksum | SHA-256 hash for integrity | a1b2c3d4e5f6... |

## Dependencies and Relationships Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{DEPENDENCIES}}` | Document Dependencies | List of dependent documents | DOC-2024-002, DOC-2024-003 |
| `{{DEPENDENCY_COUNT}}` | Document Dependencies | Number of dependencies | 3 |
| `{{SUPERSEDES}}` | Previous Version | Document this version replaces | DOC-2024-001 v1.1 |

## Technical Information Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{DOC_UUID}}` | UUID | Unique database identifier | 550e8400-e29b-41d4-a716-446655440000 |
| `{{FILE_PATH}}` | File Path | Storage location | /documents/2024/DOC-2024-001.docx |
| `{{FILE_NAME}}` | File Path | Original filename | Quality_Manual_v1.2.docx |

## Revision History Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{REVISION_HISTORY}}` | Revision History | Complete version history | v1.0: Initial release<br>v1.1: Updated procedures<br>v1.2: Added appendix |
| `{{REVISION_COUNT}}` | Revision History | Number of revisions | 3 |
| `{{PREVIOUS_VERSION}}` | Version Number | Previous version number | 1.1 |

## Advanced Date/Time Formatting Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{CURRENT_DATE}}` | System Date | Today's date | 2024-01-25 |
| `{{CURRENT_DATE_LONG}}` | System Date | Today's date formatted | January 25, 2024 |
| `{{CURRENT_TIME}}` | System Time | Current time | 14:30:15 |
| `{{CURRENT_DATETIME}}` | System DateTime | Current date and time | 2024-01-25 14:30:15 |
| `{{CURRENT_YEAR}}` | System Date | Current year | 2024 |

## Conditional Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{IF_APPROVED}}` | Document Status | Show text if approved | APPROVED DOCUMENT |
| `{{IF_DRAFT}}` | Document Status | Show text if in draft | DRAFT - NOT FOR USE |
| `{{IF_OBSOLETE}}` | Document Status | Show text if obsolete | OBSOLETE - DO NOT USE |

## Company/System Information Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{COMPANY_NAME}}` | System Setting | Company name | Acme Pharmaceuticals Inc. |
| `{{SYSTEM_NAME}}` | System Setting | EDMS system name | Electronic Document Management System |
| `{{FOOTER_TEXT}}` | System Setting | Standard footer | This document is controlled. Printed copies are uncontrolled. |

## Header/Footer Template Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{HEADER_LEFT}}` | Combined | Left header content | DOC-2024-001 v1.2 |
| `{{HEADER_CENTER}}` | Document Title | Center header content | Quality Management System Manual |
| `{{HEADER_RIGHT}}` | Download Date | Right header content | Downloaded: 2024-01-25 |
| `{{FOOTER_LEFT}}` | Document Status | Left footer content | APPROVED AND EFFECTIVE |
| `{{FOOTER_CENTER}}` | Company Name | Center footer content | Acme Pharmaceuticals Inc. |
| `{{FOOTER_RIGHT}}` | Page Info | Right footer content | Page {{PAGE}} of {{TOTAL_PAGES}} |

## Custom JSONB Metadata Placeholders

| Placeholder | Metadata Field | Description | Example Output |
|-------------|----------------|-------------|----------------|
| `{{CUSTOM_FIELD_1}}` | Metadata JSONB | Custom field from JSON | Custom Value 1 |
| `{{DEPARTMENT}}` | Metadata JSONB | Department information | Quality Assurance |
| `{{LOCATION}}` | Metadata JSONB | Document location/site | Manufacturing Site A |
| `{{CLASSIFICATION}}` | Metadata JSONB | Security classification | Confidential |

## Implementation Notes

### For .docx Files (python-docx-template)
- Use double braces: `{{PLACEHOLDER_NAME}}`
- Supports conditional logic: `{% if condition %}...{% endif %}`
- Supports loops: `{% for item in list %}...{% endfor %}`

### For PDF Generation
- Placeholders replaced before PDF conversion
- Maintain formatting during replacement
- Digital signature applied after replacement

### For Text Files
- Simple string replacement
- Metadata exported as separate text file
- Key-value pair format

### Configuration Management
- Placeholder definitions stored in S6 Placeholder Management module
- Administrators can add/modify placeholders
- Version control for placeholder definitions
- Validation rules for placeholder syntax

## Security Considerations

- Sensitive metadata (checksums, UUIDs) only in internal documents
- User information filtered based on permissions
- Audit trail for placeholder usage
- Validation of placeholder syntax before processing

This placeholder system enables dynamic document generation while maintaining compliance with 21 CFR Part 11 and ALCOA principles.