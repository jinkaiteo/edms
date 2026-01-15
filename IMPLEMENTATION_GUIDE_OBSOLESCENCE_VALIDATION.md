# Implementation Guide: Enhanced Obsolescence Validation

## 🎯 Objective

Update obsolescence validation to check ALL versions of a document family (including SUPERSEDED) for dependencies before allowing obsolescence.

---

## 🚨 The Problem

**Current Implementation:**
- Only checks if current version has dependencies
- Ignores SUPERSEDED versions

**Issue:**
```
Policy v1.0 (SUPERSEDED) ← SOP-A depends on this ⚠️
Policy v2.0 (SUPERSEDED) ← SOP-B depends on this ⚠️
Policy v3.0 (EFFECTIVE)  ← No dependencies

Current check: ✅ Can obsolete (only checks v3.0)
Correct check: ❌ Cannot obsolete (v1.0 and v2.0 have dependencies)
```

---

## 💡 Solution

Check **ALL versions** of the document family for dependencies before allowing obsolescence.

---

## 🔧 Backend Implementation

### **Step 1: Add Family Dependency Check Method**

**File:** `backend/apps/documents/models.py`

**Add to `Document` model:**

```python
def can_obsolete_family(self):
    """
    Check if this document's entire family can be obsoleted.
    
    Checks ALL versions (including SUPERSEDED) for active dependencies.
    Returns validation result with details of blocking dependencies.
    
    Returns:
        dict: {
            'can_obsolete': bool,
            'reason': str,
            'blocking_dependencies': [
                {
                    'version': str,
                    'dependents': [
                        {
                            'document': str,
                            'title': str,
                            'status': str
                        }
                    ]
                }
            ]
        }
    """
    from apps.documents.models import DocumentDependency
    
    # Get all versions of this family
    all_versions = self.get_family_versions()
    
    blocking_dependencies = []
    
    # Check each version for dependencies
    for version in all_versions:
        # Get documents that depend on this version
        dependencies = DocumentDependency.objects.filter(
            depends_on=version,
            is_active=True
        ).select_related('document')
        
        # Filter to only EFFECTIVE or APPROVED_PENDING_EFFECTIVE dependents
        active_dependents = [
            dep.document for dep in dependencies
            if dep.document.status in ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
        ]
        
        if active_dependents:
            blocking_dependencies.append({
                'version': version.version_string,
                'document_number': version.document_number,
                'status': version.status,
                'dependent_count': len(active_dependents),
                'dependents': [
                    {
                        'uuid': str(dep.uuid),
                        'document_number': dep.document_number,
                        'title': dep.title,
                        'status': dep.status,
                        'author': dep.author.username if dep.author else None,
                    }
                    for dep in active_dependents
                ]
            })
    
    if blocking_dependencies:
        total_blocking = sum(bd['dependent_count'] for bd in blocking_dependencies)
        
        return {
            'can_obsolete': False,
            'reason': f'Cannot obsolete: {total_blocking} active document(s) depend on this family',
            'blocking_dependencies': blocking_dependencies,
            'affected_versions': len(blocking_dependencies)
        }
    
    return {
        'can_obsolete': True,
        'reason': 'No active dependencies found on any version',
        'blocking_dependencies': [],
        'affected_versions': 0
    }

def get_family_dependency_summary(self):
    """
    Get comprehensive dependency summary for entire document family.
    
    Returns summary of dependencies across all versions.
    """
    all_versions = self.get_family_versions()
    
    summary = {
        'family': {
            'base_number': self.get_base_document_number(),
            'title': self.title,
            'total_versions': all_versions.count(),
        },
        'versions': [],
        'total_dependents': 0,
        'active_dependents': 0,
    }
    
    for version in all_versions:
        dependents = version.get_current_dependents()
        active_dependents = [
            d for d in dependents 
            if d.status in ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
        ]
        
        summary['versions'].append({
            'version': version.version_string,
            'document_number': version.document_number,
            'status': version.status,
            'total_dependents': len(dependents),
            'active_dependents': len(active_dependents),
            'dependents': [
                {
                    'document_number': d.document_number,
                    'title': d.title,
                    'status': d.status
                }
                for d in dependents
            ]
        })
        
        summary['total_dependents'] += len(dependents)
        summary['active_dependents'] += len(active_dependents)
    
    return summary
```

