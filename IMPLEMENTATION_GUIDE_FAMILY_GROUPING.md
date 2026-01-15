# Implementation Guide: Document Family Grouping

## 🎯 Objective

Implement family-based document grouping where SUPERSEDED documents follow their latest version's location.

---

## 📋 Implementation Overview

### **Part A: Frontend Family Grouping**
- Group documents by base number (document family)
- Display latest version prominently
- Show version history on expansion
- Filter families by latest version status

### **Files to Modify:**
1. `frontend/src/pages/DocumentLibrary.tsx`
2. `frontend/src/pages/ObsoleteDocuments.tsx` (new file)
3. `frontend/src/components/documents/DocumentFamilyCard.tsx` (new file)
4. `frontend/src/services/api.ts`

---

## 🔧 Backend Implementation

### **Step 1: Add Helper Methods to Document Model**

**File:** `backend/apps/documents/models.py`

**Add these methods to the `Document` class:**

```python
class Document(models.Model):
    # ... existing fields ...
    
    def get_base_document_number(self):
        """
        Extract base document number without version suffix.
        
        Examples:
            POL-2025-0001-v02.00 → POL-2025-0001
            SOP-2025-0015-v01.05 → SOP-2025-0015
        
        Returns:
            str: Base document number
        """
        if '-v' in self.document_number:
            return self.document_number.split('-v')[0]
        return self.document_number
    
    @classmethod
    def get_document_families(cls, status_filter=None):
        """
        Get all document families grouped by base number.
        
        Args:
            status_filter: List of statuses to include (default: all)
        
        Returns:
            dict: {
                'base_number': {
                    'title': str,
                    'latest_version': Document,
                    'all_versions': [Document, ...],
                    'is_active': bool,
                    'is_obsolete': bool
                }
            }
        """
        # Query documents
        queryset = cls.objects.all()
        if status_filter:
            queryset = queryset.filter(status__in=status_filter)
        
        # Order by version (descending)
        queryset = queryset.order_by(
            'document_number',
            '-version_major',
            '-version_minor'
        )
        
        # Group by family
        families = {}
        
        for doc in queryset:
            base_number = doc.get_base_document_number()
            
            if base_number not in families:
                families[base_number] = {
                    'title': doc.title,
                    'latest_version': doc,
                    'all_versions': [],
                    'is_active': False,
                    'is_obsolete': False
                }
            
            families[base_number]['all_versions'].append(doc)
        
        # Set family status based on latest version
        for base_number, family_data in families.items():
            latest = family_data['latest_version']
            family_data['is_active'] = latest.status in ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
            family_data['is_obsolete'] = latest.status == 'OBSOLETE'
        
        return families
    
    def get_family_versions(self):
        """
        Get all versions of this document's family.
        
        Returns:
            QuerySet: All versions ordered by version number descending
        """
        base_number = self.get_base_document_number()
        
        return Document.objects.filter(
            document_number__startswith=base_number
        ).order_by('-version_major', '-version_minor')
    
    def get_latest_version_of_family(self):
        """
        Get the latest version of this document's family.
        
        Returns:
            Document: Latest version by version number
        """
        versions = self.get_family_versions()
        return versions.first() if versions.exists() else self
    
    def is_latest_version(self):
        """
        Check if this document is the latest version of its family.
        
        Returns:
            bool: True if this is the latest version
        """
        latest = self.get_latest_version_of_family()
        return latest.id == self.id
```

---

## 📡 Backend API Endpoints

### **Step 2: Add ViewSet Actions**

**File:** `backend/apps/documents/views.py`

**Add these actions to `DocumentViewSet`:**

