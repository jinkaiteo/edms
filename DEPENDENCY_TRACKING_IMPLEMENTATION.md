# Dependency Tracking Implementation Guide

## 🎯 Objective

Track which documents need to update their dependencies when a new version is released.

---

## 📊 Three Key Questions

When Document B releases v2.0:

1. **Who depends on B?** (Current dependents)
2. **Who's using old versions?** (Outdated dependencies)
3. **Who should update?** (Update recommendations)

---

## 🔧 Implementation

### **Step 1: Add Methods to Document Model**

**File:** `backend/apps/documents/models.py`

```python
class Document(models.Model):
    # ... existing fields ...
    
    def get_current_dependents(self):
        """
        Get all documents that currently depend on THIS document.
        
        Returns:
            QuerySet of Document objects that have dependencies pointing to this document
        """
        from apps.documents.models import DocumentDependency
        
        # Get all active dependencies pointing to this document
        dependency_relationships = DocumentDependency.objects.filter(
            depends_on=self,
            is_active=True
        ).select_related('document')
        
        # Extract the documents
        dependent_docs = [dep.document for dep in dependency_relationships]
        
        return dependent_docs
    
    def get_outdated_dependents(self):
        """
        Get documents that depend on THIS document but are using an outdated version.
        
        Only relevant if this document has newer EFFECTIVE versions.
        
        Returns:
            List of dicts with dependent document info and recommended version
        """
        # First, check if there's a newer EFFECTIVE version of this document
        latest_effective = self._find_latest_effective_version_of_family()
        
        # If this IS the latest version, no documents are outdated
        if not latest_effective or latest_effective.id == self.id:
            return []
        
        # Get all documents depending on this (old) version
        current_dependents = self.get_current_dependents()
        
        outdated_info = []
        for doc in current_dependents:
            outdated_info.append({
                'document': doc,
                'document_number': doc.document_number,
                'title': doc.title,
                'status': doc.status,
                'current_version': self,
                'recommended_version': latest_effective,
                'author': doc.author,
                'is_draft': doc.status == 'DRAFT',
                'can_auto_update': doc.status == 'DRAFT',  # Only drafts can auto-update
            })
        
        return outdated_info
    
    def get_dependency_impact_report(self):
        """
        Get complete dependency impact analysis for this document.
        
        Returns comprehensive report of:
        - Current dependents
        - Outdated dependents
        - Version chain
        - Update recommendations
        """
        # Get base document number
        base_number = self._get_base_document_number()
        
        # Get all versions of this document family
        all_versions = Document.objects.filter(
            document_number__startswith=base_number
        ).order_by('-version_major', '-version_minor')
        
        # Find latest effective version
        latest_effective = all_versions.filter(
            status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
        ).first()
        
        # Get current dependents
        current_dependents = self.get_current_dependents()
        
        # Get outdated dependents (if not latest version)
        outdated_dependents = self.get_outdated_dependents() if latest_effective and latest_effective.id != self.id else []
        
        # Build report
        report = {
            'document': {
                'number': self.document_number,
                'title': self.title,
                'version': self.version_string,
                'status': self.status,
                'is_latest_effective': latest_effective and latest_effective.id == self.id,
            },
            'version_chain': {
                'total_versions': all_versions.count(),
                'latest_effective': {
                    'number': latest_effective.document_number,
                    'version': latest_effective.version_string,
                    'status': latest_effective.status,
                } if latest_effective else None,
                'all_versions': [
                    {
                        'number': v.document_number,
                        'version': v.version_string,
                        'status': v.status,
                        'effective_date': v.effective_date,
                    }
                    for v in all_versions
                ]
            },
            'dependency_impact': {
                'total_dependents': len(current_dependents),
                'outdated_dependents': len(outdated_dependents),
                'current_dependents': [
                    {
                        'number': doc.document_number,
                        'title': doc.title,
                        'status': doc.status,
                        'author': doc.author.username if doc.author else None,
                    }
                    for doc in current_dependents
                ],
                'outdated_details': outdated_dependents,
            },
            'recommendations': self._get_update_recommendations(outdated_dependents),
        }
        
        return report
    
    def _find_latest_effective_version_of_family(self):
        """Find the latest EFFECTIVE version of this document's family."""
        base_number = self._get_base_document_number()
        
        effective_versions = Document.objects.filter(
            document_number__startswith=base_number,
            status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
        )
        
        if not effective_versions.exists():
            return None
        
        # Return the one with highest version number
        return max(
            effective_versions,
            key=lambda d: (d.version_major, d.version_minor)
        )
    
    def _get_base_document_number(self):
        """Extract base document number without version suffix."""
        if '-v' in self.document_number:
            return self.document_number.split('-v')[0]
        return self.document_number
    
    def _get_update_recommendations(self, outdated_dependents):
        """Generate actionable update recommendations."""
        if not outdated_dependents:
            return []
        
        recommendations = []
        
        for info in outdated_dependents:
            doc = info['document']
            
            if info['can_auto_update']:
                recommendations.append({
                    'document': doc.document_number,
                    'action': 'AUTO_UPDATE',
                    'message': f"Draft document can be automatically updated to use {info['recommended_version'].version_string}",
                    'priority': 'LOW',
                })
            elif doc.status == 'EFFECTIVE':
                recommendations.append({
                    'document': doc.document_number,
                    'action': 'CREATE_NEW_VERSION',
                    'message': f"Create new version and dependencies will auto-upgrade to {info['recommended_version'].version_string}",
                    'priority': 'MEDIUM',
                })
            else:
                recommendations.append({
                    'document': doc.document_number,
                    'action': 'MANUAL_REVIEW',
                    'message': f"Document in {doc.status} status - review and update manually",
                    'priority': 'HIGH',
                })
        
        return recommendations
```

