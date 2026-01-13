# Document Dependency Up-versioning Fix

## 🔴 Problem Identified

When creating a new version of a document (up-versioning), **dependencies are lost**. The current implementation:

1. Creates new document version
2. Copies basic metadata (title, description, etc.)
3. Sets `supersedes` field to link to parent
4. **DOES NOT copy dependencies** ❌

### Example Scenario:
```
Document A v1.0 → depends on → Document B v1.0, Document C v1.0

User creates Document A v2.0 (new version)

Result:
Document A v2.0 → depends on → NOTHING ❌ (dependencies lost!)
```

---

## 💡 Solution Options

### Option 1: Copy Dependencies to New Version (Version-Specific)
**Approach**: When creating v2.0, copy all dependencies from v1.0 pointing to the same specific versions.

**Pros**:
- Simple implementation
- Maintains exact version references
- Clear dependency history

**Cons**:
- If dependent document is up-versioned, link becomes stale
- Requires manual updates when dependencies change
- Can create confusion about which version to use

### Option 2: Smart Dependency Resolution (Latest Effective Version)
**Approach**: Copy dependencies but resolve to **latest effective version** of each dependent document.

**Pros**:
- Always uses current versions
- Reduces maintenance burden
- More intuitive for users

**Cons**:
- Slightly more complex
- Need to handle cases where latest version doesn't exist

### Option 3: Document Family Dependencies (Recommended) ⭐
**Approach**: Dependencies point to **document families** (base document numbers), not specific versions.

**Pros**:
- Survives up-versioning naturally
- Always uses latest effective version automatically
- Most maintainable long-term
- Aligns with real-world document management

**Cons**:
- Requires data model changes
- More complex initial implementation
- Need migration for existing dependencies

---

## 🎯 Recommended Solution: Hybrid Approach

Implement a **pragmatic hybrid** that works with current schema:

### Phase 1: Immediate Fix (Copy Dependencies with Smart Resolution)
1. When creating new version, copy all dependencies from parent
2. For each dependency:
   - Check if the dependent document has a newer effective version
   - If yes, point to the newer version
   - If no, point to same version as parent

### Phase 2: Long-term Enhancement (Document Family System)
1. Add `document_family` concept to model
2. Migrate dependencies to use families
3. Auto-resolve to latest effective version at runtime

---

## 🔧 Implementation: Phase 1 (Immediate Fix)

### Modified Code for `create_version` Action

