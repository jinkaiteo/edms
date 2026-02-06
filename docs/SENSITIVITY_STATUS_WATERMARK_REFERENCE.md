# Document Status Watermark Reference

## Complete Status Watermark Configuration

This document lists all document statuses in the EDMS system and their corresponding diagonal watermark configurations.

---

## Status Watermark Matrix

| Status | Show Diagonal? | Watermark Text | Color | Opacity | Use Case |
|--------|----------------|----------------|-------|---------|----------|
| **DRAFT** | ✅ Yes | `DRAFT\nNOT FOR USE` | Red | 20% | Initial creation |
| **PENDING_REVIEW** | ✅ Yes | `PENDING REVIEW` | Orange | 20% | Submitted, awaiting reviewer assignment |
| **UNDER_REVIEW** | ✅ Yes | `UNDER REVIEW` | Orange | 20% | Actively being reviewed |
| **REVIEW_COMPLETED** | ✅ Yes | `REVIEW COMPLETED\nPENDING APPROVAL` | Green | 15% | Review done, awaiting approval |
| **PENDING_APPROVAL** | ✅ Yes | `PENDING APPROVAL` | Blue | 20% | Awaiting approver action |
| **UNDER_APPROVAL** | ✅ Yes | `UNDER APPROVAL` | Blue | 20% | Being reviewed by approver |
| **APPROVED** | ✅ Yes | `APPROVED\nNOT YET EFFECTIVE` | Blue | 15% | Approved but not effective yet |
| **APPROVED_PENDING_EFFECTIVE** | ✅ Yes | `APPROVED\nPENDING EFFECTIVE` | Blue | 15% | Approved, waiting for effective date |
| **EFFECTIVE** | ❌ No | *(none)* | - | - | **Active operational document** |
| **SCHEDULED_FOR_OBSOLESCENCE** | ✅ Yes | `SCHEDULED FOR\nOBSOLESCENCE` | Orange | 25% | Marked for retirement |
| **SUPERSEDED** | ✅ Yes | `SUPERSEDED` | Gray | 25% | Replaced by newer version |
| **OBSOLETE** | ✅ Yes | `OBSOLETE\nDO NOT USE` | Gray | 30% | Retired, do not use |
| **TERMINATED** | ✅ Yes | `TERMINATED` | Red | 30% | Cancelled before effective |

---

## Watermark Colors

| Status Category | Color | Hex Code | Meaning |
|-----------------|-------|----------|---------|
| **Draft/Not Finalized** | Red | `#ef4444` | Warning - not approved |
| **In Review** | Orange | `#f59e0b` | In progress |
| **Approved/Pending** | Blue | `#3b82f6` | Approved but waiting |
| **Review Complete** | Green | `#10b981` | Positive progress |
| **Retired** | Gray | `#6b7280` | Historical, do not use |
| **Terminated** | Red | `#dc2626` | Cancelled |

---

## Visual Examples by Status

### 1. DRAFT
```
┌─────────────────────────────────┐
│      DRAFT          ← Red, 20% opacity
│    NOT FOR USE
│
│  [Document content]
└─────────────────────────────────┘
```

### 2. PENDING_REVIEW
```
┌─────────────────────────────────┐
│   PENDING REVIEW    ← Orange, 20% opacity
│
│  [Document content]
└─────────────────────────────────┘
```

### 3. UNDER_REVIEW
```
┌─────────────────────────────────┐
│   UNDER REVIEW      ← Orange, 20% opacity
│
│  [Document content]
└─────────────────────────────────┘
```

### 4. REVIEW_COMPLETED
```
┌─────────────────────────────────┐
│  REVIEW COMPLETED   ← Green, 15% opacity
│  PENDING APPROVAL
│
│  [Document content]
└─────────────────────────────────┘
```

### 5. PENDING_APPROVAL
```
┌─────────────────────────────────┐
│  PENDING APPROVAL   ← Blue, 20% opacity
│
│  [Document content]
└─────────────────────────────────┘
```