```python
class DocumentViewSet(viewsets.ModelViewSet):
    # ... existing code ...
    
    @action(detail=False, methods=['get'])
    def families(self, request):
        """
        Get document families for Document Library.
        
        GET /api/v1/documents/families/
        
        Returns only families where latest version is EFFECTIVE or APPROVED_PENDING_EFFECTIVE.
        Each family includes all versions (including SUPERSEDED).
        
        Response:
        {
            "count": 45,
            "families": [
                {
                    "base_number": "POL-2025-0001",
                    "title": "Quality Policy",
                    "latest_version": {
                        "uuid": "...",
                        "document_number": "POL-2025-0001-v03.00",
                        "version_string": "3.0",
                        "status": "EFFECTIVE",
                        ...
                    },
                    "all_versions": [
                        {...},  # v3.0
                        {...},  # v2.0 (SUPERSEDED)
                        {...}   # v1.0 (SUPERSEDED)
                    ],
                    "version_count": 3
                },
                ...
            ]
        }
        """
        # Get active families
        families_dict = Document.get_document_families(
            status_filter=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE', 'SUPERSEDED']
        )
        
        # Filter to only active families
        active_families = []
        
        for base_number, family_data in families_dict.items():
            if family_data['is_active']:
                # Serialize all versions
                versions_serializer = DocumentDetailSerializer(
                    family_data['all_versions'],
                    many=True,
                    context={'request': request}
                )
                
                active_families.append({
                    'base_number': base_number,
                    'title': family_data['title'],
                    'latest_version': DocumentDetailSerializer(
                        family_data['latest_version'],
                        context={'request': request}
                    ).data,
                    'all_versions': versions_serializer.data,
                    'version_count': len(family_data['all_versions'])
                })
        
        return Response({
            'count': len(active_families),
            'families': active_families
        })
    
    @action(detail=False, methods=['get'])
    def obsolete_families(self, request):
        """
        Get document families where latest version is OBSOLETE.
        
        GET /api/v1/documents/obsolete-families/
        
        Returns families where latest version is OBSOLETE.
        Includes all SUPERSEDED versions in the family.
        
        Response:
        {
            "count": 12,
            "families": [
                {
                    "base_number": "SOP-2020-0050",
                    "title": "COVID Screening Procedure",
                    "latest_version": {
                        "uuid": "...",
                        "document_number": "SOP-2020-0050-v02.00",
                        "status": "OBSOLETE",
                        "obsolescence_date": "2025-05-01",
                        "obsolescence_reason": "Process discontinued",
                        ...
                    },
                    "all_versions": [
                        {...},  # v2.0 (OBSOLETE)
                        {...}   # v1.0 (SUPERSEDED)
                    ],
                    "version_count": 2
                },
                ...
            ]
        }
        """
        # Get obsolete families
        families_dict = Document.get_document_families(
            status_filter=['OBSOLETE', 'SUPERSEDED']
        )
        
        # Filter to only obsolete families
        obsolete_families = []
        
        for base_number, family_data in families_dict.items():
            if family_data['is_obsolete']:
                # Serialize all versions
                versions_serializer = DocumentDetailSerializer(
                    family_data['all_versions'],
                    many=True,
                    context={'request': request}
                )
                
                latest = family_data['latest_version']
                
                obsolete_families.append({
                    'base_number': base_number,
                    'title': family_data['title'],
                    'latest_version': DocumentDetailSerializer(
                        latest,
                        context={'request': request}
                    ).data,
                    'obsolescence_date': latest.obsolescence_date,
                    'obsolescence_reason': latest.obsolescence_reason,
                    'obsoleted_by': latest.obsoleted_by.username if latest.obsoleted_by else None,
                    'all_versions': versions_serializer.data,
                    'version_count': len(family_data['all_versions'])
                })
        
        return Response({
            'count': len(obsolete_families),
            'families': obsolete_families
        })
    
    @action(detail=True, methods=['get'])
    def family_versions(self, request, uuid=None):
        """
        Get all versions of this document's family.
        
        GET /api/v1/documents/{uuid}/family-versions/
        
        Returns all versions of the document family, ordered by version number.
        """
        document = self.get_object()
        
        versions = document.get_family_versions()
        serializer = DocumentDetailSerializer(
            versions,
            many=True,
            context={'request': request}
        )
        
        latest = versions.first() if versions.exists() else document
        
        return Response({
            'base_number': document.get_base_document_number(),
            'title': document.title,
            'latest_version': {
                'uuid': str(latest.uuid),
                'version': latest.version_string,
                'status': latest.status
            },
            'is_latest': document.is_latest_version(),
            'versions': serializer.data
        })
```

---

## 🎨 Frontend Implementation

### **Step 3: Create DocumentFamilyCard Component**

**File:** `frontend/src/components/documents/DocumentFamilyCard.tsx`

