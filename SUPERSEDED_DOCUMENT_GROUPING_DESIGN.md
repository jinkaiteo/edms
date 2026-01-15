# SUPERSEDED Document Grouping Design

## 🎯 Core Concept

**SUPERSEDED documents should "follow" their latest version wherever it goes.**

This means SUPERSEDED versions are **grouped with their document family** and appear in the same location as the latest version of that family.

---

## 💡 Design Philosophy

### **Key Principle:**

> "SUPERSEDED documents are not independently obsolete - they are part of a living document family. They should be visible alongside the current version of that family."

### **Why This Matters:**

1. **Referential Integrity**
   - Dependencies don't break
   - Users see full context
   - Version history accessible

2. **User Understanding**
   - Clear relationship between versions
   - Easy to find related documents
   - Natural document grouping

3. **Compliance**
   - Complete audit trail
   - Version history always available
   - No orphaned documents

---

## 📊 Document Location Rules

### **Rule 1: Latest Version Determines Location**

The **entire document family** appears based on the **latest version's status**.

```
IF latest version is EFFECTIVE:
  → Show family in Document Library
  → Include all SUPERSEDED versions in the group

IF latest version is OBSOLETE:
  → Move entire family to Obsolete Documents
  → Include all SUPERSEDED versions in the group
```

---

### **Rule 2: Version Grouping**

Documents are displayed as **families**, not individual versions.

**Visual Representation:**
```
📄 Quality Control SOP [Document Family]
  ├─ v3.0 (EFFECTIVE) ← Latest
  ├─ v2.0 (SUPERSEDED)
  └─ v1.0 (SUPERSEDED)
```

---

## 📋 Location Examples

### **Example 1: Active Document Family**

**Family Status:**
- Latest: Quality SOP v3.0 (EFFECTIVE)
- Previous: Quality SOP v2.0 (SUPERSEDED)
- Previous: Quality SOP v1.0 (SUPERSEDED)

**Location:** Document Library ✅

**Visible as:**
```
┌─────────────────────────────────────────────────────┐
│ 📄 Quality Control SOP                              │
│    Current: v3.0 (EFFECTIVE)                        │
│    [View Current] [Version History ▼]              │
│                                                     │
│    Version History:                                 │
│    ├─ v3.0 (EFFECTIVE) - 2025-01-10                │
│    ├─ v2.0 (SUPERSEDED) - 2023-06-15               │
│    └─ v1.0 (SUPERSEDED) - 2021-03-20               │
└─────────────────────────────────────────────────────┘
```

---

### **Example 2: Obsolete Document Family**

**Family Status:**
- Latest: COVID Screening SOP v2.0 (OBSOLETE)
- Previous: COVID Screening SOP v1.0 (SUPERSEDED)

**Location:** Obsolete Documents Page ✅

**Visible as:**
```
┌─────────────────────────────────────────────────────┐
│ 📄 COVID Screening SOP [OBSOLETE FAMILY]           │
│    Latest: v2.0 (OBSOLETE) - 2025-05-01            │
│    Reason: Process discontinued                     │
│    [Version History ▼]                             │
│                                                     │
│    All Versions:                                    │
│    ├─ v2.0 (OBSOLETE) - 2023-12-10                 │
│    └─ v1.0 (SUPERSEDED) - 2020-03-15               │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Dependency Implications

### **Critical Insight:**

When obsoleting a document, you must check **ALL versions** of that family for dependencies, not just the current version.

### **Why?**

**Scenario:**
```
Policy v1.0 (SUPERSEDED) ← SOP-A v1.0 depends on this
Policy v2.0 (SUPERSEDED) ← SOP-B v1.0 depends on this
Policy v3.0 (EFFECTIVE)  ← SOP-C v1.0 depends on this

