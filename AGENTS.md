# Workspace Memory for EDMS Development

## Key Insights from Development Sessions

### Import Path Resolution
- **Critical**: Always include `.tsx` extensions in import statements to avoid module resolution errors
- Example: Use `'./CommentHistory.tsx'` not `'./CommentHistory'`
- This prevents compilation failures in React TypeScript projects

### State Synchronization Challenges
- **Document vs Workflow State**: Frontend document status may not match backend workflow state
- Always verify both `document.status` and `workflow.current_state.code` are aligned
- Workflow engines often validate against workflow state, not document status
- Fix mismatches at the workflow level, not just document level

### API Endpoint Verification Strategy
- **Always verify current app state** before architectural changes
- Check if services are actually running in Docker vs local development
- Test API endpoints exist before building frontend features around them
- When endpoints return 404, create self-contained fallback solutions using available data

### Defensive Programming Patterns
- **Null safety for object properties**: Use `document?.version_major || 0` instead of `document.version_major.toString()`
- Prevents runtime crashes from undefined/null values
- Essential for React components that may receive incomplete data

### Role-Based Security Implementation
- **Dual validation**: Implement permission checks both frontend and backend
- **Self-exclusion logic**: Use `user.id !== document.author_id` to prevent self-review/approval
- **Use actual role groups**: Filter by Django group membership, not username patterns
- Provides enterprise-grade security for workflow systems

### Component Design Philosophy
- **Unified over duplicated**: Replace similar components (ReviewerInterface/ApproverInterface) with single configurable component
- **Shared base patterns**: Create BaseModal components for consistent UI
- **Progressive enhancement**: Build basic functionality first, add API-dependent features after
- Reduces maintenance burden and improves UX consistency

### Debug-Driven Development
- **Comprehensive logging**: Add detailed console logs for complex workflows
- **Error context**: Capture request/response details for API debugging  
- **User-friendly fallbacks**: Always provide meaningful error messages and graceful degradation
- **Targeted debug logging**: When troubleshooting complex workflows, add specific debug prints at each step rather than generic logging - this pinpoints exact failure points
- Essential for troubleshooting production issues

### FormData Structure Alignment
- **Backend expectations**: Verify API expects `dependencies[0]` not `dependencies[0][id]`
- **Simple array format**: Often simpler data structures work better than nested objects
- Test FormData structure with actual API before complex frontend logic

### Docker Architecture Considerations
- **Security vs Development**: Current setup exposes all services externally (development-style)
- **Intended architecture**: Only frontend should be externally accessible in production
- **Migration planning**: Keep both dev and secure configurations for different use cases
- Always verify what's actually running before proposing architectural changes

These insights focus on patterns that prevent common development pitfalls and improve code reliability across similar projects.

## Component Unification Patterns

### Modal Consolidation Benefits
- **Code Deduplication**: Components with 90%+ similarity (SubmitForReviewModal vs RouteForApprovalModal) benefit from unification with configuration parameters
- **Maintenance Reduction**: Single source of truth reduces bugs and simplifies testing
- **Enhanced Features**: Unified components enable consistent feature rollout (e.g., rejection awareness across all workflow actions)

