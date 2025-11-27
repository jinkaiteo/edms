# Test Template Content for DOCX Processing

## How to Test the Placeholder Replacement:

### Step 1: Create a Test Document
Create a new Word document (.docx) with this content:

```
DOCUMENT MANAGEMENT SYSTEM TEST

Document Title: {{DOC_TITLE}}
Document Number: {{DOC_NUMBER}}
Version: {{DOC_VERSION}}
Status: {{DOC_STATUS}}

Author Information:
- Name: {{AUTHOR_NAME}}
- Email: {{AUTHOR_EMAIL}}

Reviewer Information:  
- Name: {{REVIEWER_NAME}}
- Email: {{REVIEWER_EMAIL}}

Document Dates:
- Created: {{CREATED_DATE}}
- Modified: {{UPDATED_DATE}}
- Downloaded: {{DOWNLOAD_DATE}}

System Information:
- Company: {{COMPANY_NAME}}
- System: {{SYSTEM_NAME}}
- Current Time: {{CURRENT_DATETIME}}

Status Indicators:
{{IF_DRAFT}}
{{IF_APPROVED}}
{{IF_EFFECTIVE}}

Alternative Placeholder Names (also supported):
- Title: {{TITLE}}
- Author: {{AUTHOR}}  
- Status: {{STATUS}}
- Version: {{VERSION}}
- Number: {{NUMBER}}
- Date: {{DATE}}
- Time: {{TIME}}
```

### Step 2: Upload and Test
1. Save the above content as a .docx file
2. Upload it to EDMS as a new document
3. Submit for review
4. Login as reviewer
5. Click "Annotated Document" button
6. Download should return processed .docx with all placeholders replaced

### Expected Result:
All {{PLACEHOLDER}} patterns will be replaced with actual document metadata values like:
- {{DOC_TITLE}} → "Your Document Title"
- {{AUTHOR_NAME}} → "Document Author"
- {{CURRENT_DATE}} → "2025-01-27"
- etc.

### Supported Placeholders (50+ total):
The system now supports both primary names (DOC_TITLE, AUTHOR_NAME) and common alternatives (TITLE, AUTHOR) for maximum template compatibility.