User wants to obsolete Policy family (all versions)
```

**Must check:**
- Dependencies on Policy v1.0 ✅
- Dependencies on Policy v2.0 ✅
- Dependencies on Policy v3.0 ✅

**If ANY version has active dependencies → Cannot obsolete!**

---

## 🚨 Obsolescence Validation Logic

### **Before Obsoleting a Document:**

```python
def can_obsolete_document_family(document):
    """
    Check if a document family can be obsoleted.
    
    Must check ALL versions (including SUPERSEDED) for dependencies.
    """
    # Get all versions of this document family
    base_number = document.get_base_document_number()
    all_versions = Document.objects.filter(
        document_number__startswith=base_number
    )
    
    # Check each version for active dependencies
    blocking_dependencies = []
    
    for version in all_versions:
        # Get documents that depend on this version
        dependents = version.get_current_dependents()
        
        # Filter to only EFFECTIVE dependents
        active_dependents = [
            dep for dep in dependents 
            if dep.status in ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
        ]
        
        if active_dependents:
            blocking_dependencies.append({
                'version': version.version_string,
                'dependents': [
                    {
                        'document': dep.document_number,
                        'title': dep.title,
                        'status': dep.status,
                    }
                    for dep in active_dependents
                ]
            })
    
    if blocking_dependencies:
        return {
            'can_obsolete': False,
            'reason': 'Active documents depend on versions of this document family',
            'blocking_dependencies': blocking_dependencies
        }
    
    return {
        'can_obsolete': True,
        'reason': 'No active dependencies found',
        'blocking_dependencies': []
    }
```

---

## 📊 Frontend Implementation

### **Document Library Display:**

**Grouped by Family:**
```typescript
interface DocumentFamily {
  baseNumber: string;
  title: string;
  latestVersion: Document;
  allVersions: Document[];
  isActive: boolean; // Based on latest version
}

const DocumentLibrary = () => {
  const [families, setFamilies] = useState<DocumentFamily[]>([]);
  
  // Group documents by family
  const groupByFamily = (documents: Document[]) => {
    const familyMap = new Map();
    
    documents.forEach(doc => {
      const baseNumber = doc.document_number.split('-v')[0];
      
      if (!familyMap.has(baseNumber)) {
        familyMap.set(baseNumber, []);
      }
      
      familyMap.get(baseNumber).push(doc);
    });
    
    // Convert to families with latest version
    return Array.from(familyMap.entries()).map(([baseNumber, versions]) => {
      // Sort by version descending
      const sorted = versions.sort((a, b) => {
        if (a.version_major !== b.version_major) {
          return b.version_major - a.version_major;
        }
        return b.version_minor - a.version_minor;
      });
      
      const latest = sorted[0];
      
      return {
        baseNumber,
        title: latest.title,
        latestVersion: latest,
        allVersions: sorted,
        isActive: ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE'].includes(latest.status)
      };
    });
  };
  
  // Filter: Only show families where latest is EFFECTIVE
  const activeFamily = families.filter(f => f.isActive);
  
  return (
    <div>
      {activeFamilies.map(family => (
        <DocumentFamilyCard key={family.baseNumber} family={family} />
      ))}
    </div>
  );
};
```

---

### **Document Family Card:**

```typescript
const DocumentFamilyCard = ({ family }: { family: DocumentFamily }) => {
  const [showVersions, setShowVersions] = useState(false);
  
  return (
    <Card>
      <CardHeader>
        <h3>{family.title}</h3>
        <StatusBadge status={family.latestVersion.status} />
      </CardHeader>
      
      <CardContent>
        <div>
          <strong>Current Version:</strong> {family.latestVersion.version_string}
        </div>
        
        <div>
          <strong>Last Updated:</strong> {family.latestVersion.updated_at}
        </div>
        
        {family.allVersions.length > 1 && (
          <Button 
            variant="text" 
            onClick={() => setShowVersions(!showVersions)}
          >
            Version History ({family.allVersions.length}) 
            {showVersions ? '▲' : '▼'}
          </Button>
        )}
        
        {showVersions && (
          <VersionHistory>
            {family.allVersions.map(version => (
              <VersionItem key={version.uuid}>
                <VersionBadge status={version.status} />
                <span>
                  v{version.version_string} - {version.effective_date}
                </span>
                <Link to={`/documents/${version.uuid}`}>View</Link>
              </VersionItem>
            ))}
          </VersionHistory>
        )}
      </CardContent>
      
      <CardActions>
        <Button onClick={() => navigate(`/documents/${family.latestVersion.uuid}`)}>
          View Current Version
        </Button>
        <Button onClick={() => navigate(`/documents/${family.baseNumber}/history`)}>
          Full History
        </Button>
      </CardActions>
    </Card>
  );
};
```

---

### **Obsolete Documents Page:**

```typescript
const ObsoleteDocuments = () => {
  const [obsoleteFamilies, setObsoleteFamilies] = useState<DocumentFamily[]>([]);
  
  useEffect(() => {
    // Fetch families where latest version is OBSOLETE
    const fetchObsolete = async () => {
      const response = await api.get('/documents/obsolete-families/');
      setObsoleteFamilies(response.data);
    };
    fetchObsolete();
  }, []);
  
  return (
    <div>
      <h1>Obsolete Document Families</h1>
      <p>
        These document families have been retired. 
        All versions (including superseded) are shown here.
      </p>
      
      {obsoleteFamilies.map(family => (
        <ObsoleteFamilyCard key={family.baseNumber} family={family} />
      ))}
    </div>
  );
};

