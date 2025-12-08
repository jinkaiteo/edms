# Dependency Display Debug Guide

## Quick Frontend Debugging Steps

### 1. Check Browser Console
Open DevTools (F12) → Console tab and look for:
- JavaScript errors
- `document.dependencies` value
- API response data

### 2. Check Network Tab
Open DevTools (F12) → Network tab:
1. Navigate to SOP-2025-0001-v01.00 
2. Look for API call to: `documents/2c8214b0-0249-46d1-a20f-29157e83cc60/`
3. Click on the response and check if it contains:
   ```json
   {
     "dependencies": [
       {
         "id": 27,
         "depends_on_display": "POL-2025-0001-v01.00",
         "dependency_type": "required"
       }
     ]
   }
   ```

### 3. Add Temporary Debug Logging
In DocumentViewer.tsx, temporarily add this after the document is loaded:

```tsx
console.log('🔍 Document object:', document);
console.log('🔗 Dependencies:', document.dependencies);
console.log('📤 Dependents:', document.dependents);
```

### 4. Check Document Status
The document is currently `SCHEDULED_FOR_OBSOLESCENCE` - this shouldn't affect dependencies display, but the UI might be filtering based on status.

### 5. Possible Issues

**Frontend Issues:**
- Document not fully loaded when dependencies section renders
- Dependencies array being filtered or transformed somewhere
- Component state issues
- API response not matching expected structure

**Backend Issues (Less Likely):**
- Different document being returned
- Serializer not including dependencies in certain conditions
- Authentication/permission issues

### 6. Quick Test
Try this in browser console when viewing the SOP document:
```javascript
// Check if document data has dependencies
console.log('Current document:', window.documentData || 'Not available');
```

## Expected Behavior
You should see in the 📥 Dependencies section:
- Blue box containing "POL-2025-0001-v01.00"
- Type: "required" 
- Date: "Added Dec 8, 2025"

## If Still Not Working
The backend API is definitely returning the correct data, so the issue is in the frontend:
1. Document state management
2. Component rendering logic
3. Data transformation/filtering
4. Timing issues (dependencies loading after component renders)