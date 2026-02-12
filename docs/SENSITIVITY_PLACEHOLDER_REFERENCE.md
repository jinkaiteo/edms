# Sensitivity Label Placeholder Reference

## Complete List of Sensitivity Placeholders

### Basic Placeholders

| Placeholder | Output | Description |
|-------------|--------|-------------|
| `{{SENSITIVITY_LABEL}}` | `CONFIDENTIAL` | Sensitivity code (uppercase) |
| `{{SENSITIVITY_LABEL_FULL}}` | `Confidential` | Full display name |
| `{{SENSITIVITY_LABEL_ICON}}` | `🔒` | Icon emoji for the label |
| `{{SENSITIVITY_WATERMARK}}` | `CONFIDENTIAL` | Watermark text (for PDF headers) |

### Conditional Placeholders (Smart Display)

| Placeholder | Shows When | Output |
|-------------|-----------|--------|
| `{{IF_PUBLIC}}` | Sensitivity = PUBLIC | ` ` (empty - PUBLIC has no header) |
| `{{IF_INTERNAL}}` | Sensitivity = INTERNAL | `INTERNAL USE ONLY` |
| `{{IF_CONFIDENTIAL}}` | Sensitivity = CONFIDENTIAL | `CONFIDENTIAL` |
| `{{IF_RESTRICTED}}` | Sensitivity = RESTRICTED | `RESTRICTED - REGULATORY/COMPLIANCE` |
| `{{IF_PROPRIETARY}}` | Sensitivity = PROPRIETARY | `PROPRIETARY - TRADE SECRET` |

### Metadata Placeholders

| Placeholder | Output Example | Description |
|-------------|----------------|-------------|
| `{{SENSITIVITY_SET_BY}}` | `John Approver` | Who set the sensitivity label |
| `{{SENSITIVITY_SET_DATE}}` | `2026-02-05` | When sensitivity was set (short) |
| `{{SENSITIVITY_SET_DATE_LONG}}` | `February 5, 2026` | When sensitivity was set (long) |
| `{{SENSITIVITY_CHANGE_REASON}}` | `Added trade secret information...` | Reason for change (if changed from parent) |

---

## Usage Examples

### Example 1: Document Header with Sensitivity

**Template (DOCX):**
```
{{IF_CONFIDENTIAL}}

Document Title: {{DOC_TITLE}}
Document Number: {{DOC_NUMBER}}
Version: {{DOC_VERSION}}
Classification: {{SENSITIVITY_LABEL_FULL}}
```

**Output (if CONFIDENTIAL):**
```
CONFIDENTIAL

Document Title: Customer Service Agreement
Document Number: CONT-2026-0042
Version: 1.0
Classification: Confidential
```

**Output (if INTERNAL):**
```
                    ← Empty (IF_CONFIDENTIAL shows nothing)

Document Title: Standard Operating Procedure
Document Number: SOP-QMS-001
Version: 2.0
Classification: Internal Use Only
```

---

### Example 2: Cover Page with Full Sensitivity Info

**Template (DOCX):**
```
DOCUMENT CONTROL INFORMATION

Title: {{DOC_TITLE}}
Number: {{DOC_NUMBER}}
Version: {{DOC_VERSION}}
Status: {{DOC_STATUS}}

SECURITY CLASSIFICATION
{{SENSITIVITY_LABEL_ICON}} {{SENSITIVITY_LABEL_FULL}}

Classified by: {{SENSITIVITY_SET_BY}}
Classification Date: {{SENSITIVITY_SET_DATE_LONG}}

{{#if SENSITIVITY_CHANGE_REASON}}
Reason for Classification Change:
{{SENSITIVITY_CHANGE_REASON}}
{{/if}}
```

**Output:**
```
DOCUMENT CONTROL INFORMATION

Title: Manufacturing Process Specification
Number: PROC-2025-0012
Version: 3.0
Status: Effective

SECURITY CLASSIFICATION
🛡️ Proprietary / Trade Secret

Classified by: Sarah Approver
Classification Date: January 15, 2026

Reason for Classification Change:
Added proprietary coating formula developed in R&D project RD-2025-089. 
This formula represents significant competitive advantage and qualifies 
as trade secret under company IP protection policy.
```

---

### Example 3: Footer with Dynamic Sensitivity

**Template (DOCX footer):**
```
{{DOC_NUMBER}} v{{DOC_VERSION}} | {{IF_CONFIDENTIAL}}{{IF_RESTRICTED}}{{IF_PROPRIETARY}} | Page {{PAGE_NUM}}
```

**Output Options:**
- INTERNAL document: `SOP-001 v2.0 |  | Page 1` (empty middle section)
- CONFIDENTIAL document: `CONT-042 v1.0 | CONFIDENTIAL | Page 1`
- RESTRICTED document: `REG-087 v1.0 | RESTRICTED - REGULATORY/COMPLIANCE | Page 1`
- PROPRIETARY document: `PROC-012 v3.0 | PROPRIETARY - TRADE SECRET | Page 1`