```python
@action(detail=True, methods=['post'])
def create_version(self, request, uuid=None):
    """Create a new version of the document with dependency copying."""
    document = self.get_object()
    serializer = DocumentVersionCreateSerializer(
        data=request.data,
        context={'document': document, 'request': request}
    )
    
    if serializer.is_valid():
        major_increment = serializer.validated_data['major_increment']
        version_comment = serializer.validated_data.get('version_comment', '')
        change_summary = serializer.validated_data['change_summary']
        reason_for_change = serializer.validated_data['reason_for_change']
        
        # Calculate new version numbers
        if major_increment:
            new_major = document.version_major + 1
            new_minor = 0
        else:
            new_major = document.version_major
            new_minor = document.version_minor + 1
        
        # Validate version limits
        if new_major > 99:
            return Response(
                {'error': 'Major version cannot exceed 99.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if new_minor > 99:
            return Response(
                {'error': 'Minor version cannot exceed 99.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new document version
        new_document = Document.objects.create(
            title=document.title,
            description=document.description,
            keywords=document.keywords,
            version_major=new_major,
            version_minor=new_minor,
            document_type=document.document_type,
            document_source=document.document_source,
            author=request.user,
            reviewer=document.reviewer,
            approver=document.approver,
            status='DRAFT',
            priority=document.priority,
            supersedes=document,
            reason_for_change=reason_for_change,
            change_summary=change_summary,
            requires_training=document.requires_training,
            is_controlled=document.is_controlled,
        )
        
        # ✅ NEW: Copy dependencies with smart version resolution
        self._copy_dependencies_smart(document, new_document, request.user)
        
        # Log version creation
        log_document_access(
            document=new_document,
            user=request.user,
            access_type='EDIT',
            request=request,
            success=True,
            metadata={
                'action': 'version_created',
                'previous_version': document.version_string,
                'new_version': new_document.version_string,
                'major_increment': major_increment,
                'dependencies_copied': True
            }
        )
        
        serializer = DocumentDetailSerializer(new_document, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _copy_dependencies_smart(self, source_document, target_document, user):
    """
    Copy dependencies from source to target document with smart version resolution.
    
    For each dependency:
    1. Get the base document number of the dependent document
    2. Find the latest EFFECTIVE version of that document family
    3. Create dependency to the latest effective version (or original if none newer)
    
    Args:
        source_document: Original document (e.g., v1.0)
        target_document: New version (e.g., v2.0)
        user: User creating the new version
    """
    from .models import DocumentDependency
    import re
    
    # Get all active dependencies from source document
    source_dependencies = DocumentDependency.objects.filter(
        document=source_document,
        is_active=True
    ).select_related('depends_on')
    
    copied_count = 0
    updated_count = 0
    
    for dep in source_dependencies:
        original_dependent = dep.depends_on
        
        # Get base document number (remove version suffix)
        base_doc_number = self._get_base_document_number(original_dependent.document_number)
        
        # Find latest effective version of this document family
        latest_effective = self._find_latest_effective_version(base_doc_number)
        
        # Determine which document to link to
        if latest_effective and latest_effective.id != original_dependent.id:
            # Use latest effective version
            target_dependent = latest_effective
            updated_count += 1
            print(f"📈 Upgrading dependency: {original_dependent.document_number} → {target_dependent.document_number}")
        else:
            # Use same version as parent had
            target_dependent = original_dependent
            copied_count += 1
            print(f"📋 Copying dependency: {target_dependent.document_number}")
        
        # Create new dependency (with validation for circular dependencies)
        try:
            new_dependency = DocumentDependency(
                document=target_document,
                depends_on=target_dependent,
                dependency_type=dep.dependency_type,
                description=dep.description,
                is_critical=dep.is_critical,
                created_by=user,
                is_active=True,
                metadata={
                    'copied_from_version': source_document.version_string,
                    'original_dependency_id': str(dep.uuid),
                    'auto_upgraded': (target_dependent.id != original_dependent.id)
                }
            )
            
            # Validate (checks for circular dependencies)
            new_dependency.clean()
            new_dependency.save()
            
        except ValidationError as e:
            print(f"⚠️ Skipped dependency due to validation error: {e}")
            continue
    
    print(f"✅ Dependency copy complete: {copied_count} copied, {updated_count} upgraded to latest versions")
    return copied_count + updated_count


def _get_base_document_number(self, document_number):
    """
    Extract base document number without version suffix.
    
    Examples:
        POL-2025-0001-v02.00 → POL-2025-0001
        SOP-2025-0015-v01.05 → SOP-2025-0015
    """
    import re
    if '-v' in document_number:
        return document_number.split('-v')[0]
    return document_number


def _find_latest_effective_version(self, base_doc_number):
    """
    Find the latest EFFECTIVE version of a document family.
    
    Args:
        base_doc_number: Base document number (e.g., "POL-2025-0001")
    
    Returns:
        Document object of latest effective version, or None if not found
    """
    # Find all effective documents matching this base number
    effective_docs = Document.objects.filter(
        document_number__startswith=base_doc_number,
        status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
    )
    
    if not effective_docs.exists():
        return None
    
    # Get the one with highest version number
    latest = max(
        effective_docs,
        key=lambda d: (d.version_major, d.version_minor)
    )
    
    return latest
```

---

## 📝 Additional Helper Method for DocumentDependency Model

Add to `backend/apps/documents/models.py` in the `DocumentDependency` class:

```python
@classmethod
def copy_dependencies_to_new_version(cls, source_document, target_document, created_by):
    """
    Copy all dependencies from source to target document with smart version resolution.
    
    This is called automatically when creating a new version.
    Can also be called manually to restore dependencies.
    
    Returns:
        dict with 'copied', 'upgraded', and 'skipped' counts
    """
    import re
    
    source_deps = cls.objects.filter(
        document=source_document,
        is_active=True
    ).select_related('depends_on')
    
    copied = 0
    upgraded = 0
    skipped = 0
    
    for dep in source_deps:
        original_dependent = dep.depends_on
        
        # Get base document number
        base_number = cls._get_base_document_number_static(original_dependent.document_number)
        
        # Find latest effective version
        latest_effective = cls._find_latest_effective_version_static(base_number)
        
        # Determine target
        if latest_effective and latest_effective.id != original_dependent.id:
            target_dependent = latest_effective
            upgraded += 1
        else:
            target_dependent = original_dependent
            copied += 1
        
        # Create dependency
        try:
            new_dep = cls(
                document=target_document,
                depends_on=target_dependent,
                dependency_type=dep.dependency_type,
                description=dep.description,
                is_critical=dep.is_critical,
                created_by=created_by,
                is_active=True,
                metadata={
                    'copied_from_version': source_document.version_string,
                    'original_dependency_id': str(dep.uuid),
                    'auto_upgraded': (target_dependent.id != original_dependent.id)
                }
            )
            new_dep.clean()
            new_dep.save()
        except ValidationError:
            skipped += 1
            continue
    
    return {
        'copied': copied,
        'upgraded': upgraded,
        'skipped': skipped,
        'total': copied + upgraded
    }

@classmethod
def _find_latest_effective_version_static(cls, base_doc_number):
    """Find latest effective version of a document family."""
    from apps.documents.models import Document
    
    effective_docs = Document.objects.filter(
        document_number__startswith=base_doc_number,
        status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']
    )
    
    if not effective_docs.exists():
        return None
    
    return max(effective_docs, key=lambda d: (d.version_major, d.version_minor))
```