---

### **Step 2: Update Schedule Obsolescence Method**

**File:** `backend/apps/workflows/document_lifecycle.py`

**Update the `schedule_obsolescence` function:**

```python
def schedule_obsolescence(document, obsolescence_date, reason, user):
    """
    Schedule a document FAMILY for obsolescence.
    
    IMPORTANT: Validates entire family (all versions) for dependencies.
    """
    from apps.documents.models import Document
    from django.core.exceptions import ValidationError
    
    # Validate: Only EFFECTIVE documents can be obsoleted
    if document.status != 'EFFECTIVE':
        raise ValidationError(
            "Only EFFECTIVE documents can be scheduled for obsolescence"
        )
    
    # Validate: Must be latest version
    if not document.is_latest_version():
        raise ValidationError(
            "Only the latest version can be scheduled for obsolescence"
        )
    
    # ✅ NEW: Check entire family for dependencies
    validation = document.can_obsolete_family()
    
    if not validation['can_obsolete']:
        # Format error message with details
        error_msg = validation['reason']
        blocking_details = []
        
        for block in validation['blocking_dependencies']:
            version_info = f"Version {block['version']} ({block['status']})"
            dependent_list = ', '.join([d['document_number'] for d in block['dependents']])
            blocking_details.append(f"{version_info}: {dependent_list}")
        
        raise ValidationError({
            'error': error_msg,
            'details': blocking_details,
            'blocking_dependencies': validation['blocking_dependencies']
        })
    
    # Proceed with scheduling
    document.status = 'SCHEDULED_FOR_OBSOLESCENCE'
    document.obsolescence_date = obsolescence_date
    document.obsolescence_reason = reason
    document.obsoleted_by = user
    document.save()
    
    # Create audit trail
    AuditTrail.objects.create(
        user=user,
        action='OBSOLESCENCE_SCHEDULED',
        content_object=document,
        description=f'Document family scheduled for obsolescence: {reason}',
        field_changes={
            'old_status': 'EFFECTIVE',
            'new_status': 'SCHEDULED_FOR_OBSOLESCENCE',
            'obsolescence_date': obsolescence_date.isoformat(),
            'reason': reason,
            'family_versions_count': document.get_family_versions().count(),
        }
    )
    
    # Notify stakeholders about family obsolescence
    notify_family_obsolescence_scheduled(document)
    
    return document
```

---

### **Step 3: Add API Endpoint for Validation**

**File:** `backend/apps/documents/views.py`

**Add to `DocumentViewSet`:**

```python
@action(detail=True, methods=['get'])
def can_obsolete(self, request, uuid=None):
    """
    Check if a document family can be obsoleted.
    
    GET /api/v1/documents/{uuid}/can-obsolete/
    
    Checks ALL versions of the family for active dependencies.
    
    Response:
    {
        "can_obsolete": false,
        "reason": "Cannot obsolete: 8 active documents depend on this family",
        "blocking_dependencies": [
            {
                "version": "3.0",
                "document_number": "POL-2025-0001-v03.00",
                "status": "EFFECTIVE",
                "dependent_count": 5,
                "dependents": [
                    {
                        "document_number": "SOP-2025-015-v01.00",
                        "title": "Quality Control",
                        "status": "EFFECTIVE",
                        "author": "user01"
                    },
                    ...
                ]
            },
            {
                "version": "2.0",
                "document_number": "POL-2025-0001-v02.00",
                "status": "SUPERSEDED",
                "dependent_count": 2,
                "dependents": [...]
            },
            {
                "version": "1.0",
                "document_number": "POL-2025-0001-v01.00",
                "status": "SUPERSEDED",
                "dependent_count": 1,
                "dependents": [...]
            }
        ],
        "affected_versions": 3
    }
    """
    document = self.get_object()
    validation = document.can_obsolete_family()
    
    return Response(validation)

@action(detail=True, methods=['get'])
def family_dependency_summary(self, request, uuid=None):
    """
    Get complete dependency summary for document family.
    
    GET /api/v1/documents/{uuid}/family-dependency-summary/
    
    Shows dependencies across all versions of the family.
    """
    document = self.get_object()
    summary = document.get_family_dependency_summary()
    
    return Response(summary)
```