### 6. UNDER_APPROVAL
```
┌─────────────────────────────────┐
│  UNDER APPROVAL     ← Blue, 20% opacity
│
│  [Document content]
└─────────────────────────────────┘
```

### 7. APPROVED
```
┌─────────────────────────────────┐
│     APPROVED        ← Blue, 15% opacity
│  NOT YET EFFECTIVE
│
│  [Document content]
└─────────────────────────────────┘
```

### 8. APPROVED_PENDING_EFFECTIVE
```
┌─────────────────────────────────┐
│     APPROVED        ← Blue, 15% opacity
│  PENDING EFFECTIVE
│
│  [Document content]
└─────────────────────────────────┘
```

### 9. EFFECTIVE (CLEAN)
```
┌─────────────────────────────────┐
│  [No diagonal watermark]
│
│  [Document content] ← Clean, operational document
│
└─────────────────────────────────┘
```

### 10. SCHEDULED_FOR_OBSOLESCENCE
```
┌─────────────────────────────────┐
│  SCHEDULED FOR      ← Orange, 25% opacity
│   OBSOLESCENCE
│
│  [Document content]
└─────────────────────────────────┘
```

### 11. SUPERSEDED
```
┌─────────────────────────────────┐
│    SUPERSEDED       ← Gray, 25% opacity
│
│  [Document content]
└─────────────────────────────────┘
```

### 12. OBSOLETE
```
┌─────────────────────────────────┐
│     OBSOLETE        ← Gray, 30% opacity
│    DO NOT USE
│
│  [Document content]
└─────────────────────────────────┘
```

### 13. TERMINATED
```
┌─────────────────────────────────┐
│    TERMINATED       ← Red, 30% opacity
│
│  [Document content]
└─────────────────────────────────┘
```

---

## Combined with Sensitivity Headers

### Example: DRAFT + CONFIDENTIAL
```
┌─────────────────────────────────┐
│ CONFIDENTIAL                    │ ← Orange sensitivity header
├─────────────────────────────────┤
│      DRAFT                      │ ← Red diagonal watermark
│    NOT FOR USE                  │
│                                 │
│  [Document content]             │
└─────────────────────────────────┘
```

### Example: UNDER_REVIEW + RESTRICTED
```
┌─────────────────────────────────┐
│ RESTRICTED - REGULATORY         │ ← Purple sensitivity header
├─────────────────────────────────┤
│   UNDER REVIEW                  │ ← Orange diagonal watermark
│                                 │
│  [Document content]             │
└─────────────────────────────────┘
```

### Example: APPROVED_PENDING_EFFECTIVE + PROPRIETARY
```
┌─────────────────────────────────┐
│ PROPRIETARY - TRADE SECRET      │ ← Red sensitivity header
├─────────────────────────────────┤
│     APPROVED                    │ ← Blue diagonal watermark
│  PENDING EFFECTIVE              │
│                                 │
│  [Document content]             │
└─────────────────────────────────┘
```

### Example: EFFECTIVE + CONFIDENTIAL
```
┌─────────────────────────────────┐
│ CONFIDENTIAL                    │ ← Orange sensitivity header
├─────────────────────────────────┤
│  [No diagonal watermark]        │ ← Clean document
│                                 │
│  [Document content]             │
└─────────────────────────────────┘
```

### Example: OBSOLETE + PROPRIETARY
```
┌─────────────────────────────────┐
│ PROPRIETARY - TRADE SECRET      │ ← Red sensitivity header
├─────────────────────────────────┤
│     OBSOLETE                    │ ← Gray diagonal watermark
│    DO NOT USE                   │
│                                 │
│  [Document content]             │
└─────────────────────────────────┘
```

---

## Business Logic Summary

### When to Show Diagonal Watermark

