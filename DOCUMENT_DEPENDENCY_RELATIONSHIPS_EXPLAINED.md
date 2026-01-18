# Document Dependency Relationships in EDMS

**Date:** January 17, 2026  
**Version:** 1.2.0+

---

## Overview

Document dependencies in EDMS track **relationships between documents** to ensure proper change control, impact analysis, and compliance. When one document changes, you can see which other documents are affected.

---

## The 6 Types of Dependencies

### 1. **REFERENCE** 📖
**Meaning:** "This document references/cites another document"

**Use Case:** When a document mentions or refers to another document for additional information.

**Example:**
- SOP-001 (Training Procedure) **REFERENCES** POL-005 (Training Policy)
- The SOP mentions the policy but doesn't implement it directly

**Relationship:**
```
Document A ──REFERENCES──> Document B
"A mentions B for additional context"
```

**Impact:**
- **Light coupling** - Changes to B may require updating references in A
- A doesn't depend on B's content, just references it
- Common in cross-referencing between related procedures

---

### 2. **TEMPLATE** 📋
**Meaning:** "This document uses another document as a template"

**Use Case:** When a document is created based on a template document structure.

**Example:**
- SOP-002 (Lab Safety Procedure) **USES AS TEMPLATE** TMPL-001 (Standard SOP Template)
- The template provides the structure, headers, and format

**Relationship:**
```
Document A ──TEMPLATE──> Document B
"A is based on B's structure"
```

**Impact:**
- **Medium coupling** - Template changes may require reformatting A
- Content is independent, but structure is derived
- Useful for maintaining consistent document formats

---

### 3. **SUPERSEDES** 🔄
**Meaning:** "This document replaces an older version or document"

**Use Case:** Document version control and document replacement tracking.

**Example:**
- POL-006 v2.0 **SUPERSEDES** POL-006 v1.0
- New quality policy replaces old quality policy

**Relationship:**
```
Document A ──SUPERSEDES──> Document B
"A replaces B (B is now obsolete)"
```

**Impact:**
- **Strong coupling** - When A is effective, B should become obsolete
- Critical for document lifecycle management
- Used in version control and document replacement

**Special Behavior:**
- When A becomes EFFECTIVE, B should become OBSOLETE
- One-way relationship (no reciprocal dependency)
- Important for audit trail

---

### 4. **INCORPORATES** 📑
**Meaning:** "This document includes/embeds content from another document"

**Use Case:** When a document contains sections, tables, or content copied from another document.

**Example:**
- SOP-010 (Master Manufacturing Procedure) **INCORPORATES** SOP-003 (Equipment Cleaning)
- The master procedure includes the cleaning procedure as a section

**Relationship:**
```
Document A ──INCORPORATES──> Document B
"A contains content from B"
```

**Impact:**
- **Strong coupling** - Changes to B require updating A
- A contains B's content, not just a reference
- Critical for master documents that aggregate other procedures

---

### 5. **SUPPORTS** 🤝
**Meaning:** "This document provides supporting information for another document"

**Use Case:** When a document provides background, rationale, or supplementary information.

**Example:**
- RPT-001 (Validation Report) **SUPPORTS** SOP-020 (Validation Procedure)
- The report provides evidence/data supporting the procedure

**Relationship:**
```
Document A ──SUPPORTS──> Document B
"A provides evidence/data for B"
```

**Impact:**
- **Medium coupling** - Changes to A may affect B's validity
- Often used for validation/qualification relationships
- Common in regulated industries (FDA, ISO)

---

### 6. **IMPLEMENTS** ⚙️
**Meaning:** "This document implements/executes requirements from another document"

**Use Case:** When a procedure implements policy requirements or specifications.

**Example:**
- SOP-015 (Change Control Procedure) **IMPLEMENTS** POL-008 (Change Control Policy)
- The SOP provides detailed steps to execute the policy