---

## 📡 API Endpoints

### **Add ViewSet Actions**

**File:** `backend/apps/documents/views.py`

```python
class DocumentViewSet(viewsets.ModelViewSet):
    # ... existing code ...
    
    @action(detail=True, methods=['get'])
    def dependents(self, request, uuid=None):
        """
        Get list of documents that depend on this document.
        
        GET /api/v1/documents/{uuid}/dependents/
        
        Returns:
            - List of documents depending on this document
            - Their status
            - Whether they're using outdated version
        """
        document = self.get_object()
        
        dependents = document.get_current_dependents()
        
        serializer = DocumentListSerializer(
            dependents,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'count': len(dependents),
            'document': {
                'uuid': str(document.uuid),
                'document_number': document.document_number,
                'version': document.version_string,
            },
            'dependents': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def dependency_impact(self, request, uuid=None):
        """
        Get comprehensive dependency impact analysis.
        
        GET /api/v1/documents/{uuid}/dependency-impact/
        
        Returns:
            - Current dependents
            - Outdated dependents
            - Version chain
            - Update recommendations
        """
        document = self.get_object()
        
        report = document.get_dependency_impact_report()
        
        return Response(report)
    
    @action(detail=True, methods=['get'])
    def outdated_dependents(self, request, uuid=None):
        """
        Get documents using outdated version of this document.
        
        GET /api/v1/documents/{uuid}/outdated-dependents/
        
        Returns:
            - Documents depending on old version
            - Recommended version to upgrade to
            - Update recommendations
        """
        document = self.get_object()
        
        outdated = document.get_outdated_dependents()
        
        return Response({
            'count': len(outdated),
            'document': {
                'uuid': str(document.uuid),
                'document_number': document.document_number,
                'version': document.version_string,
            },
            'outdated_dependents': outdated
        })
```

---

## 🎨 Frontend Integration

### **1. Document Detail Page - Show Dependents**

**Location:** `frontend/src/pages/DocumentDetail.tsx`

```typescript
// Fetch dependents
const [dependents, setDependents] = useState([]);
const [loading, setLoading] = useState(false);

useEffect(() => {
  const fetchDependents = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/documents/${document.uuid}/dependents/`);
      setDependents(response.data.dependents);
    } catch (error) {
      console.error('Failed to fetch dependents:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (document.uuid) {
    fetchDependents();
  }
}, [document.uuid]);

// Display dependents section
<div className="dependents-section">
  <h3>Documents Using This Document ({dependents.length})</h3>
  {dependents.length > 0 ? (
    <ul>
      {dependents.map(dep => (
        <li key={dep.uuid}>
          <a href={`/documents/${dep.uuid}`}>
            {dep.document_number} - {dep.title}
          </a>
          <span className="status-badge">{dep.status}</span>
        </li>
      ))}
    </ul>
  ) : (
    <p>No documents depend on this document.</p>
  )}
</div>
```

---

### **2. Dependency Impact Warning**

**Show warning when viewing old version:**

```typescript
const [impactReport, setImpactReport] = useState(null);

useEffect(() => {
  const fetchImpact = async () => {
    const response = await api.get(`/documents/${document.uuid}/dependency-impact/`);
    setImpactReport(response.data);
  };
  fetchImpact();
}, [document.uuid]);

