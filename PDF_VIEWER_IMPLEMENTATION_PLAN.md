# PDF Viewer Implementation Plan

**Goal:** Add in-app PDF viewer for approved documents  
**Complexity:** Medium  
**Estimated Time:** 2-4 hours  
**Date:** 2026-01-30  

---

## 📊 Current State Analysis

### What We Have:
- ✅ Backend generates PDFs for approved documents
- ✅ API endpoint: `/documents/{uuid}/download_official_pdf/`
- ✅ Download button in UI (opens browser download)
- ✅ Access control (only approved/effective documents)
- ✅ DocumentViewer component showing document metadata

### What We Don't Have:
- ❌ In-app PDF rendering
- ❌ PDF viewer library installed
- ❌ View/Download toggle UI

---

## 🎯 Implementation Options

### Option 1: react-pdf (Recommended) ⭐

**Library:** `react-pdf` (Mozilla's PDF.js wrapper)

**Pros:**
- ✅ Most popular React PDF library (7K+ stars)
- ✅ Full PDF rendering capabilities
- ✅ Zoom, page navigation, search
- ✅ Mobile-friendly
- ✅ Works with streaming (large files)
- ✅ TypeScript support

**Cons:**
- ⚠️ Adds ~600KB to bundle
- ⚠️ Requires worker setup

**Installation:**
```bash
npm install react-pdf pdfjs-dist
```

**Difficulty:** Medium  
**Time:** 2-3 hours

---

### Option 2: Browser Native PDF Viewer

**Method:** Use `<iframe>` or `<object>` with PDF blob URL

**Pros:**
- ✅ No extra dependencies
- ✅ Zero bundle size increase
- ✅ Browser handles rendering
- ✅ Quick to implement (30 minutes)

**Cons:**
- ❌ No control over UI
- ❌ Different behavior across browsers
- ❌ Limited on mobile
- ❌ No custom controls

**Difficulty:** Easy  
**Time:** 30 minutes - 1 hour

---

### Option 3: PDF.js Direct Integration

**Method:** Use PDF.js library directly (no React wrapper)

**Pros:**
- ✅ Full control over rendering
- ✅ Most powerful option
- ✅ Custom UI possible

**Cons:**
- ❌ More complex setup
- ❌ More code to write
- ❌ Manual canvas rendering

**Difficulty:** Hard  
**Time:** 4-6 hours

---

## 💡 Recommended Approach: Option 1 (react-pdf)

### Implementation Plan

#### Phase 1: Setup (30 minutes)

1. **Install Dependencies**
   ```bash
   npm install react-pdf pdfjs-dist
   ```

2. **Configure Worker**
   ```typescript
   // In App.tsx or index.tsx
   import { pdfjs } from 'react-pdf';
   pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;
   ```

3. **Add TypeScript Types**
   ```bash
   npm install --save-dev @types/react-pdf
   ```

---

#### Phase 2: Create PDFViewer Component (1 hour)

**File:** `frontend/src/components/documents/PDFViewer.tsx`

```typescript
import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

interface PDFViewerProps {
  pdfUrl: string;
  documentTitle?: string;
  onClose: () => void;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, documentTitle, onClose }) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-75 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <h3 className="text-lg font-medium">{documentTitle || 'PDF Viewer'}</h3>
        
        {/* Controls */}
        <div className="flex items-center space-x-4">
          {/* Zoom */}
          <div className="flex items-center space-x-2">
            <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))}>-</button>
            <span>{Math.round(scale * 100)}%</span>
            <button onClick={() => setScale(s => Math.min(2.0, s + 0.1))}>+</button>
          </div>
          
          {/* Page Navigation */}
          <div className="flex items-center space-x-2">
            <button onClick={() => setPageNumber(p => Math.max(1, p - 1))} disabled={pageNumber <= 1}>
              Previous
            </button>
            <span>Page {pageNumber} of {numPages}</span>
            <button onClick={() => setPageNumber(p => Math.min(numPages, p + 1))} disabled={pageNumber >= numPages}>
              Next
            </button>
          </div>
          
          {/* Download */}
          <a href={pdfUrl} download className="btn-secondary">
            Download
          </a>
          
          {/* Close */}
          <button onClick={onClose}>✕</button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-gray-900 flex items-center justify-center p-4">
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<div className="text-white">Loading PDF...</div>}
          error={<div className="text-red-500">Failed to load PDF</div>}
        >
          <Page 
            pageNumber={pageNumber} 
            scale={scale}
            renderTextLayer={true}
            renderAnnotationLayer={true}
          />
        </Document>
      </div>
    </div>
  );
};

export default PDFViewer;
```

---

#### Phase 3: Integrate with DocumentViewer (30 minutes)

**Modify:** `frontend/src/components/documents/DocumentViewer.tsx`

```typescript
// Add state
const [showPDFViewer, setShowPDFViewer] = useState(false);
const [pdfUrl, setPdfUrl] = useState<string>('');

// Add View PDF button (next to download button)
{document.status === 'EFFECTIVE' && (
  <button
    onClick={() => {
      const url = `/api/v1/documents/${document.uuid}/download_official_pdf/`;
      setPdfUrl(url);
      setShowPDFViewer(true);
    }}
    className="btn-primary"
  >
    📄 View PDF
  </button>
)}

// Add PDF Viewer modal
{showPDFViewer && (
  <PDFViewer
    pdfUrl={pdfUrl}
    documentTitle={document.title}
    onClose={() => setShowPDFViewer(false)}
  />
)}
```

---

#### Phase 4: Handle Authentication (30 minutes)

PDF requests need authentication tokens:

```typescript
// Create authenticated PDF URL
const fetchPDFWithAuth = async (documentUuid: string) => {
  const response = await apiService.get(
    `/documents/${documentUuid}/download_official_pdf/`,
    { responseType: 'blob' }
  );
  
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);
  return url;
};

// Use in component
const handleViewPDF = async () => {
  setLoading(true);
  try {
    const url = await fetchPDFWithAuth(document.uuid);
    setPdfUrl(url);
    setShowPDFViewer(true);
  } catch (error) {
    console.error('Failed to load PDF:', error);
    alert('Failed to load PDF');
  } finally {
    setLoading(false);
  }
};
```

---

#### Phase 5: Testing (30 minutes)

**Test Cases:**
1. ✅ View approved document PDF
2. ✅ Page navigation works
3. ✅ Zoom in/out works
4. ✅ Download button works
5. ✅ Close button works
6. ✅ Non-approved docs don't show view button
7. ✅ Loading state displays
8. ✅ Error handling works
9. ✅ Mobile responsive

---

## 🎨 UI/UX Considerations

### Where to Add View Button

**Option A: Next to Download Button (Recommended)**
```
[📄 View PDF] [⬇️ Download]
```

**Option B: Replace Download with Dropdown**
```
[📄 Actions ▼]
  - View in Browser
  - Download PDF
  - Download Package
```

**Option C: Tab in Document Viewer**
```
Details | History | Workflows | Dependencies | [📄 PDF Preview]
```

### Responsive Design

- Desktop: Full-width viewer
- Tablet: Scaled to fit
- Mobile: Vertical scroll, simplified controls

---

## 📦 Bundle Size Impact

**Current frontend bundle:** ~2-3 MB

**After adding react-pdf:**
- react-pdf: ~100 KB
- pdfjs-dist: ~500 KB
- **Total increase:** ~600 KB (~20% increase)

**Mitigation:**
- Code splitting: Load PDF viewer only when needed
- Lazy loading: `const PDFViewer = lazy(() => import('./PDFViewer'))`
- Reduces initial bundle, loads on demand

---

## 🚀 Quick Start (Option 2: Native Browser)

**If you want something quick and simple:**

```typescript
// No dependencies needed!
const PDFViewerSimple: React.FC<{ pdfUrl: string, onClose: () => void }> = ({ pdfUrl, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col">
      <div className="bg-gray-100 p-4 flex justify-between">
        <h3>PDF Viewer</h3>
        <button onClick={onClose}>Close</button>
      </div>
      <iframe 
        src={pdfUrl} 
        className="flex-1 w-full"
        title="PDF Viewer"
      />
    </div>
  );
};
```

**Time:** 10 minutes  
**Works:** Chrome, Firefox, Edge  
**Limitations:** Basic controls only

---

## 🎯 Recommendation

### For Production: Use react-pdf

**Why:**
- Professional appearance
- Full control over UI
- Better mobile support
- Consistent across browsers
- Can add custom features later

**When to implement:**
- Now (2-3 hours work)
- Or next sprint (if tight on time)

### For Quick Demo: Use iframe

**Why:**
- Immediate functionality
- Zero dependencies
- Test user interest
- Can upgrade to react-pdf later

**When to implement:**
- Now (30 minutes)
- Good for testing user feedback

---

## 📝 Implementation Steps (Quick Start)

### Recommended: Start with iframe, upgrade to react-pdf later

**Step 1: Simple Implementation (30 min)**
```bash
# No npm install needed!
# Add PDFViewerSimple component
# Add View button to DocumentViewer
# Test with approved docs
```

**Step 2: Gather Feedback (1 week)**
- Do users actually use it?
- What features do they want?
- Is performance acceptable?

**Step 3: Upgrade to react-pdf (2 hours)**
```bash
npm install react-pdf pdfjs-dist
# Replace PDFViewerSimple with full PDFViewer
# Add zoom, page navigation, etc.
```

---

## 💡 Additional Features (Future)

Once basic viewer is working:

1. **Thumbnails** - Page previews sidebar
2. **Search** - Find text in PDF
3. **Annotations** - Add comments/highlights
4. **Print** - Print from viewer
5. **Rotate** - Rotate pages
6. **Fullscreen** - Expand to full screen
7. **Comparison** - Side-by-side version comparison

---

## 🔒 Security Considerations

### Access Control
- ✅ Already handled by backend
- ✅ Only approved/effective docs
- ✅ User authentication required

### Content Security
- ✅ PDFs served through API (not direct file access)
- ✅ Blob URLs expire when page closes
- ✅ No persistent caching in browser

### Performance
- ⚠️ Large PDFs may be slow
- ⚠️ Consider file size limits
- ⚠️ Add loading indicators

---

## ✅ Decision Matrix

| Feature | iframe | react-pdf | PDF.js Direct |
|---------|--------|-----------|---------------|
| **Time to implement** | 30 min | 2-3 hours | 4-6 hours |
| **Bundle size** | 0 KB | +600 KB | +500 KB |
| **UI Control** | ❌ None | ✅ Full | ✅ Complete |
| **Mobile support** | ⚠️ Limited | ✅ Good | ✅ Full |
| **Custom features** | ❌ No | ✅ Yes | ✅ Yes |
| **Browser consistency** | ⚠️ Varies | ✅ Consistent | ✅ Consistent |
| **Maintenance** | ✅ Low | ✅ Medium | ⚠️ High |

---

## 🎯 My Recommendation

**Start Simple, Iterate:**

1. **Week 1:** Implement iframe version (30 min)
2. **Week 2:** Gather user feedback
3. **Week 3:** Upgrade to react-pdf if users love it

**Or, if you want production-quality now:**

Implement react-pdf directly (2-3 hours total)

---

**Which approach would you like to take?**

1. 🚀 **Quick & Simple** - iframe viewer (30 min)
2. ⭐ **Full Featured** - react-pdf viewer (2-3 hours)
3. 🤔 **Let me think** - more questions first

---

*Created: 2026-01-30*  
*Status: Implementation Ready*
