---
name: Workflow Specification Compliance Issue
about: Track workflow module compliance with EDMS specifications
title: 'Workflow Module Specification Compliance Assessment - Critical Gaps Identified'
labels: workflow, compliance, critical, specification
assignees: ''
---

# 🚨 Workflow Module Specification Compliance Gaps

## Issue Summary

**Priority**: 🔴 High  
**Type**: 📋 Compliance Task  
**Epic**: Workflow Engine Compliance  
**Current Grade**: C+ (70/100)

The Enhanced Simple Workflow Engine has been assessed against `Dev_Docs/EDMS_details_workflow.txt` and shows **70% compliance** with several critical gaps preventing full specification adherence.

## 🎯 Current Status

### Document States Mismatch
**Expected vs Implemented:**
- ❌ "Pending Review" → "PENDING_REVIEW" 
- ❌ "Reviewed" → Missing
- ❌ "Approved, Pending Effective" → Missing  
- ❌ "Approved and Effective" → "EFFECTIVE"
- ❌ "Pending Obsoletion" → Missing

### Critical Missing Integration
- [ ] Document upload during workflow creation
- [ ] Document download with reviewer comments
- [ ] Automated effective date transitions (scheduler)
- [ ] Document dependency checking for obsoleting
- [ ] Workflow termination capability

## 🛠️ Phase 1: Critical Fixes (Sprint 1-2)

### Task 1: Fix Document State Naming
- [ ] Update DocumentState model to match specification exactly
- [ ] Create migration for state name changes  
- [ ] Update all references to use new state names
- [ ] Test state transition compatibility

### Task 2: Document Integration
- [ ] Add document upload to workflow creation process
- [ ] Create document download endpoints within workflow context
- [ ] Implement reviewer comment attachment system
- [ ] Add document version tracking during workflows

### Task 3: Scheduler Integration
- [ ] Implement Celery task for effective date automation
- [ ] Create `check_effective_dates()` background task
- [ ] Schedule automatic state transitions
- [ ] Add scheduler health monitoring

## 📋 Acceptance Criteria

### Definition of Done
- [ ] All document states match specification naming exactly
- [ ] Document upload/download integrated with workflows
- [ ] Scheduler automatically transitions on effective dates
- [ ] Comprehensive test coverage for changes
- [ ] Documentation updated

### Testing Requirements
- [ ] Unit tests for state transitions
- [ ] Integration tests for document handling
- [ ] End-to-end workflow cycle tests
- [ ] Performance tests for scheduler

## 📊 Success Metrics

**Target**: 90%+ specification compliance
- [ ] All critical workflow paths functional
- [ ] Zero critical compliance gaps
- [ ] Maintained audit trail compliance
- [ ] Performance <200ms API responses

## 🔗 Related Files

**Backend:**
- `backend/apps/workflows/models.py` - State definitions
- `backend/apps/workflows/services.py` - Business logic
- `backend/apps/workflows/tasks.py` - Scheduler tasks

**Frontend:**
- `frontend/src/components/workflows/` - UI components

**Documentation:**
- `Dev_Docs/EDMS_details_workflow.txt` - Specification
- `WORKFLOW_COMPLIANCE_ASSESSMENT.md` - Detailed assessment

---

**Assessment Reference**: WORKFLOW_COMPLIANCE_ASSESSMENT.md  
**Specification**: Dev_Docs/EDMS_details_workflow.txt