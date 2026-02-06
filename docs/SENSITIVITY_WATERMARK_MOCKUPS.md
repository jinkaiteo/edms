# Sensitivity Label & Status Watermark Visual Mockups

## Overview

This document shows visual representations of how sensitivity labels and status watermarks appear on PDF documents in the EDMS system.

---

## Watermark System Architecture

### Two-Layer System

1. **Sensitivity Header Bar** (Top of page) - Persistent classification reminder
2. **Status Diagonal Watermark** (Center) - Prevents use of non-finalized documents

---

## Visual Mockups

### Example 1: DRAFT + CONFIDENTIAL Document

```
┌────────────────────────────────────────────────────────────┐
│ CONFIDENTIAL                                               │  ← Orange bar (0.4" tall)
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Standard Operating Procedure                             │
│  Document Control Process                                 │
│                                                            │
│  DOC-2026-0042                                            │
│                     DRAFT                                  │  ← Red diagonal (45°, 20% opacity)
│  Purpose:                                                  │
│  This procedure      NOT FOR USE                          │
│  defines the...                                           │
│                                                            │
│  1. Scope                                                  │
│     ...                                                    │
│                                                            │
│  2. Procedure                                              │
│     ...                                                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Styling Details:**
- **Header Bar**: Orange (#ea580c), White text, 14pt bold, centered
- **Diagonal**: Red (#ef4444), "DRAFT\nNOT FOR USE", 60pt bold, 20% opacity, 45° rotation

---

### Example 2: EFFECTIVE + RESTRICTED Document

```
┌────────────────────────────────────────────────────────────┐
│ RESTRICTED - REGULATORY/COMPLIANCE                         │  ← Purple bar
├────────────────────────────────────────────────────────────┤
│                                                            │
│  FDA 510(k) Pre-market Notification                       │
│  Device XYZ Submission                                     │
│                                                            │
│  DOC-2026-0087                                            │
│                                                            │
│  [NO DIAGONAL WATERMARK]                                   │  ← Clean document
│                                                            │
│  Executive Summary:                                        │
│  This submission provides...                               │
│                                                            │
│  Device Description:                                       │
│  ...                                                       │
│                                                            │
│  Clinical Data:                                            │
│  ...                                                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Styling Details:**
- **Header Bar**: Purple (#7c3aed), White text, 14pt bold, centered
- **No Diagonal**: Document is EFFECTIVE - clean for use

---

### Example 3: EFFECTIVE + INTERNAL Document (Standard SOP)

```
┌────────────────────────────────────────────────────────────┐
│ [NO HEADER BAR]                                            │  ← INTERNAL = no header
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Standard Operating Procedure                             │
│  Document Control Process                                 │
│                                                            │
│  SOP-QMS-001                                              │
│  Version 2.0                                               │
│                                                            │
│  [NO DIAGONAL WATERMARK]                                   │  ← Clean document
│                                                            │
│  Purpose:                                                  │
│  This procedure defines...                                 │
│                                                            │
│  Scope:                                                    │
│  This SOP applies to all quality documents...             │
│                                                            │
│  Procedure:                                                │
│  ...                                                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Styling Details:**
- **No Header**: INTERNAL documents have no sensitivity header (optional: can show light blue)
- **No Diagonal**: Document is EFFECTIVE - standard approved document

---

### Example 4: OBSOLETE + PROPRIETARY Document

```
┌────────────────────────────────────────────────────────────┐
│ PROPRIETARY - TRADE SECRET                                 │  ← Red bar
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Manufacturing Process Specification                       │
│  Proprietary Coating Method                               │
│                                                            │
│  PROC-2025-0012                                           │
│                OBSOLETE                                    │  ← Gray diagonal (30% opacity)
│  Process Overview:                                         │
│  The coating        DO NOT USE                            │
│  process utilizes...                                      │
│                                                            │
│  Materials:                                                │
│  - Proprietary compound XYZ                               │
│  - ...                                                     │
│                                                            │
│  Critical Parameters:                                      │
│  ...                                                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Styling Details:**
- **Header Bar**: Red (#dc2626), White text, 14pt bold, centered
- **Diagonal**: Gray (#6b7280), "OBSOLETE\nDO NOT USE", 60pt bold, 30% opacity, 45° rotation

---

### Example 5: UNDER_REVIEW + CONFIDENTIAL Document

```
┌────────────────────────────────────────────────────────────┐
│ CONFIDENTIAL                                               │  ← Orange bar
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Customer Service Agreement                               │
│  Acme Corporation                                          │
│                                                            │
│  CONT-2026-0023                                           │
│               UNDER REVIEW                                 │  ← Yellow/Orange diagonal (20% opacity)
│  Agreement Terms:                                          │
│  ...                                                       │
│                                                            │
│  Pricing Schedule:                                         │
│  ...                                                       │
│                                                            │
│  Deliverables:                                             │
│  ...                                                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Styling Details:**
- **Header Bar**: Orange (#ea580c), White text, 14pt bold, centered
- **Diagonal**: Yellow/Orange (#f59e0b), "UNDER REVIEW", 60pt bold, 20% opacity, 45° rotation

---

### Example 6: APPROVED_PENDING_EFFECTIVE + RESTRICTED

```
┌────────────────────────────────────────────────────────────┐
│ RESTRICTED - REGULATORY/COMPLIANCE                         │  ← Purple bar
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Post-Market Surveillance Report                          │
│  Annual Summary 2025                                       │
│                                                            │
│  REG-2026-0156                                            │
│                 APPROVED                                   │  ← Blue diagonal (15% opacity)
│  Executive Summary:                                        │
│            PENDING EFFECTIVE                               │
│  This report...                                           │
│                                                            │
│  Adverse Events:                                           │
│  ...                                                       │
│                                                            │
│  Corrective Actions:                                       │
│  ...                                                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Styling Details:**
- **Header Bar**: Purple (#7c3aed), White text, 14pt bold, centered
- **Diagonal**: Blue (#3b82f6), "APPROVED\nPENDING EFFECTIVE", 60pt bold, 15% opacity, 45° rotation

---

## Color Palette Reference

### Sensitivity Header Colors

| Sensitivity | Color | Hex Code | Use Case |
|------------|--------|----------|----------|
| **CONFIDENTIAL** | Orange | `#ea580c` | Business confidential |
| **RESTRICTED** | Purple | `#7c3aed` | Regulatory/compliance |
| **PROPRIETARY** | Red | `#dc2626` | Trade secrets |
| **INTERNAL** (optional) | Blue | `#1e40af` | Internal use |

### Status Watermark Colors

| Status | Color | Hex Code | Opacity |
|--------|--------|----------|---------|
| **DRAFT** | Red | `#ef4444` | 20% |
| **UNDER_REVIEW** | Yellow/Orange | `#f59e0b` | 20% |
| **PENDING_APPROVAL** | Blue | `#3b82f6` | 20% |
| **APPROVED_PENDING_EFFECTIVE** | Blue | `#3b82f6` | 15% |
| **OBSOLETE** | Gray | `#6b7280` | 30% |
| **SUPERSEDED** | Gray | `#6b7280` | 25% |

---

## Sizing and Positioning

### Sensitivity Header Bar
```
┌─────────────────────────────────────────┐
│ ← 0.4 inch tall header bar             │
│   Full page width                       │
│   14pt Helvetica Bold, centered         │
│   White text on colored background      │
├─────────────────────────────────────────┤
│                                         │
│   Page content starts here              │
│   (0.5" margin from header)             │
```

### Status Diagonal Watermark
```
         Center of page
              ↓
    ┌─────────────────────┐
    │                     │
    │        TEXT        /│
    │       TEXT       / │
    │      TEXT      /  │
    │             /     │
    │          /        │
    │       /           │
    └─────────────────────┘
    
    - Rotation: 45 degrees
    - Font: 60pt Helvetica Bold
    - Multi-line support (\n)
    - Centered on page
```

---

## Implementation Notes

### When Headers Show
- **CONFIDENTIAL**: Always show orange header
- **RESTRICTED**: Always show purple header
- **PROPRIETARY**: Always show red header
- **INTERNAL**: Optional (configurable)
- **PUBLIC**: Never show header

### When Diagonal Watermarks Show
- **DRAFT**: Always show red "DRAFT\nNOT FOR USE"
- **UNDER_REVIEW**: Show yellow "UNDER REVIEW"
- **PENDING_APPROVAL**: Show blue "PENDING APPROVAL"
- **APPROVED_PENDING_EFFECTIVE**: Show blue "APPROVED\nPENDING EFFECTIVE"
- **OBSOLETE**: Always show gray "OBSOLETE\nDO NOT USE"
- **SUPERSEDED**: Show gray "SUPERSEDED"
- **EFFECTIVE**: Never show diagonal (clean document)
- **APPROVED_AND_EFFECTIVE**: Never show diagonal (clean document)

---

## Business Rules Summary

| Document State | Sensitivity Header | Status Diagonal |
|----------------|-------------------|-----------------|
| Draft INTERNAL SOP | ❌ No header | ✅ Red "DRAFT" |
| Draft CONFIDENTIAL Contract | ✅ Orange header | ✅ Red "DRAFT" |
| Effective INTERNAL SOP | ❌ No header | ❌ Clean |
| Effective CONFIDENTIAL Audit | ✅ Orange header | ❌ Clean |
| Effective RESTRICTED FDA Sub | ✅ Purple header | ❌ Clean |
| Effective PROPRIETARY Process | ✅ Red header | ❌ Clean |
| Obsolete PROPRIETARY Process | ✅ Red header | ✅ Gray "OBSOLETE" |
| Under Review CONFIDENTIAL | ✅ Orange header | ✅ Yellow "UNDER REVIEW" |

---

## PDF Rendering Process

1. **Original PDF** - Base document content
2. **Add Sensitivity Header** - If CONFIDENTIAL+
3. **Add Status Watermark** - If not EFFECTIVE
4. **Merge Layers** - Combine all elements
5. **Final PDF** - Ready for download/viewing

---

## User Experience

### What Users See

**During Draft Stage:**
- Clear warning: "DRAFT - NOT FOR USE"
- Classification reminder at top (if applicable)
- Cannot be confused with approved document

**During Review/Approval:**
- Status clearly visible
- Classification remains visible
- Progress tracking

**After Approval (Effective):**
- Clean, professional document
- Classification header only (if CONFIDENTIAL+)
- No distracting watermarks
- Ready for operational use

---

## Testing Checklist

- [ ] DRAFT + INTERNAL → Red diagonal only
- [ ] DRAFT + CONFIDENTIAL → Orange header + Red diagonal
- [ ] EFFECTIVE + INTERNAL → Clean (no watermarks)
- [ ] EFFECTIVE + CONFIDENTIAL → Orange header only
- [ ] EFFECTIVE + RESTRICTED → Purple header only
- [ ] EFFECTIVE + PROPRIETARY → Red header only
- [ ] OBSOLETE + PROPRIETARY → Red header + Gray diagonal
- [ ] UNDER_REVIEW + CONFIDENTIAL → Orange header + Yellow diagonal
- [ ] Multiple pages → Watermarks on ALL pages

---

**This mockup guide helps developers and QA understand exactly how watermarks should appear in the final implementation.**