**SHOW watermark for:**
- ✅ DRAFT - Not approved yet
- ✅ PENDING_REVIEW - Awaiting review
- ✅ UNDER_REVIEW - Being reviewed
- ✅ REVIEW_COMPLETED - Review done, awaiting approval
- ✅ PENDING_APPROVAL - Awaiting approval
- ✅ UNDER_APPROVAL - Being approved
- ✅ APPROVED - Approved but not effective
- ✅ APPROVED_PENDING_EFFECTIVE - Waiting for effective date
- ✅ SCHEDULED_FOR_OBSOLESCENCE - Marked for retirement
- ✅ SUPERSEDED - Replaced by newer version
- ✅ OBSOLETE - Do not use
- ✅ TERMINATED - Cancelled

**DO NOT show watermark for:**
- ❌ EFFECTIVE - Clean operational document

### Opacity Levels

| Opacity | Use Case | Example Statuses |
|---------|----------|-----------------|
| **15%** | Approved, lighter touch | APPROVED, APPROVED_PENDING_EFFECTIVE, REVIEW_COMPLETED |
| **20%** | In-progress workflow | DRAFT, PENDING_REVIEW, UNDER_REVIEW, PENDING_APPROVAL, UNDER_APPROVAL |
| **25%** | Scheduled changes | SCHEDULED_FOR_OBSOLESCENCE, SUPERSEDED |
| **30%** | Critical warnings | OBSOLETE, TERMINATED |

---

## Implementation Notes

### Watermark Processor Configuration

The watermark processor (`watermark_processor.py`) contains the `STATUS_CONFIG` dictionary that maps each status to its watermark configuration:

```python
STATUS_CONFIG = {
    'DRAFT': {
        'show_watermark': True,
        'watermark_text': 'DRAFT\nNOT FOR USE',
        'watermark_color': HexColor('#ef4444'),  # Red
        'watermark_opacity': 0.2,
    },
    # ... 12 more status configurations
}
```

### Adding New Statuses

If you add new document statuses in the future:

1. Add status to `DOCUMENT_STATUS_CHOICES` in `models.py`
2. Add corresponding entry in `STATUS_CONFIG` in `watermark_processor.py`
3. Update this reference document
4. Test watermark appearance

### Testing Checklist

- [ ] DRAFT documents show red "DRAFT\nNOT FOR USE"
- [ ] PENDING_REVIEW shows orange "PENDING REVIEW"
- [ ] UNDER_REVIEW shows orange "UNDER REVIEW"
- [ ] REVIEW_COMPLETED shows green "REVIEW COMPLETED\nPENDING APPROVAL"
- [ ] PENDING_APPROVAL shows blue "PENDING APPROVAL"
- [ ] UNDER_APPROVAL shows blue "UNDER APPROVAL"
- [ ] APPROVED shows blue "APPROVED\nNOT YET EFFECTIVE"
- [ ] APPROVED_PENDING_EFFECTIVE shows blue "APPROVED\nPENDING EFFECTIVE"
- [ ] EFFECTIVE documents have NO diagonal watermark (clean)
- [ ] SCHEDULED_FOR_OBSOLESCENCE shows orange "SCHEDULED FOR\nOBSOLESCENCE"
- [ ] SUPERSEDED shows gray "SUPERSEDED"
- [ ] OBSOLETE shows gray "OBSOLETE\nDO NOT USE"
- [ ] TERMINATED shows red "TERMINATED"
- [ ] All watermarks appear on every page
- [ ] Watermarks combined correctly with sensitivity headers

---

## User Experience

### What Users See

**During Draft/Review/Approval:**
- Clear status indicated by diagonal watermark
- Color-coded for quick recognition
- Cannot be confused with operational documents

**After Approval (Effective):**
- Clean, professional document
- No distracting diagonal watermark
- Only sensitivity header if CONFIDENTIAL+
- Ready for operational use

**After Obsolescence:**
- Clear warning not to use
- Historical reference only
- Maintains classification if sensitive

---

**Last Updated:** 2026-02-05  
**Version:** 1.0  
**Matched to:** `DOCUMENT_STATUS_CHOICES` in `backend/apps/documents/models.py`