---

## 🎨 Frontend Integration

### **Step 4: Update Schedule Obsolescence Modal**

**File:** `frontend/src/components/modals/ScheduleObsolescenceModal.tsx`

```typescript
const ScheduleObsolescenceModal = ({ document, onClose, onSuccess }) => {
  const [validating, setValidating] = useState(true);
  const [validationResult, setValidationResult] = useState(null);
  const [obsolescenceDate, setObsolescenceDate] = useState('');
  const [reason, setReason] = useState('');
  
  useEffect(() => {
    // Check if family can be obsoleted
    const validateObsolescence = async () => {
      try {
        const response = await api.get(`/documents/${document.uuid}/can-obsolete/`);
        setValidationResult(response.data);
      } catch (error) {
        console.error('Validation failed:', error);
      } finally {
        setValidating(false);
      }
    };
    
    validateObsolescence();
  }, [document.uuid]);
  
  if (validating) {
    return <div>Validating document family dependencies...</div>;
  }
  
  // Show blocking dependencies warning
  if (!validationResult.can_obsolete) {
    return (
      <Dialog open onClose={onClose}>
        <DialogTitle>Cannot Schedule Obsolescence</DialogTitle>
        <DialogContent>
          <Alert severity="error">
            {validationResult.reason}
          </Alert>
          
          <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
            Blocking Dependencies:
          </Typography>
          
          {validationResult.blocking_dependencies.map((block, idx) => (
            <Card key={idx} sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle1">
                  <strong>Version {block.version}</strong> ({block.status})
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {block.document_number}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  <strong>{block.dependent_count} document(s) depend on this version:</strong>
                </Typography>
                <List dense>
                  {block.dependents.map(dep => (
                    <ListItem key={dep.uuid}>
                      <ListItemText
                        primary={dep.document_number}
                        secondary={`${dep.title} (${dep.status})`}
                      />
                      <Button
                        size="small"
                        onClick={() => navigate(`/documents/${dep.uuid}`)}
                      >
                        View
                      </Button>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          ))}
          
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Action Required:</strong>
            </Typography>
            <Typography variant="body2">
              Before obsoleting this document family, all dependent documents 
              must be updated to remove these dependencies or be obsoleted themselves.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  }
  
  // Show obsolescence form if validation passed
  return (
    <Dialog open onClose={onClose}>
      <DialogTitle>Schedule Document Family for Obsolescence</DialogTitle>
      <DialogContent>
        <Alert severity="success" sx={{ mb: 2 }}>
          This document family can be obsoleted. No active dependencies found.
        </Alert>
        
        <Typography variant="body2" sx={{ mb: 2 }}>
          Obsoleting will retire the entire document family including all {validationResult.affected_versions || 0} versions.
        </Typography>
        
        <TextField
          fullWidth
          type="date"
          label="Obsolescence Date"
          value={obsolescenceDate}
          onChange={(e) => setObsolescenceDate(e.target.value)}
          sx={{ mb: 2 }}
          InputLabelProps={{ shrink: true }}
        />
        
        <TextField
          fullWidth
          multiline
          rows={4}
          label="Reason for Obsolescence"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Explain why this document family is being obsoleted..."
          sx={{ mb: 2 }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          color="error"
          onClick={handleScheduleObsolescence}
          disabled={!obsolescenceDate || !reason}
        >
          Schedule Obsolescence
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

---

## 📊 Dependency Summary Display

### **Step 5: Create Family Dependency Summary Component**

**File:** `frontend/src/components/documents/FamilyDependencySummary.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import api from '../../services/api';

interface Props {
  document: any;
}

