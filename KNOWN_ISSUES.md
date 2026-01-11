# Known Issues

## Document Creation API - ForeignKey Serialization Issue

**Status:** UNRESOLVED  
**Severity:** Medium (workaround available)  
**Date Identified:** 2026-01-11  

### Issue Description
Document creation via API returns 500 error with:
```
RelatedObjectDoesNotExist: Document has no document_type
Location: backend/apps/documents/models.py:404 in generate_document_number()
```

### Root Cause
Django REST Framework's ModelSerializer doesn't properly convert FormData string IDs to ForeignKey objects before calling `Model.save()`. The `document_type` and `document_source` fields arrive as string IDs but aren't converted to model instances before the document number generation logic runs.

### What Was Tried
- PrimaryKeyRelatedField in serializer
- Manual FK conversion in perform_create
- Manual FK conversion in create() method
- Making fields optional with auto-assignment
- Multiple variations of the above

### Workaround
Documents can be created via Django admin panel or shell:
```python
from apps.documents.models import Document, DocumentType, DocumentSource
from apps.users.models import User

Document.objects.create(
    title="Test",
    description="Test",
    author=User.objects.first(),
    document_type=DocumentType.objects.get(id=13),
    document_source=DocumentSource.objects.get(id=8),
    priority='normal',
    requires_training=False,
    is_controlled=True
)
```

### Testing Impact
- ✅ Workflow testing can proceed with existing documents
- ✅ Document transitions (review, approval) should work
- ❌ Cannot test document creation flow via UI
- ❌ E2E tests requiring new document creation will fail

### Next Steps
1. Test with JSON request body instead of FormData
2. Consider separate file upload endpoint
3. Override Model.save() to handle missing FKs gracefully
4. Investigate DRF FormData parser behavior

### Related
- Original issue: Frontend "User ID not found" - **FIXED** ✅
- Authentication API now returns complete user data including `id` field