---

## 🧪 Testing the Fix

### Test Case 1: Basic Dependency Copy

```python
# Setup
doc_a_v1 = create_document("DOC-A", version=(1, 0), status="EFFECTIVE")
doc_b_v1 = create_document("DOC-B", version=(1, 0), status="EFFECTIVE")
create_dependency(doc_a_v1, depends_on=doc_b_v1)

# Create new version
doc_a_v2 = create_new_version(doc_a_v1)

# Assert
assert doc_a_v2.dependencies.count() == 1
assert doc_a_v2.dependencies.first().depends_on == doc_b_v1
```

### Test Case 2: Smart Version Upgrade

```python
# Setup
doc_a_v1 = create_document("DOC-A", version=(1, 0), status="EFFECTIVE")
doc_b_v1 = create_document("DOC-B", version=(1, 0), status="EFFECTIVE")
doc_b_v2 = create_document("DOC-B", version=(2, 0), status="EFFECTIVE")  # Newer version!
create_dependency(doc_a_v1, depends_on=doc_b_v1)

# Create new version
doc_a_v2 = create_new_version(doc_a_v1)

# Assert - should upgrade to latest version
assert doc_a_v2.dependencies.count() == 1
assert doc_a_v2.dependencies.first().depends_on == doc_b_v2  # ✅ Upgraded!
```

### Test Case 3: Multiple Dependencies

```python
# Setup
doc_a_v1 = create_document("DOC-A", version=(1, 0))
doc_b_v1 = create_document("DOC-B", version=(1, 0), status="EFFECTIVE")
doc_c_v1 = create_document("DOC-C", version=(1, 0), status="EFFECTIVE")
doc_d_v2 = create_document("DOC-D", version=(2, 0), status="EFFECTIVE")  # Latest version
create_dependency(doc_a_v1, depends_on=doc_b_v1)
create_dependency(doc_a_v1, depends_on=doc_c_v1)
create_dependency(doc_a_v1, depends_on=doc_d_v2)

# Create new version
doc_a_v2 = create_new_version(doc_a_v1)

# Assert
assert doc_a_v2.dependencies.count() == 3
```

---

## 📊 Summary

### What Gets Fixed:
✅ Dependencies automatically copied when creating new version  
✅ Smart resolution to latest effective versions  
✅ Validation prevents circular dependencies  
✅ Audit trail in metadata  
✅ Works with existing data model  

### User Experience:
- **Before**: User creates v2.0, must manually re-add all dependencies ❌
- **After**: User creates v2.0, dependencies automatically copied ✅
- **Bonus**: If dependent documents have newer versions, auto-upgrades to them ⭐

### Benefits:
1. **No data loss**: Dependencies preserved across versions
2. **Smart updates**: Automatically uses latest effective versions
3. **Backwards compatible**: Works with current schema
4. **Audit trail**: Tracks what was copied/upgraded
5. **Validation**: Still prevents circular dependencies

---

## 🚀 Next Steps

1. **Implement the fix** in `views.py` and `models.py`
2. **Add helper methods** for dependency management
3. **Create migration** (if needed for new metadata fields)
4. **Test thoroughly** with existing documents
5. **Document the feature** in user guide

---

## 🔮 Future Enhancement: Document Family System

For long-term maintainability, consider implementing a document family system:

```python
class DocumentFamily(models.Model):
    """Represents a family of document versions."""
    base_number = models.CharField(unique=True)  # e.g., "POL-2025-0001"
    title = models.CharField()
    latest_effective_version = models.ForeignKey(Document)

class DocumentDependency(models.Model):
    """Dependencies between document families."""
    document_family = models.ForeignKey(DocumentFamily)
    depends_on_family = models.ForeignKey(DocumentFamily)
    
    def resolve_to_version(self):
        """Resolve to actual document versions at runtime."""
        return self.depends_on_family.latest_effective_version
```

This would make dependencies version-agnostic and always point to the latest effective version automatically.

---

**Ready to implement? Let me know if you want me to create the actual code changes!** 🚀