---

### Example 4: Conditional Warning Box

**Template (DOCX):**
```
{{#if IF_PROPRIETARY}}
┌────────────────────────────────────────────┐
│ ⚠️ PROPRIETARY INFORMATION                │
│                                            │
│ This document contains trade secrets and  │
│ proprietary information. Unauthorized     │
│ disclosure may result in legal action.    │
│                                            │
│ Classified by: {{SENSITIVITY_SET_BY}}     │
│ Date: {{SENSITIVITY_SET_DATE}}            │
└────────────────────────────────────────────┘
{{/if}}
```

**Output (if PROPRIETARY):**
```
┌────────────────────────────────────────────┐
│ ⚠️ PROPRIETARY INFORMATION                │
│                                            │
│ This document contains trade secrets and  │
│ proprietary information. Unauthorized     │
│ disclosure may result in legal action.    │
│                                            │
│ Classified by: Sarah Approver             │
│ Date: 2026-01-15                          │
└────────────────────────────────────────────┘
```

**Output (if not PROPRIETARY):**
```
                    ← Nothing displayed
```

---

### Example 5: Sensitivity with Document Status

**Template (DOCX):**
```
Classification: {{SENSITIVITY_LABEL_FULL}}
Status: {{DOC_STATUS}}

{{#if IF_DRAFT}}
⚠️ DRAFT DOCUMENT - NOT FOR USE
This document is in draft status and has not been approved.
{{/if}}

{{#if IF_RESTRICTED}}
⚠️ REGULATORY COMPLIANCE DOCUMENT
This document is subject to regulatory oversight. Handle according to 
regulatory document management procedures.
{{/if}}
```

**Output (DRAFT + RESTRICTED):**
```
Classification: Restricted - Regulatory/Compliance
Status: Draft

⚠️ DRAFT DOCUMENT - NOT FOR USE
This document is in draft status and has not been approved.

⚠️ REGULATORY COMPLIANCE DOCUMENT
This document is subject to regulatory oversight. Handle according to 
regulatory document management procedures.
```

---

## Integration with Existing Placeholders

Sensitivity placeholders work alongside all existing EDMS placeholders:

```
Document: {{DOC_TITLE}}
Number: {{DOC_NUMBER}}
Version: {{DOC_VERSION}}
Status: {{DOC_STATUS}}
Classification: {{SENSITIVITY_LABEL_FULL}}

Author: {{AUTHOR_NAME}}
Approver: {{APPROVER_NAME}}
Effective Date: {{EFFECTIVE_DATE}}
Classification Date: {{SENSITIVITY_SET_DATE}}

Created: {{CREATED_DATE}}
Last Modified: {{UPDATED_DATE}}
Downloaded: {{DOWNLOAD_DATETIME}}

{{IF_CONFIDENTIAL}}
{{IF_PROPRIETARY}}
```

---

## Common Use Cases

### 1. Cover Page
```
{{COMPANY_NAME}}

{{DOC_TITLE}}
{{DOC_NUMBER}} - Version {{DOC_VERSION}}

{{SENSITIVITY_LABEL_ICON}} {{SENSITIVITY_LABEL_FULL}}

Prepared by: {{AUTHOR_NAME}}
Approved by: {{APPROVER_NAME}}
Effective Date: {{EFFECTIVE_DATE_LONG}}
```

### 2. Header (Every Page)
```
{{IF_CONFIDENTIAL}}{{IF_RESTRICTED}}{{IF_PROPRIETARY}}
{{DOC_NUMBER}} | {{DOC_TITLE}} | v{{DOC_VERSION}}
```

### 3. Footer (Every Page)
```
{{SENSITIVITY_LABEL}} | {{DOC_STATUS}} | Page {{PAGE_NUM}} of {{TOTAL_PAGES}}
Generated: {{DOWNLOAD_DATE}}
```

### 4. Metadata Section
```
DOCUMENT CONTROL

Classification: {{SENSITIVITY_LABEL_FULL}}
Classified By: {{SENSITIVITY_SET_BY}}
Classification Date: {{SENSITIVITY_SET_DATE_LONG}}

Document Number: {{DOC_NUMBER}}
Version: {{DOC_VERSION}}
Status: {{DOC_STATUS}}
Effective Date: {{EFFECTIVE_DATE}}
```

### 5. Warning Banner
```
{{#if IF_PROPRIETARY}}
═══════════════════════════════════════════════════════════
    🛡️ PROPRIETARY - TRADE SECRET - DO NOT DISTRIBUTE
═══════════════════════════════════════════════════════════
{{/if}}

{{#if IF_RESTRICTED}}
═══════════════════════════════════════════════════════════
    ⚠️ RESTRICTED - REGULATORY/COMPLIANCE DOCUMENT
═══════════════════════════════════════════════════════════
{{/if}}
```