```typescript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Collapse,
  List,
  ListItem,
  Typography,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

interface DocumentFamily {
  base_number: string;
  title: string;
  latest_version: any;
  all_versions: any[];
  version_count: number;
}

interface Props {
  family: DocumentFamily;
  showObsoleteAlert?: boolean;
}

export const DocumentFamilyCard: React.FC<Props> = ({ 
  family, 
  showObsoleteAlert = false 
}) => {
  const [showVersions, setShowVersions] = useState(false);
  const navigate = useNavigate();
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'EFFECTIVE':
        return 'success';
      case 'APPROVED_PENDING_EFFECTIVE':
        return 'info';
      case 'SUPERSEDED':
        return 'warning';
      case 'OBSOLETE':
        return 'error';
      default:
        return 'default';
    }
  };
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'EFFECTIVE':
        return '🟢';
      case 'SUPERSEDED':
        return '🟡';
      case 'OBSOLETE':
        return '🔴';
      default:
        return '⚪';
    }
  };
  
  const latest = family.latest_version;
  const supersededVersions = family.all_versions.filter(
    v => v.status === 'SUPERSEDED'
  );
  
  return (
    <Card className="document-family-card">
      <CardContent>
        {/* Obsolete Alert */}
        {showObsoleteAlert && latest.status === 'OBSOLETE' && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">
              <strong>Obsolete Document Family</strong>
            </Typography>
            <Typography variant="body2">
              Reason: {latest.obsolescence_reason}
            </Typography>
            <Typography variant="body2">
              Obsoleted: {new Date(latest.obsolescence_date).toLocaleDateString()}
            </Typography>
            {latest.obsoleted_by && (
              <Typography variant="body2">
                By: {latest.obsoleted_by}
              </Typography>
            )}
          </Alert>
        )}
        
        {/* Document Title */}
        <Typography variant="h6">
          {family.title}
        </Typography>
        
        {/* Base Number */}
        <Typography variant="body2" color="textSecondary">
          {family.base_number}
        </Typography>
        
        {/* Latest Version Info */}
        <div className="latest-version-info" style={{ marginTop: '12px' }}>
          <Typography variant="body2">
            <strong>Current Version:</strong> {latest.version_string}
          </Typography>
          
          <Chip
            label={latest.status}
            color={getStatusColor(latest.status)}
            size="small"
            icon={<span>{getStatusIcon(latest.status)}</span>}
            sx={{ ml: 1 }}
          />
          
          <Typography variant="body2" color="textSecondary">
            Last updated: {new Date(latest.updated_at).toLocaleDateString()}
          </Typography>
        </div>
        
        {/* Version History Toggle */}
        {family.version_count > 1 && (
          <>
            <Button
              size="small"
              onClick={() => setShowVersions(!showVersions)}
              startIcon={showVersions ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              sx={{ mt: 2 }}
            >
              Version History ({supersededVersions.length} previous)
            </Button>
            
            <Collapse in={showVersions}>
              <List dense sx={{ mt: 1 }}>
                {family.all_versions.map((version, index) => (
                  <ListItem
                    key={version.uuid}
                    sx={{
                      borderLeft: index === 0 ? '3px solid #4caf50' : '3px solid #ff9800',
                      pl: 2,
                      mb: 1,
                      backgroundColor: index === 0 ? '#f1f8f4' : '#fff8e1'
                    }}
                  >
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2">
                          <strong>v{version.version_string}</strong>
                          {index === 0 && ' (Current)'}
                        </Typography>
                        
                        <Chip
                          label={version.status}
                          size="small"
                          color={getStatusColor(version.status)}
                        />
                      </div>
                      
                      <Typography variant="caption" color="textSecondary">
                        Effective: {version.effective_date ? 
                          new Date(version.effective_date).toLocaleDateString() : 
                          'N/A'}
                      </Typography>
                      
                      <div style={{ marginTop: '8px' }}>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => navigate(`/documents/${version.uuid}`)}
                        >
                          View v{version.version_string}
                        </Button>
                      </div>
                    </div>
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </>
        )}
      </CardContent>
      
      <CardActions>
        <Button
          variant="contained"
          onClick={() => navigate(`/documents/${latest.uuid}`)}
        >
          View Current Version
        </Button>
        
        <Button
          variant="outlined"
          onClick={() => navigate(`/documents/${latest.uuid}/download`)}
        >
          Download
        </Button>
        
        {family.version_count > 1 && (
          <Button
            variant="text"
            onClick={() => navigate(`/documents/family/${family.base_number}/history`)}
          >
            Full History
          </Button>
        )}
      </CardActions>
    </Card>
  );
};
```

---

### **Step 4: Update Document Library Page**

**File:** `frontend/src/pages/DocumentLibrary.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { DocumentFamilyCard } from '../components/documents/DocumentFamilyCard';
import api from '../services/api';

const DocumentLibrary: React.FC = () => {
  const [families, setFamilies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    fetchDocumentFamilies();
  }, []);
  
  const fetchDocumentFamilies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/documents/families/');
      setFamilies(response.data.families);
    } catch (err) {
      console.error('Failed to fetch document families:', err);
      setError('Failed to load document library');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return <div>Loading document library...</div>;
  }
  
  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }
  
  return (
    <div className="document-library">
      <h1>Document Library</h1>
      <p>Active documents - {families.length} document families</p>
      
      <div className="families-grid">
        {families.map(family => (
          <DocumentFamilyCard
            key={family.base_number}
            family={family}
          />
        ))}
      </div>
      
      {families.length === 0 && (
        <Alert severity="info">
          No active documents found. Create your first document to get started!
        </Alert>
      )}
    </div>
  );
};

export default DocumentLibrary;
```

---

### **Step 5: Create Obsolete Documents Page**