**Relationship:**
```
Document A ──IMPLEMENTS──> Document B
"A executes the requirements defined in B"
```

**Impact:**
- **Very strong coupling** - Changes to B require reviewing/updating A
- Policy-procedure relationship
- Requirement-implementation relationship

---

## Dependency Direction & Reciprocity

### Direction Matters

Dependencies are **directional** (one-way):

```
Document A ──DEPENDS ON──> Document B
```

- **A is the source** (the document with the dependency)
- **B is the target** (the document being depended upon)

### Example:

```
SOP-001 ──IMPLEMENTS──> POL-001
```

Means:
- SOP-001 **implements** POL-001
- If POL-001 changes, SOP-001 must be reviewed
- But if SOP-001 changes, POL-001 is not affected

### Reciprocal Relationships

Some relationships are naturally reciprocal:

```
Doc A ──SUPERSEDES──> Doc B
Doc B ──SUPERSEDED_BY──> Doc A  (implied reverse relationship)
```

The system tracks one direction, but can query both:
- `document.dependencies` - Documents this document depends on
- `document.dependents` - Documents that depend on this document

---

## Practical Examples

### Example 1: Quality Management System

```
POL-001 (Quality Policy)
    ↑ IMPLEMENTS
SOP-010 (Document Control)
    ↑ IMPLEMENTS
WI-005 (Document Review Work Instruction)
    ↑ SUPPORTS
FORM-012 (Document Review Checklist)
```

### Example 2: Version Control

```
SOP-020 v3.0 ──SUPERSEDES──> SOP-020 v2.0 ──SUPERSEDES──> SOP-020 v1.0
                                                                ↓ OBSOLETE
```

### Example 3: Master Procedure

```
SOP-100 (Master Manufacturing Procedure)
    ├─ INCORPORATES ──> SOP-101 (Material Receipt)
    ├─ INCORPORATES ──> SOP-102 (Equipment Setup)
    ├─ INCORPORATES ──> SOP-103 (Production)
    └─ INCORPORATES ──> SOP-104 (Quality Control)
```

### Example 4: Complex Relationships

```
SPEC-001 (Product Specification)
    ↑ IMPLEMENTS
SOP-200 (Testing Procedure)
    ↑ SUPPORTS
RPT-050 (Validation Report)
    ↑ REFERENCES
SOP-201 (Ongoing Testing)
```

---

## Database Model

### DocumentDependency Fields

```python
class DocumentDependency(models.Model):
    uuid = UUIDField                    # Unique identifier
    document = ForeignKey               # Source document
    depends_on = ForeignKey             # Target document
    dependency_type = CharField         # One of 6 types
    notes = TextField                   # Optional explanation
    created_at = DateTimeField          # When dependency added
    created_by = ForeignKey             # Who created dependency
    is_active = BooleanField            # Active/inactive
```

### Unique Constraint

```python
unique_together = ['document', 'depends_on', 'dependency_type']
```

You **cannot** have duplicate dependencies of the same type between two documents.

---

## Impact Analysis

### When a Document Changes

If **Document B** changes:

1. Query all documents where `depends_on = B`
2. Group by `dependency_type`
3. Notify owners of dependent documents
4. Flag for review based on dependency strength

### Dependency Strength (Impact Level)

| Type | Strength | Impact When Target Changes |
|------|----------|---------------------------|
| REFERENCE | Low | May need reference update |
| TEMPLATE | Medium | May need reformatting |
| SUPPORTS | Medium | May need re-validation |
| INCORPORATES | High | Must update incorporated content |
| IMPLEMENTS | Very High | Must review compliance |
| SUPERSEDES | Critical | Lifecycle state change |

---

## UI/UX Considerations

### Displaying Dependencies

**In Document Detail View:**