export const FamilyDependencySummary: React.FC<Props> = ({ document }) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchSummary();
  }, [document.uuid]);
  
  const fetchSummary = async () => {
    try {
      const response = await api.get(`/documents/${document.uuid}/family-dependency-summary/`);
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch dependency summary:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading || !summary) {
    return <div>Loading dependency information...</div>;
  }
  
  return (
    <Card>
      <CardHeader title="Document Family Dependencies" />
      <CardContent>
        <Typography variant="body2" sx={{ mb: 2 }}>
          <strong>Family:</strong> {summary.family.base_number}
        </Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>
          <strong>Total Versions:</strong> {summary.family.total_versions}
        </Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>
          <strong>Total Dependents (all versions):</strong> {summary.total_dependents}
        </Typography>
        <Typography variant="body2" sx={{ mb: 3 }}>
          <strong>Active Dependents:</strong> {summary.active_dependents}
        </Typography>
        
        <Typography variant="h6" sx={{ mb: 2 }}>
          Dependents by Version:
        </Typography>
        
        {summary.versions.map(version => (
          <Card key={version.document_number} sx={{ mb: 2 }}>
            <CardContent>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="subtitle1">
                  Version {version.version}
                </Typography>
                <Chip
                  label={version.status}
                  size="small"
                  color={version.status === 'EFFECTIVE' ? 'success' : 'warning'}
                />
              </div>
              
              <Typography variant="body2" color="textSecondary">
                {version.document_number}
              </Typography>
              
              <Typography variant="body2" sx={{ mt: 1 }}>
                Total dependents: {version.total_dependents} 
                ({version.active_dependents} active)
              </Typography>
              
              {version.active_dependents > 0 && (
                <>
                  <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                    Active Dependents:
                  </Typography>
                  <List dense>
                    {version.dependents
                      .filter(d => ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE'].includes(d.status))
                      .map(dep => (
                        <ListItem key={dep.document_number}>
                          <ListItemText
                            primary={dep.document_number}
                            secondary={`${dep.title} (${dep.status})`}
                          />
                        </ListItem>
                      ))}
                  </List>
                </>
              )}
            </CardContent>
          </Card>
        ))}
        
        {summary.active_dependents > 0 && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            This document family has active dependents. 
            These must be updated before the family can be obsoleted.
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};
```

---

## 🧪 Testing

### **Test Case 1: Cannot Obsolete (Has Dependencies)**

**Setup:**
```sql
-- Create family with dependencies
POL-2025-0001-v01.00 (SUPERSEDED) ← SOP-A depends on this
POL-2025-0001-v02.00 (SUPERSEDED) ← SOP-B depends on this
POL-2025-0001-v03.00 (EFFECTIVE)  ← SOP-C depends on this

-- All SOPs are EFFECTIVE
```

**Test:**
```python
doc = Document.objects.get(document_number='POL-2025-0001-v03.00')
result = doc.can_obsolete_family()

assert result['can_obsolete'] == False
assert result['affected_versions'] == 3
assert len(result['blocking_dependencies']) == 3
```

**Expected:**
- ❌ Cannot obsolete
- Shows all 3 versions with dependencies
- Lists all 3 dependent documents
- Clear error message

---

### **Test Case 2: Can Obsolete (No Dependencies)**

**Setup:**
```sql
-- Create family without dependencies
MEM-2025-0100-v01.00 (SUPERSEDED)
MEM-2025-0100-v02.00 (EFFECTIVE)

-- No other documents depend on this family
```

**Test:**
```python
doc = Document.objects.get(document_number='MEM-2025-0100-v02.00')
result = doc.can_obsolete_family()

assert result['can_obsolete'] == True
assert result['affected_versions'] == 0
```

**Expected:**
- ✅ Can obsolete
- No blocking dependencies
- Proceeds to schedule obsolescence

---

### **Test Case 3: Mixed Dependencies**

**Setup:**
```sql
-- Create family
SOP-2025-0050-v01.00 (SUPERSEDED) ← WI-A (OBSOLETE) depends on this
SOP-2025-0050-v02.00 (SUPERSEDED) ← WI-B (DRAFT) depends on this
SOP-2025-0050-v03.00 (EFFECTIVE)  ← WI-C (EFFECTIVE) depends on this
```

**Test:**
```python
doc = Document.objects.get(document_number='SOP-2025-0050-v03.00')
result = doc.can_obsolete_family()

# Only WI-C (EFFECTIVE) is blocking
assert result['can_obsolete'] == False
assert result['affected_versions'] == 1  # Only v3.0 has active dependent
assert len(result['blocking_dependencies'][0]['dependents']) == 1
```

**Expected:**
- ❌ Cannot obsolete
- Only counts WI-C (EFFECTIVE) as blocking
- WI-A (OBSOLETE) ignored
- WI-B (DRAFT) ignored

---

## 📋 Implementation Checklist

### **Backend Changes:**
- [ ] Add `can_obsolete_family()` to Document model
- [ ] Add `get_family_dependency_summary()` to Document model
- [ ] Update `schedule_obsolescence()` to use family validation
- [ ] Add `can_obsolete` API endpoint
- [ ] Add `family_dependency_summary` API endpoint
- [ ] Update obsolescence workflow
- [ ] Add tests for family validation
- [ ] Test API endpoints

### **Frontend Changes:**
- [ ] Update `ScheduleObsolescenceModal.tsx` to show family validation
- [ ] Create `FamilyDependencySummary.tsx` component
- [ ] Add pre-validation before opening modal
- [ ] Display blocking dependencies with details
- [ ] Show affected versions count
- [ ] Add navigation to blocking documents
- [ ] Test validation flow
- [ ] Test error messages

---

## 🚨 Error Messages

### **User-Friendly Messages:**

**When validation fails:**
```
❌ Cannot Schedule Obsolescence

This document family cannot be obsoleted because 8 active documents 
depend on versions of this family:

Version 3.0 (EFFECTIVE):
  • SOP-2025-015: Quality Control Procedure
  • SOP-2025-020: Manufacturing Process
  • WI-2025-100: Equipment Calibration
  • WI-2025-105: Sample Testing
  • Form-2025-050: Inspection Checklist

Version 2.0 (SUPERSEDED):
  • SOP-2025-012: Legacy QC Process
  • WI-2025-095: Old Calibration Method

Version 1.0 (SUPERSEDED):
  • SOP-2025-010: Original Process

Action Required:
Update these documents to remove dependencies before obsoleting this family.
```

---

## 📊 API Response Examples

### **Example 1: Validation Failed**

```json
{
  "can_obsolete": false,
  "reason": "Cannot obsolete: 8 active documents depend on this family",
  "blocking_dependencies": [
    {
      "version": "3.0",
      "document_number": "POL-2025-0001-v03.00",
      "status": "EFFECTIVE",
      "dependent_count": 5,
      "dependents": [
        {
          "uuid": "...",
          "document_number": "SOP-2025-015-v01.00",
          "title": "Quality Control",
          "status": "EFFECTIVE",
          "author": "user01"
        }
      ]
    },
    {
      "version": "2.0",
      "document_number": "POL-2025-0001-v02.00",
      "status": "SUPERSEDED",
      "dependent_count": 2,
      "dependents": [...]
    }
  ],
  "affected_versions": 2
}
```

---

### **Example 2: Validation Passed**

```json
{
  "can_obsolete": true,
  "reason": "No active dependencies found on any version",
  "blocking_dependencies": [],
  "affected_versions": 0
}
```

---

## ✅ Benefits

### **1. Referential Integrity**
- ✅ No broken dependencies
- ✅ Complete validation
- ✅ Safe obsolescence

### **2. User Guidance**
- ✅ Clear error messages
- ✅ Shows exactly what's blocking
- ✅ Provides actionable steps

### **3. Compliance**
- ✅ Complete audit trail
- ✅ Prevents data integrity issues
- ✅ Validates entire family

### **4. Better UX**
- ✅ Prevents user errors
- ✅ Clear visualization
- ✅ Helpful error messages

---

## 🎯 Summary

**Enhanced Obsolescence Validation:**

✅ Checks ALL versions of family for dependencies  
✅ Shows blocking dependencies by version  
✅ Prevents obsolescence if any active dependents  
✅ Provides detailed error messages  
✅ Guides users to fix dependencies  

**Combined with Family Grouping:**

✅ SUPERSEDED versions follow latest version  
✅ Obsolete families shown together  
✅ Complete audit trail maintained  
✅ No broken dependencies  
✅ Intuitive user experience  

---

**Both implementation guides are complete and ready for next session!** 🎉

**Files Created:**
1. `IMPLEMENTATION_GUIDE_FAMILY_GROUPING.md` - Frontend family grouping
2. `IMPLEMENTATION_GUIDE_OBSOLESCENCE_VALIDATION.md` - Enhanced validation

**Ready to continue in new session!** 🚀
