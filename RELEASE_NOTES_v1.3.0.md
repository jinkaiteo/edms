# Release Notes - EDMS v1.3.0

**Release Date:** 2026-01-30  
**Version:** 1.3.0  
**Branch:** main  
**Commit:** ad94bb6

---

## 🎉 New Features

### 1. Interactive Dependency Graph Visualization 📊

A powerful new way to visualize document dependencies and relationships.

**Key Capabilities:**
- **Graph View**: Interactive node-based visualization using ReactFlow
  - Drag and drop nodes to arrange layout
  - Zoom and pan for large dependency trees
  - Color-coded nodes (current document in blue, dependencies/dependents in gray)
  - Animated edges showing relationship flow
  
- **Tree View**: Hierarchical list view of dependencies
  - Collapsible/expandable sections
  - Clear parent-child relationships
  - Easy navigation to related documents

- **Toggle Between Views**: Switch between graph and tree views instantly
  - View mode preference saves per session
  - Responsive design works on all screen sizes

**Where to Find It:**
- Navigate to any document with dependencies
- Open the "Dependencies" tab
- Click "View Graph" or "View Tree" buttons

**Technical Details:**
- Added `@xyflow/react v12.10.0` for graph rendering
- New components: `DependencyGraphView.tsx`, `DependencyTreeView.tsx`
- Enhanced backend API with `dependency_chain` endpoint
- Includes `parent_id` tracking for hierarchy visualization

---

### 2. Auto-Copy Dependencies on Upversion 🔄

Documents now automatically maintain their dependency relationships when creating new versions.

**How It Works:**
- When you create a new version of a document, all dependencies are automatically copied
- Dependencies are **smart-resolved** to the latest EFFECTIVE version
- Example: If v1.0 depends on POLICY-v1.0, and you create v2.0, it will depend on POLICY-v3.0 (if that's the latest EFFECTIVE version)
- Fallback: If no EFFECTIVE version exists, copies the original dependency

**Benefits:**
- ✅ No manual dependency management needed
- ✅ Always references current approved documents
- ✅ Maintains compliance with latest standards
- ✅ Audit trail with "Auto-copied from v1.0" descriptions

**Technical Details:**
- Added `_copy_dependencies_smart()` method to `DocumentLifecycleService`
- Added `_find_latest_effective_version()` helper method
- Runs automatically during `start_version_workflow()`

---

## 🐛 Bug Fixes

### Fixed: Incorrect Arrow Directions in Dependency Graph

**Problem:**
- All arrows pointed away from the current document regardless of relationship type
- Made it impossible to distinguish dependencies from dependents

**Solution:**
- Fixed edge direction logic in `DependencyGraphView.tsx`
- **Dependencies** (left side): Arrows point FROM dependency TO current document
- **Dependents** (right side): Arrows point FROM current document TO dependent
- Clear visual distinction of "depends on" vs "is depended on by"

**Impact:** Users can now correctly understand document relationships at a glance

---

### Fixed: Missing Dependencies After Upversion

**Problem:**
- Creating new document versions through workflow didn't copy dependencies
- New versions appeared "orphaned" without relationships

**Solution:**
- Added dependency copying logic to workflow lifecycle service
- Matches behavior of direct API endpoint
- Ensures consistency across all upversion paths

**Impact:** All new versions maintain proper dependency relationships

---

## 🔧 Technical Improvements

### Backend Changes
- **Modified Files:**
  - `backend/apps/documents/models.py` - Enhanced dependency chain methods
  - `backend/apps/documents/views.py` - Added dependency API endpoints
  - `backend/apps/workflows/document_lifecycle.py` - Added dependency copying

### Frontend Changes
- **New Components:**
  - `frontend/src/components/documents/DependencyGraphView.tsx` (406 lines)
  - `frontend/src/components/documents/DependencyTreeView.tsx` (254 lines)
  
- **Modified Components:**
  - `frontend/src/components/documents/DependencyVisualization.tsx` - Refactored for view modes
  - `frontend/src/components/documents/DocumentViewer.tsx` - Integrated new visualization

### Dependencies
- **Added:** `@xyflow/react@^12.10.0` - React Flow library for graph visualization
- **Updated:** `frontend/package-lock.json` - Locked dependency versions

---

## 📊 Statistics

- **Files Changed:** 10
- **Lines Added:** +1,316
- **Lines Removed:** -314
- **Net Change:** +1,002 lines
- **New Components:** 2
- **New Methods:** 3
- **Bug Fixes:** 2

---

## 🚀 Deployment Notes

### Requirements
- No new environment variables
- No database migrations required
- Frontend rebuild required (new npm package)
- Backend restart required (code changes)

### Deployment Steps
1. Pull latest main branch
2. Run `docker compose build` (installs new npm package)
3. Run `docker compose up -d`
4. Verify deployment with test checklist

### Deployment Time
- **Expected:** 10-15 minutes
- **Docker Build:** 5-8 minutes
- **Service Startup:** 2-3 minutes
- **Verification:** 2-4 minutes

---

## ✅ Testing Checklist

### After Deployment, Verify:

**Dependency Graph Visualization:**
- [ ] Navigate to a document with dependencies
- [ ] Click "View Graph" button
- [ ] Verify graph renders with correct layout
- [ ] Verify arrows point in correct directions
- [ ] Test drag and drop functionality
- [ ] Test zoom and pan
- [ ] Switch to tree view
- [ ] Verify tree shows correct hierarchy

**Dependency Copying on Upversion:**
- [ ] Select a document with dependencies
- [ ] Create new version
- [ ] Complete upversion workflow
- [ ] Verify new version shows dependencies
- [ ] Check dependency descriptions show "Auto-copied"
- [ ] Verify dependencies point to latest EFFECTIVE versions

**Backward Compatibility:**
- [ ] Existing features work unchanged
- [ ] Document list loads correctly
- [ ] Document viewer displays properly
- [ ] All workflows function normally

---

## 🔄 Rollback Plan

If issues arise:

```bash
# Rollback to previous version
git checkout 5cae7d4
docker compose build
docker compose up -d
```

**Previous Stable Version:** 5cae7d4 (2026-01-29)

---

## 📝 Known Issues

None at this time.

---

## 🎯 Next Steps / Roadmap

**Potential Enhancements:**
- Export dependency graphs as images (PNG/SVG)
- Dependency impact analysis ("What documents are affected if I update this?")
- Circular dependency detection and alerts
- Dependency version pinning (lock to specific versions)
- Bulk dependency updates
- Dependency change notifications

---

## 👥 Contributors

- **Development:** Rovo Dev AI Assistant
- **Testing:** QMS Team
- **Deployment:** Staging Server (2026-01-30)

---

## 📚 Documentation

- **Deployment Analysis:** `DEPLOYMENT_ANALYSIS_DEPENDENCY_GRAPH.md`
- **Feature Documentation:** See "Dependencies" tab in Document Viewer
- **API Documentation:** `/api/v1/documents/{uuid}/dependency_chain/`

---

## 🔗 Related Resources

- **GitHub Commit:** ad94bb6
- **Feature Branch:** feature/dependency-graph-visualization (merged and deleted)
- **Previous Release:** v1.2.0 (5cae7d4)

---

**For questions or issues, please contact the development team.**

---

*This release improves document relationship management and visualization, making it easier to understand and maintain document dependencies in compliance workflows.*