```
📋 This Document Depends On:
  ✓ POL-001 (Quality Policy) - IMPLEMENTS
  ✓ TMPL-003 (SOP Template) - TEMPLATE
  
📊 Documents That Depend On This:
  ⚠ SOP-015 (Training Procedure) - IMPLEMENTS
  ⚠ SOP-020 (Audit Procedure) - IMPLEMENTS
  ℹ RPT-001 (Annual Report) - REFERENCES
```

### Visual Indicators

- ✓ Green: Active, no issues
- ⚠ Yellow: Dependent on obsolete document
- ❌ Red: Broken dependency (target deleted)
- ℹ Blue: Informational reference

---

## Change Impact Workflow

### When Document Status Changes

**Scenario:** POL-001 changes from v1.0 to v2.0

```
1. POL-001 v2.0 created
2. POL-001 v2.0 SUPERSEDES POL-001 v1.0
3. System finds dependencies:
   - SOP-010 IMPLEMENTS POL-001 v1.0
   - SOP-015 IMPLEMENTS POL-001 v1.0
   - DOC-100 REFERENCES POL-001 v1.0
4. System actions:
   - Notify owners of SOP-010, SOP-015 (high impact)
   - Flag for review
   - Optional: Auto-create change requests
```

---

## API Operations

### Common Queries

```python
# Get all dependencies of a document
document.dependencies.all()

# Get all documents that depend on this document
document.dependents.all()

# Get dependencies by type
document.dependencies.filter(dependency_type='IMPLEMENTS')

# Get all documents implementing a policy
policy.dependents.filter(dependency_type='IMPLEMENTS')

# Check if document has any dependents
if document.dependents.exists():
    print("Warning: Other documents depend on this!")
```

---

## Best Practices

### 1. Use Appropriate Types

✅ **DO:**
- Use IMPLEMENTS for policy→procedure
- Use SUPERSEDES for version control
- Use INCORPORATES when content is actually copied

❌ **DON'T:**
- Use REFERENCE for everything
- Create circular dependencies
- Use wrong type (e.g., SUPERSEDES for unrelated documents)

### 2. Document the Relationship

Always add notes explaining **why** the dependency exists:

```
SOP-010 IMPLEMENTS POL-001
Notes: "This procedure executes the requirements in Section 4.2 
       of the Quality Policy regarding document review cycles."
```

### 3. Keep Dependencies Updated

When document changes:
- Review all dependencies
- Update or remove obsolete dependencies
- Add new dependencies if relationships change

### 4. Prevent Orphans

Before obsoleting/deleting a document:
- Check for dependents
- Warn if other documents depend on it
- Require reassignment or dependency removal

---

## Future Enhancements (v1.3.0)

### Planned Features:

1. **Dependency Visualization**
   - Graph view of document relationships
   - Interactive dependency tree
   - Impact radius visualization

2. **Automatic Impact Analysis**
   - When document changes, auto-calculate impact
   - Suggest which documents need review
   - Generate change impact reports

3. **Dependency Validation**
   - Warn about circular dependencies
   - Flag orphaned dependencies
   - Suggest missing dependencies

4. **Smart Notifications**
   - Notify owners when dependencies change
   - Escalate high-impact changes
   - Batch notifications for efficiency

---

## Summary Table

| Type | Symbol | Coupling | Common Use | Reciprocal |
|------|--------|----------|------------|------------|
| REFERENCE | 📖 | Light | Cross-reference | No |
| TEMPLATE | 📋 | Medium | Format standard | No |
| SUPERSEDES | 🔄 | Critical | Version control | Yes (implied) |
| INCORPORATES | 📑 | Strong | Content inclusion | No |
| SUPPORTS | 🤝 | Medium | Evidence/validation | No |
| IMPLEMENTS | ⚙️ | Very Strong | Policy→procedure | No |

---

**Document dependencies are essential for:**
- ✅ Change impact analysis
- ✅ Document lifecycle management  
- ✅ Compliance tracking
- ✅ Quality management
- ✅ Risk mitigation