---

## Placeholder Values by Sensitivity Level

| Sensitivity | LABEL | LABEL_FULL | ICON | WATERMARK |
|-------------|-------|------------|------|-----------|
| PUBLIC | `PUBLIC` | `Public` | 🌐 | ` ` (empty) |
| INTERNAL | `INTERNAL` | `Internal Use Only` | 🏢 | `INTERNAL USE ONLY` |
| CONFIDENTIAL | `CONFIDENTIAL` | `Confidential` | 🔒 | `CONFIDENTIAL` |
| RESTRICTED | `RESTRICTED` | `Restricted - Regulatory/Compliance` | ⚠️ | `RESTRICTED - REGULATORY/COMPLIANCE` |
| PROPRIETARY | `PROPRIETARY` | `Proprietary / Trade Secret` | 🛡️ | `PROPRIETARY - TRADE SECRET` |

---

## Best Practices

### ✅ DO

1. **Use conditional placeholders for headers**
   ```
   {{IF_CONFIDENTIAL}}{{IF_RESTRICTED}}{{IF_PROPRIETARY}}
   ```
   This ensures only applicable classifications show

2. **Include classification in cover pages**
   ```
   Classification: {{SENSITIVITY_LABEL_FULL}}
   Classified by: {{SENSITIVITY_SET_BY}}
   ```

3. **Show classification in footers for high-sensitivity docs**
   ```
   {{IF_CONFIDENTIAL}} | {{DOC_NUMBER}} | Page {{PAGE_NUM}}
   ```

4. **Document classification changes**
   ```
   {{#if SENSITIVITY_CHANGE_REASON}}
   Classification Change: {{SENSITIVITY_CHANGE_REASON}}
   {{/if}}
   ```

### ❌ DON'T

1. **Don't use raw labels without context**
   ```
   {{SENSITIVITY_LABEL}}  ← Just "CONFIDENTIAL" - not user-friendly
   ```
   Use instead:
   ```
   Classification: {{SENSITIVITY_LABEL_FULL}}  ← "Classification: Confidential"
   ```

2. **Don't show classification metadata for all docs**
   ```
   Classified by: {{SENSITIVITY_SET_BY}}  ← Shows "System Default" for old docs
   ```
   Use conditional:
   ```
   {{#if SENSITIVITY_SET_BY}}
   Classified by: {{SENSITIVITY_SET_BY}}
   {{/if}}
   ```

3. **Don't duplicate watermarks**
   - PDF watermarks are added automatically
   - Don't add `{{IF_DRAFT}}` in body text - it's in the diagonal watermark

---

## Testing Your Templates

### Test Document 1: DRAFT + INTERNAL
- `{{SENSITIVITY_LABEL}}` → `INTERNAL`
- `{{IF_INTERNAL}}` → `INTERNAL USE ONLY`
- `{{IF_CONFIDENTIAL}}` → ` ` (empty)
- PDF: No header bar, Red "DRAFT" diagonal

### Test Document 2: EFFECTIVE + CONFIDENTIAL
- `{{SENSITIVITY_LABEL}}` → `CONFIDENTIAL`
- `{{IF_CONFIDENTIAL}}` → `CONFIDENTIAL`
- `{{IF_INTERNAL}}` → ` ` (empty)
- PDF: Orange header bar, No diagonal

### Test Document 3: EFFECTIVE + PROPRIETARY
- `{{SENSITIVITY_LABEL}}` → `PROPRIETARY`
- `{{IF_PROPRIETARY}}` → `PROPRIETARY - TRADE SECRET`
- `{{SENSITIVITY_SET_BY}}` → `Sarah Approver`
- PDF: Red header bar, No diagonal

---

## Backward Compatibility

**Old templates without sensitivity placeholders:**
- Will continue to work
- Documents will have sensitivity set by approver
- PDF watermarks will still be applied
- No placeholders = no sensitivity text in document body (only in PDF watermark)

**Recommended migration:**
1. Add `{{IF_CONFIDENTIAL}}{{IF_RESTRICTED}}{{IF_PROPRIETARY}}` to headers
2. Add `Classification: {{SENSITIVITY_LABEL_FULL}}` to cover page
3. Test with documents at each sensitivity level

---

## Support

For questions about sensitivity placeholders:
1. Review examples in this document
2. Check `SENSITIVITY_LABEL_CLASSIFICATION_GUIDE.md` for classification guidance
3. Review `SENSITIVITY_WATERMARK_MOCKUPS.md` for visual examples
4. Contact Document Control team

---

**Last Updated:** 2026-02-05  
**Version:** 1.0  
**Module:** S6 - Placeholder System + Sensitivity Labels