**File:** `frontend/src/pages/ObsoleteDocuments.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { DocumentFamilyCard } from '../components/documents/DocumentFamilyCard';
import api from '../services/api';
import { Alert, Typography } from '@mui/material';

const ObsoleteDocuments: React.FC = () => {
  const [obsoleteFamilies, setObsoleteFamilies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    fetchObsoleteFamilies();
  }, []);
  
  const fetchObsoleteFamilies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/documents/obsolete-families/');
      setObsoleteFamilies(response.data.families);
    } catch (err) {
      console.error('Failed to fetch obsolete families:', err);
      setError('Failed to load obsolete documents');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return <div>Loading obsolete documents...</div>;
  }
  
  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }
  
  return (
    <div className="obsolete-documents">
      <h1>Obsolete Document Families</h1>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          These document families have been retired and are no longer in use.
          All versions (including superseded) are shown for reference and audit purposes.
        </Typography>
      </Alert>
      
      <Typography variant="body1" sx={{ mb: 2 }}>
        {obsoleteFamilies.length} obsolete document families
      </Typography>
      
      <div className="families-grid">
        {obsoleteFamilies.map(family => (
          <DocumentFamilyCard
            key={family.base_number}
            family={family}
            showObsoleteAlert={true}
          />
        ))}
      </div>
      
      {obsoleteFamilies.length === 0 && (
        <Alert severity="success">
          No obsolete documents. All document families are active!
        </Alert>
      )}
    </div>
  );
};

export default ObsoleteDocuments;
```

---

### **Step 6: Add Route**

**File:** `frontend/src/App.tsx`

```typescript
import ObsoleteDocuments from './pages/ObsoleteDocuments';

// Add to routes
<Route path="/documents/obsolete" element={<ObsoleteDocuments />} />
```

---

### **Step 7: Add Navigation Link**

**File:** `frontend/src/components/Navigation.tsx`

```typescript
<NavLink to="/documents/obsolete">
  <ArchiveIcon />
  <span>Obsolete Documents</span>
</NavLink>
```

---

## 🧪 Testing

### **Test 1: Active Family Display**

**Setup:**
```sql
-- Create family
POL-2025-0001-v01.00 (SUPERSEDED)
POL-2025-0001-v02.00 (SUPERSEDED)
POL-2025-0001-v03.00 (EFFECTIVE) ← Latest
```

**Expected:**
- Family appears in Document Library
- Shows v3.0 as current
- Expand shows v2.0 and v1.0
- All versions marked SUPERSEDED except v3.0

---

### **Test 2: Obsolete Family Display**

**Setup:**
```sql
-- Create family
SOP-2020-0050-v01.00 (SUPERSEDED)
SOP-2020-0050-v02.00 (OBSOLETE) ← Latest
```

**Expected:**
- Family does NOT appear in Document Library
- Family appears in Obsolete Documents page
- Shows v2.0 as OBSOLETE
- Expand shows v1.0 as SUPERSEDED
- Shows obsolescence reason

---

### **Test 3: Version History Navigation**

1. Open any document
2. See version history
3. Click on SUPERSEDED version
4. Should show warning: "You are viewing an outdated version"
5. Link to view current version

---

## 📋 Implementation Checklist

### **Backend:**
- [ ] Add `get_base_document_number()` to Document model
- [ ] Add `get_document_families()` class method
- [ ] Add `get_family_versions()` method
- [ ] Add `get_latest_version_of_family()` method
- [ ] Add `is_latest_version()` method
- [ ] Add `families` API endpoint
- [ ] Add `obsolete_families` API endpoint
- [ ] Add `family_versions` API endpoint
- [ ] Test API endpoints

### **Frontend:**
- [ ] Create `DocumentFamilyCard.tsx` component
- [ ] Update `DocumentLibrary.tsx` to use families
- [ ] Create `ObsoleteDocuments.tsx` page
- [ ] Add route for obsolete documents
- [ ] Add navigation link
- [ ] Update API service methods
- [ ] Test family grouping
- [ ] Test version history expansion
- [ ] Test navigation between versions

---

## 🚀 Deployment

### **After Implementation:**

1. **Commit changes**
2. **Test on local development**
3. **Deploy to staging**
4. **Test family grouping on staging**
5. **Deploy to production**

---

## 📊 Summary

**What This Achieves:**

✅ **Logical Grouping** - Documents grouped by family  
✅ **Location Follows Latest** - SUPERSEDED versions follow latest  
✅ **No Broken Dependencies** - All versions considered  
✅ **Clear Visualization** - Easy to see version relationships  
✅ **Compliance** - Complete audit trail  
✅ **User-Friendly** - Intuitive navigation  

---

**Continued in IMPLEMENTATION_GUIDE_OBSOLESCENCE_VALIDATION.md**
