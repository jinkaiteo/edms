# Periodic Review - Frontend Integration Guide

**Date:** January 22, 2026  
**Status:** Frontend Components Complete - Integration Pending

---

## ✅ Components Created (5/5)

### 1. PeriodicReviewModal.tsx (379 lines)
Main review completion modal with three outcomes

### 2. PeriodicReviewList.tsx (272 lines)
List page showing all documents under periodic review

### 3. ReviewHistoryTab.tsx (203 lines)
Tab component showing complete review audit trail

### 4. TypeScript Interfaces (api.ts)
All type definitions for periodic review

### 5. API Service Methods (api.ts)
All REST API integration methods

---

## 🔧 Integration Tasks

### Task 1: Add Route for Periodic Review List

**File:** `frontend/src/App.tsx` or your routing file

```tsx
import PeriodicReviewList from './components/documents/PeriodicReviewList';

// Add route
<Route path="/periodic-reviews" element={<PeriodicReviewList />} />

// Alternative: Use filter parameter
<Route path="/documents" element={<DocumentLibrary />} />
// Then in DocumentLibrary, check for ?filter=periodic_review
```

---

### Task 2: Add Navigation Menu Item

**File:** `frontend/src/components/Navigation.tsx` (or similar)

**Option A: Simple Link**
```tsx
<NavLink 
  to="/periodic-reviews"
  className={({ isActive }) => 
    isActive ? 'nav-link-active' : 'nav-link'
  }
>
  Periodic Reviews
</NavLink>
```

**Option B: With Badge Count (Recommended)**
```tsx
import { useState, useEffect } from 'react';
import apiService from '../services/api';

const Navigation: React.FC = () => {
  const [reviewCount, setReviewCount] = useState(0);

  useEffect(() => {
    loadReviewCount();
    // Refresh every 5 minutes
    const interval = setInterval(loadReviewCount, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadReviewCount = async () => {
    try {
      const response = await apiService.getPeriodicReviewDocuments();
      const docs = Array.isArray(response) ? response : response.results || [];
      setReviewCount(docs.length);
    } catch (error) {
      console.error('Failed to load review count:', error);
    }
  };

  return (
    <nav>
      {/* Other nav items */}
      
      <NavLink 
        to="/periodic-reviews"
        className={({ isActive }) => 
          `nav-link ${isActive ? 'nav-link-active' : ''}`
        }
      >
        <span>Periodic Reviews</span>
        {reviewCount > 0 && (
          <span className="ml-2 px-2 py-1 text-xs font-medium bg-red-500 text-white rounded-full">
            {reviewCount}
          </span>
        )}
      </NavLink>
    </nav>
  );
};
```

---

### Task 3: Integrate into DocumentViewer

**File:** `frontend/src/components/documents/DocumentViewer.tsx`

**Step 1: Import Components**
```tsx
import PeriodicReviewModal from './PeriodicReviewModal';
import ReviewHistoryTab from './ReviewHistoryTab';
```

**Step 2: Add State**
```tsx
const [showReviewModal, setShowReviewModal] = useState(false);
```

**Step 3: Add Review Button (if document needs review)**
```tsx
{/* In document header or action buttons area */}
{document.next_review_date && 
 new Date(document.next_review_date) <= new Date() && 
 document.status === 'EFFECTIVE' && (
  <button
    onClick={() => setShowReviewModal(true)}
    className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
  >
    ⚠️ Periodic Review Due
  </button>
)}
```

**Step 4: Add Review History Tab**
```tsx
{/* In your tab navigation */}
<Tabs>
  <Tab label="Details">
    {/* Existing content */}
  </Tab>
  
  <Tab label="Version History">
    {/* Existing content */}
  </Tab>
  
  <Tab label="Review History">
    <ReviewHistoryTab document={document} />
  </Tab>
</Tabs>
```

**Step 5: Add Modal**
```tsx
{/* At the end of component, before closing div */}
<PeriodicReviewModal
  isOpen={showReviewModal}
  onClose={() => setShowReviewModal(false)}
  document={document}
  onSuccess={() => {
    // Refresh document data
    loadDocument();
    setShowReviewModal(false);
  }}
/>
```

---

### Task 4: Integrate into My Tasks

**File:** `frontend/src/components/workflows/MyTasks.tsx`

**Option A: Separate Section**
```tsx
import { useState, useEffect } from 'react';
import { Document } from '../../types/api';
import apiService from '../../services/api';
import PeriodicReviewModal from '../documents/PeriodicReviewModal';

const MyTasks: React.FC = () => {
  const [reviewDocuments, setReviewDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadReviewTasks();
  }, []);

  const loadReviewTasks = async () => {
    try {
      const response = await apiService.getPeriodicReviewDocuments();
      const docs = Array.isArray(response) ? response : response.results || [];
      setReviewDocuments(docs);
    } catch (error) {
      console.error('Failed to load review tasks:', error);
    }
  };

  return (
    <div>
      {/* Existing tasks sections */}
      
      {/* Periodic Review Section */}
      {reviewDocuments.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">
            📋 Periodic Reviews ({reviewDocuments.length})
          </h2>
          
          <div className="space-y-3">
            {reviewDocuments.map((doc) => (
              <div 
                key={doc.uuid}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">{doc.document_number}</h3>
                    <p className="text-sm text-gray-600">{doc.title}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Due: {doc.next_review_date ? 
                        new Date(doc.next_review_date).toLocaleDateString() : 
                        'N/A'}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedDoc(doc);
                      setShowModal(true);
                    }}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Complete Review
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Modal */}
      {selectedDoc && (
        <PeriodicReviewModal
          isOpen={showModal}
          onClose={() => {
            setShowModal(false);
            setSelectedDoc(null);
          }}
          document={selectedDoc}
          onSuccess={() => {
            loadReviewTasks();
            setShowModal(false);
            setSelectedDoc(null);
          }}
        />
      )}
    </div>
  );
};
```