### Permission-Based Routing Issues
- **Document State Permissions**: can_edit() may restrict operations based on document status (e.g., REVIEWED documents can't be modified via PATCH)
- **Workflow-Specific Permissions**: Route approval may need direct workflow API calls to bypass document-level edit restrictions
- **API Strategy**: Different workflow actions may require different API approaches (PATCH + POST vs direct workflow API)

## Workflow Integration Patterns

### Notification System Architecture
- **Multi-layer integration required**: Notifications alone are insufficient - must create corresponding WorkflowTask objects for complete user experience
- **API response field alignment**: Frontend components often expect specific field names (e.g., `reviewer_username` vs `reviewer`) - add serializer fields to match frontend expectations rather than changing frontend logic
- **Database field validation**: Always verify actual model field names before writing code - assumptions about field names (`status` vs `is_active`, `created_by` vs `initiated_by`) cause runtime errors

### HTTP Polling Strategy
- **HTTP polling for dashboard updates**: Simple, reliable 60-second polling for document workflow status updates perfectly suits human-paced document management workflows
- **Authentication simplicity**: HTTP authentication is straightforward and well-understood - no WebSocket complexity needed for document management use cases
- **User experience**: Clear polling indicators show system is actively updating data

### Architecture Migration Patterns
- **Progressive elimination over rewriting**: When removing complex systems (like WorkflowTask), disable imports first, then remove dependencies systematically rather than attempting to fix all syntax errors
- **Migration dependencies**: Check actual migration file dependencies before creating new migrations - auto-generated dependency references may not exist
- **Component consolidation**: Replace multiple similar components (MyTasks, TaskList, etc.) with single configurable component using URL parameters for different views
- **Direct fetch over hook complexity**: For simple polling scenarios, direct fetch calls can be more reliable than complex custom hooks that may have circular dependencies

### Database Migration and Development Flow
- **Incremental database changes**: Add fields via proper migrations rather than manual SQL to avoid dependency issues
- **Field existence verification**: Use `getattr()` and `hasattr()` when adding new fields to handle cases where migrations haven't run yet
- **Container service dependencies**: When modifying database schema, ensure Django Channels dependencies are properly installed and container is rebuilt

### API Endpoint and User Context Issues

### Authentication Context Mismatches
- **Multi-User Systems**: Always verify which user account frontend API calls are executing under - badge logic may fetch data for wrong user
- **Consistent API Endpoints**: Ensure badge counts and page content use same API endpoints/filters for consistency
- **User Session Verification**: Test API responses with actual logged-in user context, not assumed test users

### Mock Data vs Real Data Problems
- **History Tab Issue Pattern**: Components may show mock/placeholder data instead of real database content due to missing or incorrect API integration
- **API Endpoint Verification**: Always confirm API endpoints exist and return expected data structure before assuming frontend component issues
- **Progressive Fallback Strategy**: Implement graceful fallback from detailed API data → basic document data → mock data with clear user messaging

## Frontend-Backend Integration Debugging
- **API endpoint verification first**: Always verify API endpoints exist and return expected data structure before debugging frontend logic
- **Response structure mapping**: Frontend components may expect different data structures than backend provides - check actual API response format vs frontend expectations
- **URL pattern matching**: Ensure URL patterns match between frontend calls (`my-notifications`) and backend routes (`my_notifications`) - hyphens vs underscores matter
- **Navigation highlighting with query parameters**: When using URL query parameters for filtering (e.g., `/document-management?filter=pending`), navigation highlighting logic needs special handling to distinguish between base routes and filtered routes
- **UX principle - proximity and single action**: Place counters/badges directly on navigation items rather than separate header elements to reduce cognitive load and provide clearer user affordance
- **Document-centric architecture benefits**: For document management systems, consolidating around document filtering with query parameters (/document-management?filter=type) provides better UX than separate pages for different document states
- **Modern navigation patterns**: Following established app patterns (Gmail's inbox badges, Slack's channel counters) improves user adoption and reduces cognitive load

### Search Filter Implementation
- **Backend-frontend filter alignment**: Always verify backend DocumentFilter capabilities before implementing frontend search options - remove unsupported filters (e.g., department) to prevent user confusion
- **API parameter format consistency**: Backend expects repeated parameters for arrays (`status=DRAFT&status=APPROVED`) not nested objects - implement proper array handling in frontend API calls
- **Filter relevance assessment**: Regularly audit search filters - remove 40-60% irrelevant filters and add missing high-value options (title, description, document_number) for better user experience
- **Status filter maintenance**: Keep frontend DocumentStatus types synchronized with backend STATUS_CHOICES - mismatched status values cause 400 API errors

### Development Environment Architecture
- **Container networking over localhost**: Use service names (`backend:8000`) instead of `localhost:8000` for container-to-container communication
- **Development vs production patterns**: Keep both localhost development configs and containerized configs for different use cases
- **Standard Django WSGI**: HTTP-only implementation uses standard Django WSGI deployment - no ASGI complexity needed

## Container Rebuild Requirements

### Docker Container Dependencies
- **LibreOffice Installation**: When adding system dependencies like LibreOffice for PDF conversion, container rebuild is mandatory - code changes alone are insufficient
- **System Package Changes**: Any modifications to Dockerfile (apt-get install) require `docker compose build <service>` before taking effect
- **Development vs Production**: Both development and production Dockerfiles need synchronization when adding system dependencies

### PDF Conversion Quality Indicators
- **File Size Indicators**: PDF output size indicates conversion quality - 9KB suggests basic ReportLab fallback, 50-100KB+ indicates proper LibreOffice conversion
- **Tool Priority**: LibreOffice headless → docx2pdf → ReportLab (decreasing quality)
- **Container Verification**: Always test tool availability with `docker compose exec backend <tool> --version` after rebuild

## Container and Module Caching Issues

### Python Module Caching in Docker
- **Django module reloading problems**: Django may use cached bytecode even after file changes - use `docker compose restart` rather than just container restart
- **Python cache clearing**: When code changes don't apply, manually clear Python cache with `find /app -name "*.pyc" -delete` and `find /app -name "__pycache__" -type d -exec rm -rf {} +`
- **Force module reload**: Use `importlib.reload()` in Django shell for testing code changes without full container restart
- **Docker volume mounting**: Ensure source code is properly mounted as volumes for development, not copied into container images

### API Endpoint Consistency Patterns
- **URL endpoint discrepancies**: Common API path mistakes include `/documents/documents/` vs `/documents/` - always verify the actual endpoint structure before debugging frontend issues
- **Parameter validation order**: Backend method signatures matter - check parameter order (e.g., `approve_document(document, user, effective_date, comment, approved)`) when adding new parameters
- **Boolean parameter handling**: JSON boolean `false` may not be properly detected in Django views - use explicit checks like `approved is False or str(approved).lower() == 'false'`

### Workflow State Consistency
- **Database state vs workflow state mismatches**: Documents marked as `APPROVED_AND_EFFECTIVE` may still have unterminated workflows (`is_terminated=False`) causing validation failures
- **System-wide consistency fixes**: When fixing workflow state issues, check for patterns across multiple documents rather than fixing individual cases
- **Validation logic enhancement**: Include `is_terminated=False` filters when checking for active workflows to prevent completed workflows from blocking operations

### Backend Troubleshooting Strategy
- **Systematic syntax error resolution**: When extensive model removal creates cascading syntax errors, use targeted approach: fix imports first, then disable problematic modules temporarily to get core functionality working
- **Migration dependency verification**: Always check existing migration files before referencing dependencies in new migrations - don't assume migration names based on logical sequence
- **Container restart vs rebuild**: For complex dependency changes, full container rebuild may be needed rather than just restart
- **Temporary import disabling**: When removing complex systems, temporarily disable imports with minimal stub implementations to isolate core functionality
- **Iterative syntax fixing**: When automated cleanup creates multiple syntax errors, fix one at a time systematically rather than attempting to fix all at once - missing parentheses, commas, and orphaned code blocks are common patterns

## Data Consolidation and Business Logic Simplification

### Status Consolidation Patterns
- **Functional equivalence assessment**: When multiple statuses represent the same business state (e.g., `APPROVED_AND_EFFECTIVE` vs `EFFECTIVE`), analyze actual usage patterns before architectural decisions
- **Data migration strategy**: Use systematic approach: data migration → code updates → frontend cleanup → verification, with transaction safety at each step
- **Legacy status handling**: Don't remove DocumentState records immediately - keep for audit trail while updating code to use consolidated status
- **Backend-frontend alignment**: Update both serializer choices AND frontend TypeScript types simultaneously to prevent API validation errors

### API Response Structure Mismatches
- **Component-API integration gaps**: Frontend components may expect different response formats than APIs provide - transform data at the API boundary rather than modifying components
- **Missing endpoint vs broken integration**: When components show fallback data, verify if the expected API endpoint exists before assuming frontend bugs
- **Response format evolution**: APIs may return different structures over time - always check actual response format when debugging historical integrations

## Navigation State Management

### Page Navigation Cleanup Patterns
- **Filter-based navigation**: When navigation uses URL parameters instead of separate routes, use `useEffect([filterType])` to clear state on filter changes
- **Cross-route state persistence**: Component state may persist across navigation - implement cleanup in both component unmount AND route change listeners
- **Event-driven cleanup**: Use custom events (`clearDocumentSelection`) for cross-component state clearing when direct prop passing isn't feasible

### UI Polish and Professional Appearance
- **Step-based UI patterns**: Technical step indicators ("Step 1", "Step 2") in user-facing elements reduce professional appearance - replace with descriptive action labels
- **Contextual refresh strategies**: Manual refresh buttons should be contextual to specific pages rather than global header elements - leverages existing auto-refresh infrastructure while providing user control