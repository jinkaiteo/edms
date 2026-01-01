# Document Types and Sources Analysis

## 🔍 **Current Running System (from Docker)**

### Document Types (9 types in database)
```
- POL: Policy
- FORM: Forms and Templates  
- FRM: Form
- MAN: Manual
- POL: Policy (duplicate entry with blank code?)
- PROC: Procedures
- REC: Record
- SOP: Work Instructions
- WI: Work Instruction
```

**Issue Found:** There's a duplicate or data quality issue - two POL entries, one with blank code.

### Document Sources (3 sources in database)
```
- Original Digital Draft (Type: original_digital)
  * Requires Signature: False
  * Requires Verification: False

- Scanned Copy (Type: scanned_copy)
  * Requires Signature: False
  * Requires Verification: True

- Scanned Original (Type: scanned_original)
  * Requires Signature: False
  * Requires Verification: True
```

---

## 📋 **Model Definition (from models.py)**

### DocumentSource.SOURCE_TYPES Choices
```python
SOURCE_TYPES = [
    ('original_digital', 'Original Digital'),
    ('scanned_paper', 'Scanned Paper Document'),
    ('imported_system', 'Imported from Another System'),
    ('email_attachment', 'Email Attachment'),
    ('web_upload', 'Web Upload'),
    ('api_creation', 'API Creation'),
    ('template_generation', 'Generated from Template'),
]
```

**Gap:** Only 3 out of 7 possible source types are created in the database!

---

## 🎯 **What Should Be Created**

### Recommended Document Types (8 clean types)
Based on running system (fixing the duplicate):
1. **POL** - Policy
2. **PROC** - Procedures  
3. **SOP** - Standard Operating Procedures / Work Instructions
4. **WI** - Work Instruction
5. **FORM** - Forms and Templates
6. **FRM** - Form
7. **MAN** - Manual
8. **REC** - Record

### Recommended Document Sources (All 7 types)
Based on SOURCE_TYPES choices:
1. **Original Digital** (original_digital) - Born-digital documents
2. **Scanned Paper** (scanned_paper) - Scanned from paper
3. **Scanned Original** (scanned_original) - Scanned original document
4. **Imported System** (imported_system) - Migrated from another system
5. **Email Attachment** (email_attachment) - Received via email
6. **Web Upload** (web_upload) - User uploaded through web interface
7. **Template Generation** (template_generation) - Auto-generated from template

---

## 🔧 **Action Items**

### 1. Create Management Command for Document Types
```python
# backend/apps/documents/management/commands/create_default_document_types.py
```

Should create:
- POL, PROC, SOP, WI, FORM, FRM, MAN, REC

### 2. Create Management Command for Document Sources  
```python
# backend/apps/documents/management/commands/create_default_document_sources.py
```

Should create all 7 source types from SOURCE_TYPES

### 3. Fix Data Quality Issue
- Remove duplicate POL entry with blank code
- Ensure all codes are unique and uppercase

---

## 📊 **Current State vs Desired State**

| Category | Current | Should Have | Missing |
|----------|---------|-------------|---------|
| Document Types | 9 (with dupe) | 8 clean | Need cleanup |
| Document Sources | 3 | 7 | Missing 4 |

---

## 🚀 **Next Steps**

1. Create `create_default_document_types.py` management command
2. Create `create_default_document_sources.py` management command
3. Add to initialization script alongside roles
4. Clean up duplicate POL entry

---

**Status:** Analysis complete, ready to create initialization commands
