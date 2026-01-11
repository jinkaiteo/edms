# Fix: document_type Object in List Response

## Root Cause Found!

Django REST Framework is **automatically including** `document_type` and `document_source` 
as nested objects in the list response, even though they're NOT in `Meta.fields`.

This happens because:
1. The model has ForeignKey fields: `document_type` and `document_source`
2. DRF automatically serializes FK fields with their related serializer
3. Even though Meta.fields doesn't include them explicitly

## The API Response Shows:

```json
{
  "document_type": {
    "id": 13,
    "name": "Policy",
    "code": "POL",
    ... (full object)
  }
}
```

But DocumentListSerializer.Meta.fields (line 257-270) only lists:
- `document_type_display` (string)
- NOT `document_type` (object)

## Solution

Add document_type and document_source to `read_only_fields` 
OR explicitly set them to use PrimaryKeyRelatedField to return just IDs
OR set `depth = 0` to prevent automatic nesting

**Recommended:** Use StringRelatedField or remove from output entirely.

