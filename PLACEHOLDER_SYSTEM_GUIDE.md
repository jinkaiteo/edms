# Placeholder System - Complete User Guide

**Last Updated**: December 23, 2025  
**System Version**: EDMS v1.0 with 68 Runtime Placeholders

---

## 📋 Table of Contents

1. [What Are Placeholders?](#what-are-placeholders)
2. [How to Use Placeholders](#how-to-use-placeholders)
3. [Complete Placeholder Reference](#complete-placeholder-reference)
4. [Backward Compatibility & Aliases](#backward-compatibility--aliases)
5. [Download Methods](#download-methods)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 What Are Placeholders?

**Placeholders** are special tags in document templates that get automatically replaced with real document data when you download the document.

### Example

**In your template:**
```
Document Title: {{DOCUMENT_TITLE}}
Author: {{AUTHOR_NAME}}
Effective Date: {{EFFECTIVE_DATE}}
Status: {{WORKFLOW_STATUS}}
```

**After download:**
```
Document Title: Quality Control Procedure
Author: John Doe
Effective Date: 2025-01-15
Status: Effective
```

### Benefits

✅ **No manual data entry** - Placeholders automatically pull current information  
✅ **Always up-to-date** - Data reflects current document state  
✅ **Single template, unlimited documents** - Reuse templates across all documents  
✅ **Professional consistency** - Uniform formatting across all documents  
✅ **Error reduction** - No typos or outdated information  

---

## 📝 How to Use Placeholders

### Step 1: Create a Template

Create a Word document (.docx) with placeholders using double braces:

```
{{PLACEHOLDER_NAME}}
```

**Rules:**
- Use UPPERCASE letters
- Use underscores for spaces: `AUTHOR_NAME` not `AUTHOR NAME`
- Wrap in double braces: `{{` and `}}`
- No spaces inside braces: `{{AUTHOR}}` not `{{ AUTHOR }}`

### Step 2: Upload Template to EDMS

Upload your template as a document in EDMS.

### Step 3: Validate Template (Optional)

Go to **Placeholders** page → **Validate Template** → Upload your .docx file

The validator will:
- ✅ Show all valid placeholders
- ❌ Flag unknown placeholders
- 💡 Suggest corrections for typos
- 📋 Show available placeholders you haven't used

### Step 4: Download with Placeholders Replaced

Two options:

**Option A: Download Annotated** (any status)
- Placeholders replaced
- Original format (.docx)
- Editable for further work

**Option B: Download Official PDF** (approved only)
- Placeholders replaced
- PDF format (not editable)
- Professional watermarks/headers
- Digitally signed

---

## 📚 Complete Placeholder Reference

### 68 Available Placeholders

#### 📄 Document Information (15 placeholders)

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{DOCUMENT_NUMBER}}` | Full document number | PROC-2025-0001-v01.00 |
| `{{DOCUMENT_TITLE}}` | Document title | Quality Control Procedure |
| `{{DOC_NUMBER}}` | Alias for DOCUMENT_NUMBER | PROC-2025-0001-v01.00 |
| `{{DOC_TITLE}}` | Alias for DOCUMENT_TITLE | Quality Control Procedure |
| `{{NUMBER}}` | Short alias for doc number | PROC-2025-0001-v01.00 |
| `{{TITLE}}` | Short alias for doc title | Quality Control Procedure |
| `{{DOC_VERSION}}` | Document version | 1.0 |
| `{{DOC_TYPE}}` | Document type | Policy |
| `{{DOC_SOURCE}}` | Document source | Internal |
| `{{DOC_STATUS}}` | Document status | Effective |
| `{{DOC_DESCRIPTION}}` | Document description | Describes QC process |
| `{{VERSION_MAJOR}}` | Major version number | 1 |
| `{{VERSION_MINOR}}` | Minor version number | 0 |
| `{{VERSION_FULL}}` | Full version string | 1.0 |
| `{{DOC_BASE_NUMBER}}` | Base number without version | PROC-2025-0001 |
| `{{DOC_UUID}}` | Document unique identifier | 7009b4ae-... |

#### 👥 People Information (12 placeholders)

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{AUTHOR_NAME}}` | Document author full name | John Doe |
| `{{AUTHOR}}` | Alias for AUTHOR_NAME | John Doe |
| `{{AUTHOR_EMAIL}}` | Author email address | john.doe@company.com |
| `{{REVIEWER_NAME}}` | Document reviewer full name | Jane Smith |
| `{{REVIEWER}}` | Alias for REVIEWER_NAME | Jane Smith |
| `{{REVIEWER_EMAIL}}` | Reviewer email address | jane.smith@company.com |
| `{{APPROVER_NAME}}` | Document approver full name | Bob Wilson |
| `{{APPROVER}}` | Alias for APPROVER_NAME | Bob Wilson |
| `{{APPROVER_EMAIL}}` | Approver email address | bob.wilson@company.com |
| `{{current_user_name}}` | Person downloading document | Your Name |
| `{{current_user_email}}` | Downloader's email | your.email@company.com |

#### 📅 Date & Time Information (18 placeholders)

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{CREATED_DATE}}` | Document creation date | 2025-01-15 |
| `{{CREATED_DATE_LONG}}` | Creation date (long format) | January 15, 2025 |
| `{{CREATION_DATE}}` | Alias for CREATED_DATE | 2025-01-15 |
| `{{UPDATED_DATE}}` | Last update date | 2025-01-20 |
| `{{MODIFIED_DATE}}` | Alias for UPDATED_DATE | 2025-01-20 |
| `{{LAST_MODIFIED}}` | Last modification date | 2025-01-20 |
| `{{APPROVAL_DATE}}` | Date document was approved | 2025-01-18 |
| `{{APPROVAL_DATE_LONG}}` | Approval date (long format) | January 18, 2025 |
| `{{EFFECTIVE_DATE}}` | Date document becomes effective | 2025-02-01 |
| `{{EFFECTIVE_DATE_LONG}}` | Effective date (long format) | February 1, 2025 |
| `{{DOWNLOAD_DATE}}` | Date of download | 2025-12-23 |
| `{{DOWNLOAD_DATE_LONG}}` | Download date (long format) | December 23, 2025 |
| `{{DOWNLOAD_TIME}}` | Time of download | 14:30:00 |
| `{{CURRENT_DATE}}` | Current date (same as download) | 2025-12-23 |
| `{{CURRENT_DATE_LONG}}` | Current date (long format) | December 23, 2025 |
| `{{CURRENT_TIME}}` | Current time | 14:30:00 |
| `{{CURRENT_DATETIME}}` | Current date and time | 2025-12-23 14:30:00 |
| `{{CURRENT_YEAR}}` | Current year | 2025 |

#### 🔄 Status & Workflow (4 placeholders)

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{WORKFLOW_STATUS}}` | Current workflow state | Under Review |
| `{{DOC_STATUS}}` | Document status | Approved |
| `{{DOC_STATUS_SHORT}}` | Status code | APPROVED |
| `{{STATUS}}` | Alias for DOC_STATUS | Approved |
| `{{IS_CURRENT}}` | Is this the current version? | True |

#### 📁 File Information (5 placeholders)

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{FILE_NAME}}` | Original file name | quality_procedure.docx |
| `{{FILE_PATH}}` | File storage path | documents/uuid.docx |
| `{{FILE_SIZE}}` | File size in bytes | 124263 |
| `{{FILE_CHECKSUM}}` | File integrity checksum | 8bfcc6a9... |

#### 🏢 System Information (4 placeholders)

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{COMPANY_NAME}}` | Your company name | Your Company |
| `{{ORGANIZATION}}` | Alias for company name | Your Company |
| `{{COMPANY}}` | Short alias | Your Company |
| `{{SYSTEM_NAME}}` | EDMS system name | Electronic Document Management System |

#### ⚙️ Conditional Placeholders (3 placeholders)

| Placeholder | Description | Output When True |
|-------------|-------------|------------------|
| `{{IF_APPROVED}}` | Shows text if approved | APPROVED DOCUMENT |
| `{{IF_DRAFT}}` | Shows text if draft | DRAFT - NOT FOR USE |
| `{{IF_EFFECTIVE}}` | Shows text if effective | OFFICIAL DOCUMENT |

#### 📊 Special Placeholders (2 placeholders)

| Placeholder | Description | Output |
|-------------|-------------|--------|
| `{{VERSION_HISTORY}}` | Creates version history table | Formatted table with all versions |
| `{{VERSION_HISTORY_TABLE_DATA}}` | Raw version history data | Data for custom table formatting |

---

## 🔄 Backward Compatibility & Aliases

Many placeholders have **multiple names** that work interchangeably. This allows old templates to continue working while providing clearer names for new templates.

### People Placeholders

| Primary (Database) | Alias (Runtime) | Both Work? |
|--------------------|-----------------|------------|
| `{{AUTHOR}}` | `{{AUTHOR_NAME}}` | ✅ Yes |
| `{{REVIEWER}}` | `{{REVIEWER_NAME}}` | ✅ Yes |
| `{{APPROVER}}` | `{{APPROVER_NAME}}` | ✅ Yes |

**Recommendation**: Use `_NAME` versions for new templates (more descriptive).

### Document Placeholders

| Primary | Aliases | Recommendation |
|---------|---------|----------------|
| `{{DOCUMENT_NUMBER}}` | `{{DOC_NUMBER}}`, `{{NUMBER}}` | Use DOC_NUMBER (balanced) |
| `{{DOCUMENT_TITLE}}` | `{{DOC_TITLE}}`, `{{TITLE}}` | Use DOC_TITLE (balanced) |
| `{{DOCUMENT_STATUS}}` | `{{DOC_STATUS}}`, `{{STATUS}}` | Use DOC_STATUS (balanced) |
| `{{VERSION_FULL}}` | `{{DOC_VERSION}}`, `{{VERSION}}` | Use DOC_VERSION (clearest) |

### Date Placeholders

| Primary | Aliases | Use Case |
|---------|---------|----------|
| `{{CREATION_DATE}}` | `{{CREATED_DATE}}` | Either is fine |
| `{{LAST_MODIFIED}}` | `{{UPDATED_DATE}}`, `{{MODIFIED_DATE}}` | Use LAST_MODIFIED |

### Why Multiple Names?

1. **Backward compatibility** - Old templates continue working
2. **Flexibility** - Choose short or descriptive names
3. **Clarity** - `_NAME` suffix clearly indicates it's a name string

**All aliases point to the same value** - use whichever makes your template clearest!

---

## 📥 Download Methods

### Download Annotated Document

**Access**: Any authenticated user  
**Status**: Any document status  
**Output**: Original format (.docx) or ZIP

**What happens:**
1. System gets 68 placeholder values from database
2. For .docx files: Replaces all `{{PLACEHOLDER}}` with actual values
3. For other files: Creates ZIP with original file + metadata.txt
4. Returns editable document

**Use when:**
- ✅ Reviewing draft documents
- ✅ Developing new templates
- ✅ Need to edit document further
- ✅ Want metadata for reference
- ✅ Testing placeholder replacements

### Download Official PDF

**Access**: Any authenticated user  
**Status**: APPROVED or EFFECTIVE documents only  
**Output**: Always PDF format

**What happens:**
1. System gets 68 placeholder values from database
2. For .docx: Replaces `{{PLACEHOLDER}}`, then converts to PDF
3. For .pdf: Uses existing PDF
4. Adds professional elements:
   - Watermark: "OFFICIAL DOCUMENT"
   - Header: Document number and title
   - Footer: Page numbers, effective date, company name
5. Digital signature (if configured)
6. Returns tamper-proof PDF

**Use when:**
- ✅ Distributing approved documents
- ✅ Printing official copies
- ✅ Archiving records
- ✅ Compliance requirements
- ✅ External distribution

---

## 💡 Best Practices

### Template Design

✅ **DO:**
- Use descriptive placeholder names: `{{AUTHOR_NAME}}` over `{{AUTHOR}}`
- Include fallback text: "Author: {{AUTHOR_NAME}}" (shows "Author: " even if value is empty)
- Test with Template Validator before deployment
- Document which placeholders your template uses
- Use consistent naming (pick one alias style and stick with it)

❌ **DON'T:**
- Mix placeholder styles inconsistently (choose DOC_TITLE or DOCUMENT_TITLE, not both)
- Use placeholders that aren't in the system
- Forget double braces: `{AUTHOR}` won't work, must be `{{AUTHOR}}`
- Use spaces inside braces: `{{ AUTHOR }}` won't work

### Placeholder Selection

| Use Case | Recommended Placeholders |
|----------|-------------------------|
| **Cover Page** | DOCUMENT_NUMBER, DOCUMENT_TITLE, DOC_VERSION, EFFECTIVE_DATE, COMPANY_NAME |
| **Header/Footer** | DOC_NUMBER, TITLE, CURRENT_DATE, PAGE_NUMBER |
| **Approval Section** | AUTHOR_NAME, REVIEWER_NAME, APPROVER_NAME, APPROVAL_DATE |
| **Version History** | VERSION_HISTORY (creates full table automatically) |
| **Metadata Table** | CREATED_DATE, LAST_MODIFIED, DOC_TYPE, DOC_SOURCE, WORKFLOW_STATUS |

### Testing Templates

1. Create template with placeholders
2. Upload to EDMS
3. Go to **Placeholders** page → **Validate Template**
4. Upload .docx to check for issues
5. Fix any unknown placeholders
6. Download Annotated to verify replacement works
7. Deploy to production

---

## 🔧 Troubleshooting

### Placeholder Not Replacing

**Problem**: `{{AUTHOR_NAME}}` appears in downloaded document instead of actual name

**Solutions:**
1. Check spelling: Must be exact match (case-sensitive)
2. Check braces: Must be `{{` and `}}` (two braces each side)
3. Check spaces: No spaces inside braces
4. Verify placeholder exists: Use Template Validator
5. For .pdf/.txt files: Placeholders go in metadata.txt, not the file itself

### Unknown Placeholder Warning

**Problem**: Template Validator says "Unknown placeholder: {{AUTHOR_NAME}}"

**Solutions:**
1. This was a bug we fixed today! If you still see this, refresh your browser
2. Check spelling against placeholder list
3. Use Template Validator's suggestions
4. Verify you're using a supported placeholder (check this guide)

### Wrong Person's Name Appearing

**Problem**: Template shows approver's name instead of reviewer's name

**Solutions:**
1. Verify you're using correct placeholder: `{{REVIEWER_NAME}}` not `{{APPROVER_NAME}}`
2. Check if document has reviewer assigned (may show "Not Assigned")
3. Verify person fields are populated in document

### Dates Not Formatting Correctly

**Problem**: Want "December 23, 2025" but get "2025-12-23"

**Solutions:**
1. Use `_LONG` versions: `{{CREATED_DATE_LONG}}` instead of `{{CREATED_DATE}}`
2. Available long formats: CREATED_DATE_LONG, APPROVAL_DATE_LONG, EFFECTIVE_DATE_LONG, DOWNLOAD_DATE_LONG, CURRENT_DATE_LONG

### Version History Table Not Showing

**Problem**: `{{VERSION_HISTORY}}` placeholder not creating table

**Solutions:**
1. Only works in .docx templates
2. Requires document to have version history
3. Must be in a table cell or paragraph (not text box)
4. For custom formatting, use `{{VERSION_HISTORY_TABLE_DATA}}` and format manually

---

## 📞 Support

### Need Help?

1. **Template Validator**: Use built-in validator on Placeholders page
2. **This Guide**: Refer to placeholder reference above
3. **Test First**: Always test with "Download Annotated" before official distribution
4. **IT Support**: Contact your system administrator for custom placeholder requests

### Reporting Issues

If you find a placeholder that:
- Doesn't work as documented
- Shows incorrect information
- Causes download errors

Contact your system administrator with:
- Template file
- Document number
- Expected vs. actual output
- Screenshot of issue

---

## 📊 Quick Reference Card

### Most Common Placeholders

```
{{DOCUMENT_NUMBER}}      - Full document number
{{DOCUMENT_TITLE}}       - Document title
{{DOC_VERSION}}          - Version number
{{AUTHOR_NAME}}          - Author's name
{{EFFECTIVE_DATE}}       - When document takes effect
{{WORKFLOW_STATUS}}      - Current workflow state
{{COMPANY_NAME}}         - Your company name
{{DOWNLOAD_DATE}}        - Today's date
```

### Download Options

| Feature | Annotated | Official PDF |
|---------|-----------|-------------|
| Access | All users | All users |
| Status | Any | Approved only |
| Format | Original | PDF |
| Editable | Yes | No |
| Watermarks | No | Yes |
| Signed | No | Optional |

### Alias Quick Reference

- `AUTHOR` = `AUTHOR_NAME`
- `REVIEWER` = `REVIEWER_NAME`
- `APPROVER` = `APPROVER_NAME`
- `DOC_NUMBER` = `DOCUMENT_NUMBER` = `NUMBER`
- `DOC_TITLE` = `DOCUMENT_TITLE` = `TITLE`
- `DOC_STATUS` = `DOCUMENT_STATUS` = `STATUS`

All aliases work identically - choose based on your preference!

---

**Last Updated**: December 23, 2025  
**Total Placeholders**: 68 (32 in database + 36 runtime aliases/extras)  
**System Version**: EDMS v1.0 with Enhanced Placeholder Support