// Show warning if there are outdated dependents
{impactReport && impactReport.dependency_impact.outdated_dependents > 0 && (
  <Alert severity="warning">
    <AlertTitle>Outdated Version</AlertTitle>
    <p>
      {impactReport.dependency_impact.outdated_dependents} document(s) 
      are using this version, but a newer version 
      ({impactReport.version_chain.latest_effective.version}) is available.
    </p>
    <Button onClick={() => navigate(`/documents/${impactReport.version_chain.latest_effective.uuid}`)}>
      View Latest Version
    </Button>
  </Alert>
)}
```

---

### **3. Update Recommendations Dashboard**

**New component for document owners:**

```typescript
const UpdateRecommendations = () => {
  const [recommendations, setRecommendations] = useState([]);
  
  useEffect(() => {
    // Fetch all documents owned by user that have outdated dependencies
    const fetchRecommendations = async () => {
      const response = await api.get('/documents/update-recommendations/');
      setRecommendations(response.data);
    };
    fetchRecommendations();
  }, []);
  
  return (
    <div className="update-recommendations">
      <h2>Dependency Update Recommendations</h2>
      {recommendations.map(rec => (
        <div key={rec.document_uuid} className="recommendation-card">
          <h3>{rec.document_number}</h3>
          <p>Using outdated dependency: {rec.outdated_dependency}</p>
          <p>Recommended: Update to {rec.recommended_version}</p>
          <Button onClick={() => handleUpdate(rec)}>
            {rec.action === 'AUTO_UPDATE' ? 'Auto Update' : 'Create New Version'}
          </Button>
        </div>
      ))}
    </div>
  );
};
```

---

## 🔔 Notification System

### **Send Notifications When New Version Released**

**File:** `backend/apps/workflows/document_lifecycle.py`

```python
def notify_dependent_document_owners(document):
    """
    Notify owners of dependent documents when new version is approved.
    
    Called when document becomes EFFECTIVE.
    """
    from apps.notifications.models import Notification
    
    # Get all documents depending on this one
    dependents = document.get_current_dependents()
    
    # Get unique owners
    owners = set()
    for dep in dependents:
        if dep.author:
            owners.add(dep.author)
    
    # Create notifications
    for owner in owners:
        Notification.objects.create(
            user=owner,
            notification_type='DEPENDENCY_UPDATE_AVAILABLE',
            title=f'New version of {document.document_number} available',
            message=f'''
                A new version ({document.version_string}) of {document.document_number} 
                is now EFFECTIVE. You have document(s) that depend on this document.
                
                Consider updating your documents to use the latest version.
            ''',
            related_object=document,
            action_url=f'/documents/{document.uuid}/dependents/',
        )
```

---

## 📊 Usage Examples

### **Example 1: Check Who Uses a Document**

```python
# In Django shell or view
document = Document.objects.get(document_number='POL-2025-001-v01.00')

# Get current dependents
dependents = document.get_current_dependents()
print(f"Documents using POL-2025-001 v1.0: {len(dependents)}")
for dep in dependents:
    print(f"  - {dep.document_number}: {dep.title}")

# Output:
# Documents using POL-2025-001 v1.0: 5
#   - SOP-2025-015-v01.00: Quality Control Procedure
#   - SOP-2025-020-v01.00: Manufacturing Process
#   - WI-2025-100-v01.00: Equipment Calibration
#   - WI-2025-105-v01.00: Sample Testing
#   - Form-2025-050-v01.00: Inspection Checklist
```

---

### **Example 2: Find Outdated Dependencies**

```python
# Check if documents are using old version
old_version = Document.objects.get(document_number='POL-2025-001-v01.00')
outdated = old_version.get_outdated_dependents()

if outdated:
    print(f"Found {len(outdated)} documents using outdated version:")
    for info in outdated:
        print(f"  - {info['document_number']}")
        print(f"    Status: {info['status']}")
        print(f"    Should upgrade to: {info['recommended_version'].version_string}")
        print(f"    Can auto-update: {info['can_auto_update']}")
```

---

### **Example 3: Generate Impact Report**

```python
# Get comprehensive report
document = Document.objects.get(document_number='POL-2025-001-v02.00')
report = document.get_dependency_impact_report()

print(f"Document: {report['document']['number']}")
print(f"Total dependents: {report['dependency_impact']['total_dependents']}")
print(f"Outdated dependents: {report['dependency_impact']['outdated_dependents']}")
print(f"\nRecommendations:")
for rec in report['recommendations']:
    print(f"  - {rec['document']}: {rec['action']} ({rec['priority']})")