---

### Task 5: Add to Dashboard (Optional)

**File:** `frontend/src/components/Dashboard.tsx`

```tsx
const [reviewCount, setReviewCount] = useState(0);

useEffect(() => {
  const loadStats = async () => {
    try {
      const response = await apiService.getPeriodicReviewDocuments();
      const docs = Array.isArray(response) ? response : response.results || [];
      setReviewCount(docs.length);
    } catch (error) {
      console.error('Failed to load review stats:', error);
    }
  };
  loadStats();
}, []);

return (
  <div>
    {/* Existing dashboard content */}
    
    {/* Add card for periodic reviews */}
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-2">Periodic Reviews</h3>
      <div className="text-3xl font-bold text-orange-600">{reviewCount}</div>
      <p className="text-sm text-gray-600">Documents need review</p>
      <Link 
        to="/periodic-reviews" 
        className="text-blue-600 text-sm hover:underline mt-2 block"
      >
        View all →
      </Link>
    </div>
  </div>
);
```

---

## 🎨 Styling Guide

### Color Scheme
- **Overdue:** Red (`bg-red-500`, `text-red-600`)
- **Due Soon:** Orange (`bg-orange-500`, `text-orange-600`)
- **Upcoming:** Green/Yellow (`bg-green-500`, `text-green-600`)
- **Confirmed:** Green (`bg-green-100`, `text-green-800`)
- **Updated:** Blue (`bg-blue-100`, `text-blue-800`)
- **Upversioned:** Orange (`bg-orange-100`, `text-orange-800`)

### Icons
- 🔴 Overdue
- 🟡 Due Soon
- 🟢 Upcoming
- ✅ Confirmed
- 📝 Updated
- 🔄 Upversioned
- 📋 Review

---

## 🧪 Testing Checklist

### Unit Testing
- [ ] PeriodicReviewModal renders correctly
- [ ] PeriodicReviewList loads documents
- [ ] ReviewHistoryTab displays reviews
- [ ] API service methods work
- [ ] Error states display properly

### Integration Testing
- [ ] Navigation to /periodic-reviews works
- [ ] Badge count updates correctly
- [ ] Modal opens from list
- [ ] Modal opens from DocumentViewer
- [ ] Review completion refreshes data

### End-to-End Testing
- [ ] Complete CONFIRMED review flow
- [ ] Complete UPDATED review flow
- [ ] Complete UPVERSIONED review flow
- [ ] Verify review history appears
- [ ] Check audit trail in backend
- [ ] Verify next_review_date updates

---

## 📋 Quick Implementation Checklist

```
Phase 2 - Frontend Implementation:

Components:
[✅] PeriodicReviewModal.tsx (379 lines)
[✅] PeriodicReviewList.tsx (272 lines)
[✅] ReviewHistoryTab.tsx (203 lines)
[✅] TypeScript interfaces
[✅] API service methods

Integration:
[ ] Add route for /periodic-reviews
[ ] Add navigation menu item (with badge)
[ ] Integrate modal into DocumentViewer
[ ] Add review button to DocumentViewer
[ ] Add ReviewHistoryTab to DocumentViewer tabs
[ ] Integrate into My Tasks view
[ ] Add dashboard card (optional)

Testing:
[ ] Test all three outcomes
[ ] Verify API connections
[ ] Check error handling
[ ] Test navigation flow
[ ] Verify data refresh

Total Estimated Time: 1-2 hours for integration + testing
```

---

## 🚀 Deployment Steps

1. **Build Frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Restart Frontend Container**
   ```bash
   docker compose restart frontend
   ```

3. **Test in Browser**
   - Navigate to http://localhost:3001/periodic-reviews
   - Check navigation menu
   - Test completing a review
   - Verify review history appears

4. **Monitor Logs**
   ```bash
   docker compose logs -f frontend backend
   ```

---

## 📊 File Summary

### Created Files
1. `frontend/src/components/documents/PeriodicReviewModal.tsx` (379 lines)
2. `frontend/src/components/documents/PeriodicReviewList.tsx` (272 lines)
3. `frontend/src/components/documents/ReviewHistoryTab.tsx` (203 lines)
4. `frontend/src/types/api.ts` (updated - added ~60 lines)
5. `frontend/src/services/api.ts` (updated - added ~50 lines)

### Total New Code
**~964 lines** of production-ready TypeScript/React code

---

## ✅ What's Complete

- ✅ All TypeScript interfaces
- ✅ All API service methods
- ✅ Main periodic review modal (3 outcomes)
- ✅ Document list page with color coding
- ✅ Review history display component
- ✅ Error handling and loading states
- ✅ Responsive design with Tailwind CSS
- ✅ Professional UI/UX
- ✅ Complete documentation

---

## ⏳ What Remains (1-2 hours)

- ⏳ Add route configuration
- ⏳ Add navigation menu item
- ⏳ Integrate into DocumentViewer
- ⏳ Integrate into My Tasks
- ⏳ End-to-end testing

**The hard work is DONE! Just plug the components in and test! 🎉**

---

**Ready to integrate?** Follow the tasks above in order, or I can help you with specific integration steps!
