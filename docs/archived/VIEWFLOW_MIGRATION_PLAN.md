# Viewflow Migration Plan - EDMS Workflow Engine Upgrade

## Executive Summary

**Decision**: Migrate from Django-River to Viewflow for the EDMS workflow engine
**Timeline**: 2-3 days
**Status**: Approved for implementation
**Branch**: `feature/viewflow-migration`

## Background

### Current State (Django-River Issues)
- ❌ Last updated: January 2021 (4+ years abandoned)
- ❌ Django 4.2 compatibility issues requiring workarounds
- ❌ Limited maintenance and community support
- ❌ Technical debt accumulation risk

### Target State (Viewflow Benefits)
- ✅ Active maintenance (latest: v2.2.13, September 2024)
- ✅ Django 4.2/5.0 native compatibility
- ✅ Built-in audit trails for 21 CFR Part 11 compliance
- ✅ Professional-grade workflow features
- ✅ Better performance and scalability

## Migration Strategy

### Phase 1: Documentation & Planning (Day 1 - Morning)
- [x] Document migration plan
- [x] Create feature branch
- [x] Commit current working state
- [ ] Research Viewflow patterns for EDMS workflows

### Phase 2: Viewflow Installation & Setup (Day 1 - Afternoon)
- [ ] Install django-viewflow package
- [ ] Update requirements.txt
- [ ] Configure basic Viewflow settings
- [ ] Create initial flow definitions

### Phase 3: Core Workflow Implementation (Day 2)
- [ ] Implement DocumentReviewFlow
- [ ] Implement DocumentApprovalFlow
- [ ] Implement DocumentUpVersionFlow
- [ ] Implement DocumentObsoleteFlow
- [ ] Create workflow views and forms

### Phase 4: Integration & Testing (Day 2-3)
- [ ] Update API endpoints for Viewflow
- [ ] Migrate existing workflow data
- [ ] Update frontend integration
- [ ] Comprehensive testing
- [ ] Documentation updates

### Phase 5: Validation & Deployment (Day 3)
- [ ] Performance testing
- [ ] Security validation
- [ ] Compliance verification
- [ ] Merge to main branch

## Technical Implementation Details

### 1. Workflow Definitions (Viewflow Flows)

#### Document Review Flow
```python
class DocumentReviewFlow(Flow):
    class Meta:
        task_class = DocumentTask
        
    start = flow.Start(DocumentCreateView) \
        .Permission('documents.add_document') \
        .Next(this.review)
    
    review = flow.View(DocumentReviewView) \
        .Assign(lambda process: process.document.assigned_reviewer) \
        .Next(this.check_review)
    
    check_review = flow.If(cond_review_approved) \
        .Then(this.approve) \
        .Else(this.revise)
    
    approve = flow.View(DocumentApprovalView) \
        .Permission('documents.can_approve') \
        .Next(this.effective)
    
    effective = flow.View(DocumentEffectiveView) \
        .Next(this.end)
    
    revise = flow.View(DocumentRevisionView) \
        .Next(this.review)
    
    end = flow.End()
```

### 2. Database Schema Changes

#### New Viewflow Tables
- `viewflow_process` - Workflow process instances
- `viewflow_task` - Individual workflow tasks
- `document_review_flow_process` - Document-specific process data

#### Migration Strategy
- Preserve existing document data
- Map current workflow states to Viewflow processes
- Maintain audit trail integrity

### 3. API Integration

#### Updated Endpoints
- `/api/v1/workflows/processes/` - Process management
- `/api/v1/workflows/tasks/` - Task management
- `/api/v1/workflows/flows/` - Flow definitions

### 4. Frontend Integration

#### Component Updates
- `WorkflowConfiguration.tsx` - Viewflow process configuration
- `DocumentViewer.tsx` - Viewflow task actions
- `Dashboard.tsx` - Viewflow task lists

## Compliance Benefits

### 21 CFR Part 11 Enhancements
1. **Built-in Audit Trails**: Automatic logging of all workflow actions
2. **Electronic Signatures**: Native integration with signature workflows
3. **Access Controls**: Granular permission management
4. **Data Integrity**: Built-in validation and checksums
5. **Retention Policies**: Configurable data retention for compliance

### ALCOA Principle Alignment
- **Attributable**: All actions tied to authenticated users
- **Legible**: Clear audit trail format
- **Contemporaneous**: Real-time activity logging
- **Original**: Immutable process records
- **Accurate**: Built-in data validation

## Risk Assessment

### Low Risk Items
- ✅ Package stability (Viewflow is actively maintained)
- ✅ Django compatibility (native Django 4.2 support)
- ✅ Feature completeness (comprehensive workflow features)

### Managed Risks
- ⚠️ **Data Migration**: Careful mapping of existing workflow states
  - *Mitigation*: Thorough testing with backup/restore procedures
- ⚠️ **Frontend Integration**: API endpoint changes
  - *Mitigation*: Maintain backward compatibility during transition
- ⚠️ **User Training**: New workflow interface
  - *Mitigation*: Similar UI patterns, minimal user impact

## Success Criteria

### Technical Criteria
- [ ] All existing workflow functionality preserved
- [ ] Performance equal or better than current implementation
- [ ] Zero data loss during migration
- [ ] All tests passing
- [ ] API compatibility maintained

### Business Criteria
- [ ] Document lifecycle workflows operational
- [ ] User permissions and roles functional
- [ ] Audit trails complete and compliant
- [ ] Frontend workflow interfaces working
- [ ] Phase 6 (Compliance) implementation ready

## Rollback Plan

### If Migration Fails
1. **Immediate Rollback**: Revert to previous branch
2. **Data Restoration**: Restore from pre-migration backup
3. **Service Restoration**: Resume with current Django-River workaround
4. **Post-Mortem**: Analyze failure points and revise plan

### Rollback Triggers
- Data integrity issues during migration
- Performance degradation > 50%
- Critical workflow functionality broken
- Unable to resolve within 1 additional day

## Dependencies

### Technical Dependencies
- `django-viewflow>=2.2.13`
- `django>=4.2`
- Current EDMS codebase
- PostgreSQL/SQLite database

### Team Dependencies
- Development time allocation (2-3 days)
- Testing resources for validation
- Documentation updates

## Documentation Updates Required

### Technical Documentation
- [ ] Update `Dev_Docs/3_Django_River_Workflow_Setup.md` → `3_Viewflow_Workflow_Setup.md`
- [ ] Update API specifications
- [ ] Update database schema documentation
- [ ] Update deployment guides

### User Documentation
- [ ] Workflow user guides
- [ ] Administrator workflow management
- [ ] API integration examples

## Communication Plan

### Stakeholder Notifications
- **Development Team**: Immediate notification of migration start
- **QA Team**: Testing requirements and timeline
- **Documentation Team**: Update requirements
- **End Users**: No immediate impact (UI remains consistent)

## Next Steps

1. **Immediate Actions** (Today):
   - [x] Create feature branch
   - [x] Commit current state
   - [ ] Begin Viewflow research and setup

2. **Tomorrow**:
   - [ ] Implement core workflows
   - [ ] Begin integration testing

3. **Day After**:
   - [ ] Complete testing and validation
   - [ ] Prepare for merge to main

---

**Prepared by**: Rovo Dev  
**Date**: January 2025  
**Status**: Ready for Implementation  
**Next Action**: Create feature branch and begin implementation