const ObsoleteFamilyCard = ({ family }) => {
  return (
    <Card className="obsolete">
      <CardHeader>
        <h3>{family.title}</h3>
        <Badge color="error">OBSOLETE FAMILY</Badge>
      </CardHeader>
      
      <CardContent>
        <Alert severity="error">
          This entire document family has been obsoleted.
          
          <div>
            <strong>Reason:</strong> {family.latestVersion.obsolescence_reason}
          </div>
          <div>
            <strong>Obsoleted:</strong> {family.latestVersion.obsolescence_date}
          </div>
        </Alert>
        
        <div className="version-list">
          <strong>All Versions (for reference only):</strong>
          {family.allVersions.map(version => (
            <div key={version.uuid}>
              {version.version_string} 
              ({version.status}) 
              - {version.effective_date}
              <Link to={`/documents/${version.uuid}`}>View</Link>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
```

---

## 🔧 Backend API Endpoints

### **Endpoint 1: Get Document Families (Active)**

```python
@action(detail=False, methods=['get'])
def families(self, request):
    """
    Get document families grouped by base number.
    Only returns families where latest version is EFFECTIVE.
    """
    # Get all effective and superseded documents
    documents = Document.objects.filter(
        status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE', 'SUPERSEDED']
    ).order_by('document_number', '-version_major', '-version_minor')
    
    # Group by family
    families = {}
    for doc in documents:
        base_number = doc.document_number.split('-v')[0]
        
        if base_number not in families:
            families[base_number] = []
        
        families[base_number].append(doc)
    
    # Filter: only families where latest is EFFECTIVE
    active_families = []
    for base_number, versions in families.items():
        latest = versions[0]  # Already sorted
        
        if latest.status in ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']:
            serializer = DocumentDetailSerializer(versions, many=True, context={'request': request})
            active_families.append({
                'base_number': base_number,
                'title': latest.title,
                'latest_version': versions[0].uuid,
                'all_versions': serializer.data
            })
    
    return Response({
        'count': len(active_families),
        'families': active_families
    })
```

---

### **Endpoint 2: Get Obsolete Families**

```python
@action(detail=False, methods=['get'])
def obsolete_families(self, request):
    """
    Get document families where latest version is OBSOLETE.
    Includes all superseded versions in the family.
    """
    # Get all obsolete and superseded documents
    documents = Document.objects.filter(
        status__in=['OBSOLETE', 'SUPERSEDED']
    ).order_by('document_number', '-version_major', '-version_minor')
    
    # Group by family
    families = {}
    for doc in documents:
        base_number = doc.document_number.split('-v')[0]
        
        if base_number not in families:
            families[base_number] = []
        
        families[base_number].append(doc)
    
    # Filter: only families where latest is OBSOLETE
    obsolete_families = []
    for base_number, versions in families.items():
        latest = versions[0]
        
        if latest.status == 'OBSOLETE':
            serializer = DocumentDetailSerializer(versions, many=True, context={'request': request})
            obsolete_families.append({
                'base_number': base_number,
                'title': latest.title,
                'latest_version': latest.uuid,
                'obsolescence_date': latest.obsolescence_date,
                'obsolescence_reason': latest.obsolescence_reason,
                'all_versions': serializer.data
            })
    
    return Response({
        'count': len(obsolete_families),
        'families': obsolete_families
    })
```

---

### **Endpoint 3: Check Can Obsolete (with full family check)**

```python
@action(detail=True, methods=['get'])
def can_obsolete(self, request, uuid=None):
    """
    Check if a document family can be obsoleted.
    Checks ALL versions for dependencies.
    """
    document = self.get_object()
    result = can_obsolete_document_family(document)
    
    return Response(result)
```

---

## 🚨 Obsolescence Workflow Update

### **Before Obsoleting:**

```python
def schedule_obsolescence(document, approver, obsolescence_date, reason):
    """
    Schedule a document FAMILY for obsolescence.
    """
    # Validate: Check all versions for dependencies
    validation = can_obsolete_document_family(document)
    
    if not validation['can_obsolete']:
        raise ValidationError({
            'error': 'Cannot obsolete document family',
            'reason': validation['reason'],
            'blocking_dependencies': validation['blocking_dependencies']
        })
    
    # Get all versions
    base_number = document.get_base_document_number()
    all_versions = Document.objects.filter(
        document_number__startswith=base_number
    )
    
    # Get latest version
    latest = max(all_versions, key=lambda d: (d.version_major, d.version_minor))
    
    # Only latest version gets scheduled
    if latest.status != 'EFFECTIVE':
        raise ValidationError("Only EFFECTIVE documents can be obsoleted")
    
    latest.status = 'SCHEDULED_FOR_OBSOLESCENCE'
    latest.obsolescence_date = obsolescence_date
    latest.obsolescence_reason = reason
    latest.obsoleted_by = approver
    latest.save()
    
    # Notify stakeholders
    notify_family_obsolescence_scheduled(latest, all_versions)
```

---

### **When Obsolescence Date Reached:**

```python
def process_scheduled_obsolescence():
    """
    Process scheduled obsolescence.
    Only the latest version changes to OBSOLETE.
    SUPERSEDED versions remain SUPERSEDED (they follow the family).
    """
    due_docs = Document.objects.filter(
        status='SCHEDULED_FOR_OBSOLESCENCE',
        obsolescence_date__lte=timezone.now().date()
    )
    
    for doc in due_docs:
        # Change latest version to OBSOLETE
        doc.status = 'OBSOLETE'
        doc.save()
        
        # SUPERSEDED versions don't change status
        # They remain SUPERSEDED but are now part of an obsolete family
        
        # Notify
        notify_family_obsoleted(doc)
```

---

## 📊 User Experience Flow

### **Scenario: User Wants to Obsolete a Document**

```
Step 1: User selects "Schedule Obsolescence" for Policy v3.0
  ↓
Step 2: System checks ALL versions for dependencies
  - Policy v3.0 (EFFECTIVE): 5 dependencies
  - Policy v2.0 (SUPERSEDED): 2 dependencies
  - Policy v1.0 (SUPERSEDED): 1 dependency
  ↓
Step 3: System shows warning
  "Cannot obsolete: 8 documents depend on this family
   
   Dependencies:
   - SOP-2025-015 depends on Policy v3.0
   - SOP-2025-020 depends on Policy v3.0
   - ...
   - WI-2025-100 depends on Policy v2.0 (SUPERSEDED version)
   - ...
   
   Action: Update these documents to remove dependencies first."
  ↓
Step 4: User updates dependent documents
  ↓
Step 5: Try again - all dependencies removed
  ↓
Step 6: System schedules entire family for obsolescence
  "Policy family will be obsoleted on 2025-06-01"
  ↓
Step 7: On 2025-06-01, entire family moves to Obsolete Documents
  - Policy v3.0: OBSOLETE
  - Policy v2.0: SUPERSEDED (in obsolete family)
  - Policy v1.0: SUPERSEDED (in obsolete family)
```

---

## ✅ Benefits of This Approach

### **1. Referential Integrity**
- Dependencies tracked across all versions
- No broken links
- Complete dependency validation

### **2. User Understanding**
- Clear family grouping
- Easy to find related versions
- Natural organization

### **3. Compliance**
- Complete audit trail
- All versions accessible
- Clear retirement process

### **4. Consistency**
- Logical grouping
- Predictable location
- Clear relationship between versions

---

## 🎯 Summary

### **Key Rules:**

1. **SUPERSEDED documents follow their latest version**
   - Latest EFFECTIVE → Family in Document Library
   - Latest OBSOLETE → Family in Obsolete Documents

2. **Obsolescence checks ALL versions**
   - Check v3.0 (EFFECTIVE)
   - Check v2.0 (SUPERSEDED)
   - Check v1.0 (SUPERSEDED)
   - Any dependencies → Cannot obsolete

3. **Family-based display**
   - Group by base document number
   - Show latest version prominently
   - Expand to show version history

4. **Only latest version changes to OBSOLETE**
   - SUPERSEDED versions stay SUPERSEDED
   - They become part of an obsolete family
   - Location changes but status doesn't

---

**This design maintains referential integrity while providing excellent UX!** 🎯

Would you like me to:
- **A)** Implement this family-based grouping in the frontend?
- **B)** Update the obsolescence validation logic?
- **C)** Create the API endpoints for family views?
- **D)** All of the above?
