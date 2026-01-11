# Dependency Fix Plan

## Root Cause
The backend serializer is inconsistent:
- `DocumentListSerializer` - Should only return `document_type_display` (string)
- `DocumentDetailSerializer` - Returns full `document_type` object (nested serializer)

## Issue
Frontend components expect `document_type` to be a STRING, but:
- When listing documents (for dependencies), it gets mixed responses
- DocumentSelector tries to render `document_type` directly
- Results in "Objects are not valid as React child" errors

## Solution Options

### Option A: Fix Backend (Remove object, keep string only) ✅ RECOMMENDED
**Change:** Ensure DocumentListSerializer never includes full document_type object
**Impact:** Frontend works as designed
**Files:** backend/apps/documents/serializers.py

### Option B: Fix Frontend (Handle both string and object)
**Change:** Every place that renders document_type checks if it's string or object
**Impact:** More frontend changes, harder to maintain
**Files:** Multiple frontend components

## Recommendation: Option A

The frontend was designed to work with `document_type` as a string.
The backend should provide `document_type_display` for display purposes.
Full object details should only be in DocumentDetailSerializer.