```

---

## 🎯 Use Cases

### **Use Case 1: Before Approving New Version**

**User Story:** As an approver, I want to know which documents will be affected before I approve a new version.

**Implementation:**
```typescript
// Show impact before approval
const handleApprove = async () => {
  // Fetch impact report first
  const impact = await api.get(`/documents/${doc.uuid}/dependency-impact/`);
  
  // Show confirmation dialog
  if (impact.data.dependency_impact.total_dependents > 0) {
    const confirmed = await showDialog({
      title: 'Approve Document',
      message: `
        This document is used by ${impact.data.dependency_impact.total_dependents} other documents.
        Approving will make this version available as the latest effective version.
      `,
      showDependentsList: impact.data.dependency_impact.current_dependents
    });
    
    if (!confirmed) return;
  }
  
  // Proceed with approval
  await api.post(`/documents/${doc.uuid}/approve/`, data);
};
```

---

### **Use Case 2: Automated Update Suggestions**

**User Story:** As a document owner, I want to be notified when my dependencies have newer versions.

**Implementation:**
```python
# Daily scheduled task (Celery)
@shared_task
def check_outdated_dependencies():
    """Check all EFFECTIVE documents for outdated dependencies."""
    
    effective_docs = Document.objects.filter(status='EFFECTIVE')
    
    for doc in effective_docs:
        outdated_deps = []
        
        # Check each dependency
        for dep in doc.dependencies.filter(is_active=True):
            dependent_doc = dep.depends_on
            latest = dependent_doc._find_latest_effective_version_of_family()
            
            # If using old version
            if latest and latest.id != dependent_doc.id:
                outdated_deps.append({
                    'current': dependent_doc,
                    'latest': latest
                })
        
        # Notify owner if outdated dependencies found
        if outdated_deps and doc.author:
            Notification.objects.create(
                user=doc.author,
                notification_type='OUTDATED_DEPENDENCIES',
                title=f'Outdated dependencies in {doc.document_number}',
                message=f'Your document has {len(outdated_deps)} outdated dependencies.',
                related_object=doc,
            )
```

---

### **Use Case 3: Dependency Health Dashboard**

**User Story:** As a quality manager, I want to see all documents with outdated dependencies.

**Implementation:**
```python
# API endpoint
@action(detail=False, methods=['get'])
def dependency_health(self, request):
    """Get system-wide dependency health report."""
    
    effective_docs = Document.objects.filter(status='EFFECTIVE')
    
    docs_with_outdated_deps = []
    
    for doc in effective_docs:
        has_outdated = False
        outdated_list = []
        
        for dep in doc.dependencies.filter(is_active=True):
            dependent_doc = dep.depends_on
            latest = dependent_doc._find_latest_effective_version_of_family()
            
            if latest and latest.id != dependent_doc.id:
                has_outdated = True
                outdated_list.append({
                    'using': dependent_doc.document_number,
                    'latest': latest.document_number,
                })
        
        if has_outdated:
            docs_with_outdated_deps.append({
                'document': doc.document_number,
                'title': doc.title,
                'author': doc.author.username if doc.author else None,
                'outdated_count': len(outdated_list),
                'outdated_dependencies': outdated_list,
            })
    
    return Response({
        'total_effective_documents': effective_docs.count(),
        'documents_with_outdated_dependencies': len(docs_with_outdated_deps),
        'details': docs_with_outdated_deps,
    })
```

---

## ✅ Summary

### **Tracking Methods:**

| Method | What It Tracks | Use Case |
|--------|----------------|----------|
| `get_current_dependents()` | Who uses this document | Impact analysis |
| `get_outdated_dependents()` | Who's using old version | Update recommendations |
| `get_dependency_impact_report()` | Complete analysis | Comprehensive view |

### **Key Features:**

1. ✅ **Real-time tracking** - Always accurate
2. ✅ **No extra tables** - Uses existing relationships
3. ✅ **Smart recommendations** - Actionable advice
4. ✅ **Notification support** - Proactive alerts
5. ✅ **Frontend integration** - User-friendly display

---

**Would you like me to:**
- **A)** Implement this tracking system now?
- **B)** Show more frontend UI examples?
- **C)** Add automatic update features?
- **D)** Implement the full dependency copying + tracking solution?

This tracking system works perfectly with the automatic dependency copying we discussed earlier! 🚀
