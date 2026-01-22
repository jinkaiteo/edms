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
- **Badge and counter logic**: Always implement conditional rendering for UI badges (`count > 0`) to avoid displaying "0" values - users expect badges to appear only when actionable
- **Navigation state management**: Implement proper route-based selection logic to prevent multiple navigation items appearing selected simultaneously
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

## Status Naming and System Integration

### Check Automated Systems Before Standardizing Statuses
When choosing between similar status names (e.g., EFFECTIVE vs APPROVED_AND_EFFECTIVE), always check what automated systems (schedulers, background tasks) expect FIRST before making architectural decisions.

**Critical Pattern**: Look for status references in:
- Scheduler tasks (`apps/scheduler/automated_tasks.py`)
- Celery tasks
- Management commands
- Any code that runs without user interaction

**Example from session**: Chose APPROVED_AND_EFFECTIVE for workflow but scheduler expected EFFECTIVE, causing:
- Approval workflow failures
- PDF download button disabled
- Dependencies not displaying
- Scheduler unable to activate pending documents

**Solution**: Standardized on EFFECTIVE (what scheduler expected) rather than forcing scheduler to change.

### Serializer Filter Debugging Pattern
When data exists in database but doesn't appear in API responses, check serializer filters BEFORE debugging frontend or backend logic.

**Symptom**: Backend logs show "saved successfully" but frontend shows empty arrays/null values.

**Common Cause**: Serializer method filters exclude the data:
```python
def get_dependencies(self, obj):
    # This filter might exclude valid data!
    return obj.dependencies.filter(
        depends_on__status__in=['EFFECTIVE']  # Wrong status = data hidden
    )
```

**Debugging Steps**:
1. Verify data exists in database (Django shell)
2. Check serializer get_* methods for status filters
3. Check if filter values match actual document statuses
4. Look for status__in=[...] patterns in List AND Detail serializers

**Prevention**: When adding new statuses, grep for all status filters: `grep -r "status__in=" backend/apps/*/serializers.py`

## Deployment Script Dependencies

### Initialization Order Matters: Analyze Foreign Keys
When writing initialization scripts, analyze ALL foreign key dependencies to determine correct execution order.

**Pattern**: Build dependency tree bottom-up:
1. Independent models (no FKs)
2. Models with FKs to #1
3. Models with FKs to #2
4. ...and so on

**Example from session**:
- WorkflowType has `created_by` FK to User
- Tried to create WorkflowTypes before Users existed
- Result: "No users found in database" error
- Solution: Create Users BEFORE WorkflowTypes

**Correct Sequence**:
```bash
1. Users (no dependencies)
2. Groups (no dependencies)  
3. Roles (FK to nothing critical)
4. WorkflowTypes (FK to User via created_by)
5. DocumentStates (no dependencies but referenced by WorkflowTypes)
6. Everything else
```

**Prevention**: Before writing init script, check model definitions:
```python
grep -A 10 "class WorkflowType" backend/apps/workflows/models.py
# Look for ForeignKey, OneToOneField, required fields
```

### Graceful Degradation in Deployment Scripts
Distinguish between critical and nice-to-have initialization steps. Make non-essential steps non-fatal.

**Critical (must succeed)**:
- Database migrations
- User creation
- Core workflow states
- Required configuration

**Nice-to-have (can fail)**:
- Static file collection (only affects admin UI)
- Cache warming
- Non-essential notifications
- UI theming

**Implementation**:
```bash
# Critical - exit on failure
if ! create_users; then
    error "User creation failed"
    exit 1
fi

# Nice-to-have - warn but continue
if ! collectstatic; then
    warn "Static files failed (non-critical, admin UI may lack styling)"
fi
```

**Benefit**: Deployment continues despite minor issues, reducing troubleshooting time.

## Docker Volume Management

### Volume Prune for Clean Slate
`docker-compose down -v` doesn't always remove volumes with permission issues. For truly clean deployments, use `docker volume prune -f`.

**Issue Pattern**:
- Old deployment created files as root
- New deployment runs as different user
- Volume persists with old permissions
- `down -v` claims to remove volume but files remain

**Symptoms**:
- PermissionError when accessing old files
- "Permission denied" on collectstatic
- Can't delete/overwrite existing files

**Nuclear Solution**:
```bash
docker-compose down
docker volume prune -f  # Removes ALL unused volumes
docker-compose up -d
```

**Surgical Solution** (if you need to keep some volumes):
```bash
docker-compose down
docker volume ls | grep problematic_volume
docker volume rm specific_volume_name
docker-compose up -d
```

**Prevention**: 
- Run containers as non-root user from start
- Use named volumes with proper ownership
- Document required volume cleanup in deployment guides
- Make collectstatic failures non-fatal (see Graceful Degradation)

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

### API Serializer Consistency Patterns
- **Synchronize serializer filtering**: When multiple serializers (List vs Detail) handle same data, ensure identical filtering logic to prevent frontend inconsistencies
- **Status filter alignment**: DocumentListSerializer and DocumentDetailSerializer must use identical status filtering (`APPROVED_PENDING_EFFECTIVE`, `EFFECTIVE`, `SCHEDULED_FOR_OBSOLESCENCE`) to avoid data discrepancies
- **Frontend data expectations**: When frontend components switch between list and detail APIs, ensure both return identical data structures and field coverage

### Database Field Constraints and Error Handling
- **CharField max_length constraints**: Always check model field max_length limits when writing audit trails or other dynamic content - Django's CharField fields have strict length limits (e.g., 30 chars for action fields)
- **Audit trail field optimization**: Use shortened, meaningful action names instead of descriptive sentences to avoid length constraint errors (e.g., `DOC_EFFECTIVE_PROCESSED` vs `DOCUMENT_EFFECTIVE_DATE_PROCESSED`)
- **JSON serialization safety**: Convert datetime objects to ISO format with `.isoformat()` before returning in API responses to prevent JSON serialization errors
- **Model field verification**: Before writing ORM queries, verify actual model field names exist - database schema may differ from assumptions (e.g., `status` field might not exist, use `is_active` and `is_completed` instead)
- **Protected foreign key recognition**: Django's ProtectedError on FK deletions is correct architecture, not a bug - respect these constraints rather than forcing deletion, as they preserve audit trails and data integrity

### API Endpoint and User Context Issues

### Authentication Context Mismatches
- **Multi-User Systems**: Always verify which user account frontend API calls are executing under - badge logic may fetch data for wrong user
- **Consistent API Endpoints**: Ensure badge counts and page content use same API endpoints/filters for consistency
- **User Session Verification**: Test API responses with actual logged-in user context, not assumed test users

### Real-World User Testing Value
- **Unit tests vs integration issues**: Real user testing often reveals frontend-backend integration problems that unit tests miss (e.g., incorrect filename construction, header handling)
- **Browser behavior verification**: Test actual download behavior in browsers - server may return correct data but client-side processing can introduce bugs
- **End-to-end validation**: Always test complete user workflows, not just individual API endpoints - issues often emerge in the full integration flow

### Mock Data vs Real Data Problems
- **History Tab Issue Pattern**: Components may show mock/placeholder data instead of real database content due to missing or incorrect API integration
- **API Endpoint Verification**: Always confirm API endpoints exist and return expected data structure before assuming frontend component issues
- **Progressive Fallback Strategy**: Implement graceful fallback from detailed API data → basic document data → clear error messages with actionable guidance
- **No Misleading Mock Data**: Never use mock data as fallback - show clear errors when real data can't be retrieved to prevent user misrepresentation and maintain system integrity

### Frontend-Backend Integration Debugging
- **API endpoint verification first**: Always verify API endpoints exist and return expected data structure before debugging frontend logic
- **Response structure mapping**: Frontend components may expect different data structures than backend provides - check actual API response format vs frontend expectations
- **URL pattern matching**: Ensure URL patterns match between frontend calls (`my-notifications`) and backend routes (`my_notifications`) - hyphens vs underscores matter
- **API parameter format validation**: Frontend and backend parameter formats must match exactly - query filters like `?filter=pending_my_action` vs `?pending_my_action=true` can return completely different results leading to incorrect UI state
- **Multiple API call debugging**: When frontend components make multiple API calls (list + detail), ensure both endpoints return consistent data - detail endpoints overwriting good list data is a common integration failure pattern
- **Debug logging strategic placement**: Add detailed debug logging in frontend components to trace data flow between API calls, especially when components switch between different endpoints
- **Content-Disposition header authority**: Frontend should extract filenames from server's `Content-Disposition` header instead of constructing them client-side - server determines correct filename and extension, especially important for ZIP packages vs single files
- **Paginated response handling**: DRF often returns `{count, next, previous, results: [...]}` not direct arrays - use `Array.isArray(data) ? data : (data.results || [])` to handle both formats gracefully

### Performance Optimization Patterns
- **Event-driven over polling**: Replace regular HTTP polling with event-triggered updates plus minimal backup polling (5-minute safety net vs 15-60 second intervals) for 95% server load reduction
- **Infinite loop prevention**: Remove changing values (like `lastRefreshTime`) from useEffect dependencies to prevent continuous re-renders and API calls
- **Server resource management**: Aggressive polling can cause "too many open files" and database connection exhaustion in Docker containers - prioritize event-driven patterns for production scalability

### Search Filter Implementation
- **Backend-frontend filter alignment**: Always verify backend DocumentFilter capabilities before implementing frontend search options - remove unsupported filters (e.g., department) to prevent user confusion
- **API parameter format consistency**: Backend expects repeated parameters for arrays (`status=DRAFT&status=APPROVED`) not nested objects - implement proper array handling in frontend API calls
- **Filter relevance assessment**: Regularly audit search filters - remove 40-60% irrelevant filters and add missing high-value options (title, description, document_number) for better user experience
- **Status filter maintenance**: Keep frontend DocumentStatus types synchronized with backend STATUS_CHOICES - mismatched status values cause 400 API errors

### Development Environment Architecture
- **Container networking over localhost**: Use service names (`backend:8000`) instead of `localhost:8000` for container-to-container communication
- **Development vs production patterns**: Keep both localhost development configs and containerized configs for different use cases
- **Standard Django WSGI**: HTTP-only implementation uses standard Django WSGI deployment - no ASGI complexity needed

### Pragmatic Architecture Decisions
- **80/20 principle in practice**: For multi-format document processing, simple ZIP packages with metadata provide 80% of user value with 20% of complexity compared to format-specific processors
- **Strategic simplicity over feature completeness**: Sometimes the smartest architectural decision is the simplest one that delivers real value - avoid complex solutions when pragmatic approaches solve the actual user need
- **Stop-gap solutions that exceed expectations**: Well-implemented interim solutions (like ZIP packages with professional metadata) can be superior to complex alternatives and become permanent architectural choices

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

## Module Analysis and Assessment Patterns

### Comprehensive Module Evaluation
- **Initial assessment vs reality**: Always verify actual integration points before concluding functionality status - modules may be more deeply integrated than initial API testing suggests
- **Feature discovery methodology**: Test both individual components AND their integration workflows - a module's true value often lies in its integration with other systems rather than standalone functionality
- **Production usage verification**: Check if seemingly "underutilized" features are actually core to business processes (e.g., placeholder processing in document generation pipelines)

### Core Infrastructure Identification
- **Business-critical vs user data distinction**: Distinguish between core system infrastructure (templates, placeholders, configurations) and user-generated content (documents, workflows, user accounts)
- **Architecture protection patterns**: Core infrastructure like document templates and placeholders (32 in this system) should be protected from deletion during system operations - they represent significant configuration work and business logic
- **Infrastructure preservation strategy**: Remove user options to delete core infrastructure - make preservation automatic rather than optional to prevent accidental system damage

### API Endpoint Integration Debugging
- **Endpoint mismatch patterns**: Frontend components using different endpoint paths than backend provides (`/auth/users/` vs `/users/users/`) is a common integration failure point
- **Authentication endpoint alignment**: When API calls fail, verify both authentication AND endpoint path correctness before debugging component logic
- **Service method parameter validation**: Backend API parameter expectations may not match frontend service method implementations - always verify actual API requirements
- **ViewSet lookup_field alignment**: When Django REST Framework ViewSets use UUID but routes still expect 'id', add `lookup_field = 'uuid'` to ViewSet class AND update action method parameters from `pk=None` to `uuid=None` - both changes are required
- **404 to 500 progression**: If fixing 404 errors leads to 500 errors, check that action method signatures match the lookup_field (e.g., `def action(self, request, uuid=None)` not `pk=None`)

### Management Command Debugging
- **Missing dependencies pattern**: Management commands failing due to undefined variables (categories, models) should be debugged by checking all referenced objects exist in scope
- **Field mapping validation**: When ORM operations fail, verify model field names match exactly with what the command attempts to create - use shell inspection to confirm actual model fields
- **Progressive command fixes**: Fix one missing dependency at a time rather than attempting to predict all missing elements

## Cross-Origin Authentication and API Security Patterns

### Frontend-Backend Authentication Issues
- **Cross-origin cookie problems**: Frontend on `localhost:3000` making requests to `localhost:8000` may not properly share authentication cookies
- **CSRF token handling**: Always include CSRF tokens in POST requests: `document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1]`
- **Development authentication fallback**: For development environments, implement graceful fallbacks to admin users when frontend authentication fails
- **Authentication verification approach**: Test auth endpoints (`/api/v1/auth/profile/`) before debugging complex authentication flows

### API Error Handling Patterns
- **401 vs 400 distinction**: 401 Unauthorized often indicates session/authentication issues rather than malformed requests
- **Model field constraints debugging**: When getting field constraint errors, check model definitions for `max_length` restrictions and field requirements
- **Anonymous user detection**: `AnonymousUser` in error messages indicates authentication pipeline issues, not data validation problems

## File Upload and Validation Strategies

### Multi-Stage File Validation
- **Pre-processing validation**: Validate file integrity BEFORE attempting any business logic operations
- **Corruption detection layers**: File size → Archive integrity → Content structure → Sample extraction validation
- **Immediate cleanup strategy**: Remove invalid files immediately after detection to prevent disk bloat
- **User-friendly error mapping**: Convert technical validation errors into actionable user guidance

### Import Resolution and Module Dependencies
- **Import placement strategy**: Place imports at module level rather than inside functions to avoid scope issues
- **Missing import debugging**: When getting `name 'X' is not defined` errors in Django views, check both local and global import statements
- **Function-level imports**: Use sparingly and only when avoiding circular dependencies or lazy loading is required
- **Comprehensive model imports**: When implementing system reset/cleanup operations, import ALL required models at the module level to avoid runtime import errors - missing imports like DocumentType, WorkflowType cause NameError exceptions during cleanup operations

## Scope Creep Prevention and System Analysis Patterns

### Over-Engineering Detection and Prevention
- **Progressive complexity trap**: When implementing complex features (like database restoration), start with validation of existing working components before adding new logic
- **Systematic analysis approach**: When debugging loops or repeated failures, step back to analyze what's actually working vs. what's failing - often 80% of system works and 20% has scope creep
- **Working foundation identification**: Always identify and preserve working components (backup creation, validation, tracking) before attempting complex enhancements
- **Scope boundary enforcement**: When asked to "complete" functionality, clarify if the working validation/tracking system meets the core requirement before adding restoration complexity

### Comprehensive Module Analysis Pattern
- **Tab-by-tab systematic review**: When analyzing complex modules, examine each tab/section individually for redundancies, missing features, and phasing issues
- **Redundancy identification**: Look for duplicate functionality across different UI sections (e.g., restore dropdown vs table button) - consolidate to single source of truth
- **Incremental implementation phases**: Break large feature additions into phases (Quick Wins → CRUD → Search/Filter) for manageable progress and testing
- **Quick wins first**: Start with simple high-impact changes (removing hardcoded checks, eliminating duplicates) before tackling complex CRUD operations
- **Document as you go**: Create comprehensive analysis documents with line numbers, recommendations, and impact metrics to guide implementation

### Database Integrity vs Business Requirements
- **Constraint interpretation**: When database operations "fail" due to FK constraints, first assess if the constraint is protecting critical data integrity rather than assuming it needs to be bypassed
- **Architectural success redefinition**: System operations that preserve critical infrastructure while achieving core business goals (data cleanup) should be considered successful, even if not achieving 100% deletion targets
- **Protected relationship respect**: Django's protected foreign keys often represent intentional business logic (audit trails, ownership tracking) - work with these constraints rather than against them

### Database Constraint and Foreign Key Patterns
- **Related object save sequence**: When creating objects with foreign key relationships, always save the parent object before creating dependent objects to avoid "unsaved related object" errors
- **Required field discovery**: When getting constraint violations, check model definitions for required fields that may not be obvious (configuration_id, triggered_by, etc.)
- **Auto-configuration strategy**: For complex models requiring configurations, implement get_or_create patterns to auto-generate required configurations rather than requiring manual setup

### API Method Signature Verification
- **Parameter name validation**: Always check actual method signatures before implementing calls - parameter names like `details` vs `additional_data` can cause runtime failures
- **Service inspection pattern**: Use `inspect.signature()` and `dir()` to verify available methods and parameters before implementation
- **Consistent parameter mapping**: When methods expect specific parameter formats, create helper functions to ensure consistent parameter transformation

## Backup & Restore System Patterns

### Natural Key Resolution for Data Portability
- **Critical insight**: When implementing backup/restore systems, missing natural key handlers cause silent FK resolution failures - the object creates with None instead of the resolved reference
- **Diagnostic pattern**: When restored objects count as "created" but don't show up or have missing relationships, check if natural key handlers exist for ALL models with FKs
- **Complete handler coverage**: For each model with FK fields, verify there's a corresponding `_resolve_<modelname>_natural_key()` handler - missing even one (like Document) breaks the entire chain
- **Testing strategy**: Always test FK resolution explicitly in isolation before running full restoration - it's easier to debug `None` returns in unit tests than in complex restoration flows

### Timestamp Preservation in ORM Operations
- **Django auto_now issue**: `auto_now=True` and `auto_now_add=True` fields ALWAYS override provided values during `.create()` - this causes historical timestamps to be lost during restoration
- **Solution pattern**: Temporarily disable these flags before object creation: `field.auto_now = False`, create object, then re-enable: `field.auto_now = True`
- **Scope correctly**: Use try/finally blocks to ensure flags are always re-enabled, even if creation fails - prevents corrupting normal operation
- **Apply to all creation paths**: Don't forget fallback/progressive creation paths - they need the same timestamp preservation logic

### Debugging Complex Restoration Failures
- **Start with isolation**: When complete restoration shows "0 objects restored", test individual record restoration in isolation first - it's faster to debug one object than a full migration package
- **Check actual data flow**: Use manual FK resolution tests to verify each natural key resolves correctly before assuming the restoration logic is wrong
- **Transaction boundaries matter**: Understand where transaction.atomic() blocks are - objects may be created successfully but rolled back if anything fails later in the same transaction
- **Count vs. existence verification**: Just because an object returns from .create() doesn't mean it's in the database - always verify with a fresh query after transaction completes

### API Preprocessing Conflicts
- **Avoid dual processing**: When using specialized processors (like EnhancedRestoreProcessor), don't add preprocessing in the API layer that modifies the data format
- **Natural key integrity**: If backup data has natural keys (arrays), don't convert them to IDs before passing to a processor that expects natural keys - this corrupts the data
- **Simple pass-through**: The best API design for complex operations is often the simplest - extract package, pass raw data to processor, return results
- **Processor responsibility**: Let the processor handle ALL data transformation - that's its job, and it has the context to do it correctly

## State Variable Cleanup Safety

### React State Removal Pattern
When removing unused React state variables during cleanup, a common mistake is removing the state declaration but forgetting setter calls throughout the component.

**Problem Pattern** (repeated 3 times in one session):
```typescript
// Remove this:
const [loading, setLoading] = useState(false);

// But forget to remove ALL of these:
setLoading(true);  // Line 85
setLoading(false); // Line 177
setLoading(false); // Line 434
// ... 5 more calls scattered throughout
```

**Result**: Runtime error "setLoading is not defined" crashes the component

**Solution Pattern**:
1. Before removing state, grep for ALL references: `grep -n "setStateVariable" Component.tsx`
2. Remove or refactor ALL setter calls first
3. Then remove state declaration
4. Verify no references remain

**Safety Check**: `grep -c "setVariableName" file.tsx` should return 0 after cleanup

## Frontend-Backend API Contract Verification

### API Response Format Mismatches
When backend API response format is updated, frontend components may still expect the old format, causing "data exists but doesn't display" issues.

**Symptom**: Backend returns valid data, frontend shows "0 items" or empty state

**Example from session**:
- Backend returns: `{ isValid: true, identifiedPlaceholders: [...], totalPatternsFound: 6 }`
- Frontend expects: `{ is_valid: true, placeholders_found: [...] }`
- Result: Shows "0 patterns • 0 issues" despite 6 valid placeholders

**Root Cause**: 
- Backend API was enhanced with new field names (camelCase)
- Frontend still mapped old field names (snake_case)
- No TypeScript interface to catch mismatch

**Prevention**:
1. **Define shared TypeScript interfaces** for API responses
2. **Verify frontend mapping** when changing backend response format
3. **Test API integration** after backend changes, not just unit tests
4. **Use consistent naming** (pick camelCase or snake_case, not mixed)

**Quick Check**: After updating API response format, search frontend for old field names

## Regex Pattern Exclusivity for Validators

### Overlapping Pattern Detection
When validating multiple formats (correct and incorrect), regex patterns can accidentally match each other, causing false positives.

**Problem Example**:
```python
patterns = [
    r'\{\{([A-Z_]+)\}\}',  # Standard {{PLACEHOLDER}}
    r'\{([A-Z_]+)\}',       # Single braces {PLACEHOLDER}
]
```

**Issue**: Pattern 2 matches the opening `{` in `{{PLACEHOLDER}}` from Pattern 1, flagging valid placeholders as errors

**Result**: 6 valid placeholders + 18 false positive "errors"

**Solution**: Use negative lookahead/lookbehind for mutual exclusivity
```python
patterns = [
    r'\{\{([A-Z_]+)\}\}',              # Standard (check first)
    r'(?<!\{)\{([A-Z_]+)\}(?!\})',     # Single braces (exclude if surrounded)
]
```

**Pattern Order Matters**: Always check the "correct" format first, then exclude it from "incorrect" patterns

**Verification**: Test with known valid input - should show 0 errors, not false positives

## Database Constraint Fixing Pattern

### Check All Related Tables When Fixing Constraints
When encountering database constraints (like NOT NULL violations), don't fix them one at a time. Check all related tables that might have the same pattern.

**Example from Session:**
- Fixed `document_access_logs.session_id` to allow NULL
- Later encountered same issue in `audit_trail.session_id`
- Could have been fixed together if checked comprehensively

**Better Approach:**
```bash
# Search for all similar patterns
grep -r "session_id.*CharField" backend/apps/*/models.py
# Fix all occurrences in one pass
```

**Why:** Database constraint errors often repeat across similar tables (audit logs, history tables, etc.). Fixing comprehensively saves multiple deploy cycles.

---

## Deployment Script Verification Pattern

### Always Verify Script Results, Not Assumptions
Deployment scripts may encounter existing data and behave differently than expected. Always verify what actually happened.

**Issue from Session:**
- Script checked if users existed
- If they existed, skipped creation
- But didn't verify/fix their role assignments
- Result: Users had wrong roles despite "successful" deployment

**Solution Pattern:**
```python
# Don't just check existence
if not User.objects.filter(username='user01').exists():
    create_user()
    assign_roles()

# ALSO verify configuration
else:
    user = User.objects.get(username='user01')
    verify_and_fix_roles(user)  # Add this!
```

**Why:** Scripts often handle "fresh install" differently than "existing data" scenarios. Test both paths.

---

## Permission Debugging Chain

### Follow Permission Chain Completely
When debugging permission errors, check the entire chain, not just one level.

**Complete Permission Chain:**
1. User exists?
2. UserRole relationship exists?
3. UserRole.is_active = True?
4. Role has correct module code?
5. Role has correct permission_level?
6. Permission check uses correct field names?

**Example from Session:**
- User had role assigned
- Role existed
- But role had wrong `permission_level` value
- Had to check 5 levels deep to find root cause

**Pattern:** Create a diagnostic script that checks ALL levels at once, not step-by-step.

---

## Deployment Method Selection

### Hot Restart vs Full Rebuild Decision Tree
Choose deployment method based on what changed:

**Hot Restart (2 minutes, no downtime)**:
- ✅ Python code changes only
- ✅ JavaScript/TypeScript changes only
- ✅ Configuration file changes (settings.py)
- ❌ Dockerfile changes
- ❌ requirements.txt changes
- ❌ System package additions

**Full Rebuild (5 minutes, 2-3 min downtime)**:
- ✅ Dockerfile modifications
- ✅ New system dependencies (LibreOffice, etc.)
- ✅ New Python packages in requirements.txt
- ✅ Major infrastructure changes
- ✅ When troubleshooting mysterious issues

**Command Reference**:
```bash
# Hot restart (fast)
docker compose restart backend frontend

# Full rebuild (thorough)
docker compose down
docker compose build backend frontend
docker compose up -d
```

**Lesson from session**: Full rebuild chosen for code-only changes; hot restart would have been sufficient and 3 minutes faster

## React Environment Variables and Docker Build Process

### Build-Time vs Runtime Environment Variables
React environment variables (`REACT_APP_*`) must be available at **build time**, not runtime, as they get baked into the JavaScript bundle during `npm run build`.

**Problem Pattern**: Setting `REACT_APP_API_URL` in `docker-compose.yml` environment without corresponding Dockerfile ARG/ENV declarations causes the build to use fallback values.

**Solution Pattern**:
```dockerfile
# Dockerfile - Accept as build argument
ARG REACT_APP_API_URL=/api/v1
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
RUN npm run build  # Now uses the correct value
```

```yaml
# docker-compose.yml - Pass as build argument
frontend:
  build:
    args:
      REACT_APP_API_URL: /api/v1  # Build-time
  environment:
    - REACT_APP_API_URL=/api/v1   # Runtime reference only
```

**Symptom**: Frontend rebuilt multiple times but still calling hardcoded URLs (e.g., `localhost:8000`) despite environment variable being set.

**Root Cause**: React bundler uses environment variables at build time. If ARG not declared in Dockerfile, the variable isn't available during `npm run build`, so code falls back to hardcoded defaults.

**Verification**: Check running container has correct env (`docker compose exec frontend env`) but JavaScript bundle still has old value - indicates build-time issue, not runtime.

**Critical**: After fixing Dockerfile, must rebuild with `--no-cache` and users must clear browser cache or use incognito mode to load new JavaScript bundle.

## HAProxy Health Check Configuration

### Health Check Path Requirements
**Issue Pattern**: HAProxy backend showing as DOWN despite service being healthy, causing 503 errors for all requests routed through HAProxy.

**Root Cause**: Django URLs often require trailing slashes. Health check using `/health` fails while `/health/` succeeds.

**Example**:
```haproxy
# Wrong - fails health check
option httpchk GET /health HTTP/1.1\r\nHost:\ localhost

# Correct - passes health check
option httpchk GET /health/ HTTP/1.1\r\nHost:\ localhost
```

**Diagnostic Pattern**: 
- Service responds to direct curl: `curl http://localhost:8001/health/` → 200 OK
- HAProxy shows backend DOWN in stats page
- All requests through HAProxy return 503
- Check HAProxy health check configuration for missing trailing slash

**Prevention**: Always test the exact health check path that HAProxy uses against the actual service before deploying.

## Docker Container vs Service Health Checks

### Service-Specific Health Check Patterns
**Issue**: Using same health check for all containers in a multi-service docker-compose setup causes false "unhealthy" status for services that don't run web servers.

**Example Problem**:
```dockerfile
# Dockerfile with HTTP health check
HEALTHCHECK CMD curl -f http://localhost:8000/health/ || exit 1
```

This works for Django backend but fails for Celery worker/beat (no web server).

**Solution Pattern**:
```yaml
# docker-compose.yml - Override per service
celery_worker:
  healthcheck:
    test: ["CMD-SHELL", "celery -A edms inspect ping"]

celery_beat:
  healthcheck:
    disable: true  # Beat doesn't respond to ping
```

**Key Insight**: Docker health check status ("unhealthy") ≠ Service functionality. Celery Beat can be actively scheduling tasks while showing "unhealthy" because it doesn't respond to ping commands by design.

**Diagnostic Approach**: When health checks fail, verify actual functionality (check logs, test operations) before assuming service is broken.

## Deployment Port Conflicts and Service Coordination

### HAProxy and Container Port Binding Conflicts
**Issue Pattern**: HAProxy fails to start with "Address already in use" on port 80 when Docker containers are already running.

**Root Cause**: Standalone nginx container or other service binding to port 80 before HAProxy starts.

**Solution Sequence**:
1. Stop Docker services first: `docker compose down`
2. Start HAProxy: `systemctl start haproxy`
3. Start Docker services (internal ports only): `docker compose up -d`

**Architecture Understanding**:
```
User → HAProxy (host port 80)
         ↓
         ├─ Frontend Container (internal: 3001 → maps to host: 3001)
         └─ Backend Container (internal: 8001 → maps to host: 8001)
```

HAProxy on **host** connects to **host** ports (127.0.0.1:3001, 127.0.0.1:8001), not container internal ports.

**Prevention**: When using HAProxy, don't expose container port 80 to host. Frontend container can run internal nginx on port 80, mapped to host port 3001, and HAProxy routes to that.

## Management Command Deployment in Docker

### New Management Commands Require Image Rebuild
**Issue Pattern**: Added new Django management commands (e.g., `create_default_roles.py`) to repository, pulled code on server, but commands show as "Unknown command" when run.

**Root Cause**: Django management commands are part of the Python codebase. Just pulling code updates files on host, but Docker container runs from an **image** (snapshot). The running container still has old code.

**Solution**:
```bash
# Must rebuild Docker image, not just restart
docker compose build backend
docker compose up -d backend
```

**Symptom**: `git pull` succeeded, file exists on host at `backend/apps/users/management/commands/create_default_roles.py`, but `python manage.py create_default_roles` returns "Unknown command".

**Prevention**: After adding new Python files (models, views, management commands), always rebuild the Docker image. Code changes to existing files can hot-reload, but new files require image rebuild.

**Efficient Pattern**: Create a rebuild script that stops service → rebuilds image → restarts service → waits for health check.

## Backend API Multiple View Files Pattern

### Always Check Which View File Is Actually Being Called

**Problem Pattern**: When multiple view files exist with similar names (e.g., `dashboard_api_views.py` and `dashboard_stats.py`), you may edit the wrong file and wonder why changes don't take effect.

**Example from session**:
- Edited `dashboard_api_views.py` extensively, added stat_cards logic
- Backend kept returning old data structure
- Added debug logging - nothing appeared in logs
- Spent 18 iterations debugging before discovering URL routing used `dashboard_stats.py` instead

**Root Cause**: URL configuration pointed to a different view file than expected.

**Solution**:
```bash
# 1. First check which view is actually being called
grep -r "dashboard/stats" backend/edms/urls.py backend/apps/api/urls.py

# 2. Check URL patterns to find actual view
python manage.py show_urls | grep dashboard
# OR
from django.urls import get_resolver
# Inspect actual routing

# 3. Then edit the CORRECT file
```

**Prevention**: Before editing views for an API endpoint, always verify which file the URL routing actually calls. Don't assume based on file names.

## Backend Filter Logic and Frontend Display

### Verify Backend API Returns Data Before Debugging Frontend

**Problem Pattern**: Frontend not displaying data → immediately debug frontend code → turns out backend filtered the data out.

**Example from session**:
- Frontend document list not showing POL-2026-0001 v1.0 (SUPERSEDED)
- Family grouping code was correct
- Issue: Backend `library` filter only returned latest version, filtered out SUPERSEDED
- Also: Default query excluded SUPERSEDED status from allowed statuses

**Debugging Steps**:
1. Check browser network tab - is API returning the data?
2. Check backend filter logic for that endpoint
3. Check backend queryset for status exclusions
4. THEN debug frontend display logic

**Prevention**: When frontend doesn't display expected data, check backend API response FIRST before debugging frontend components. Use browser DevTools Network tab or `curl` to inspect actual API responses.

## Docker Container Rebuild Pattern

### Python Code Changes Require Image Rebuild, Not Just Restart

**Critical Pattern:** When modifying Python code in Docker containers, the container must be REBUILT to load the new code, not just restarted.

**Problem Pattern:**
```bash
# ❌ WRONG - Won't load new Python code
git pull origin develop
docker compose restart backend

# Container restarts but runs OLD code from existing image
```

**Correct Pattern:**
```bash
# ✅ CORRECT - Rebuilds image with new code
git pull origin develop
docker compose stop backend
docker compose build backend  # Creates new image from updated code on disk
docker compose up -d backend
```

**Why This Happens:**
- Docker containers run from **images** (snapshots), not live code on disk
- `git pull` updates files on disk
- But containers continue using the old image until rebuilt
- Even if code is on disk, container needs new image

**Timeline Understanding:**
```
Disk (has new code) → Build → Image (snapshot) → Container (runs from image)
```

After code changes:
```
Disk (✅ new) → No rebuild → Image (❌ old) → Container (❌ runs old code)
```

After rebuild:
```
Disk (✅ new) → Build → Image (✅ new) → Container (✅ runs new code)
```

**Symptoms of Running Old Code:**
- Changes committed and pushed to GitHub
- Code pulled to server successfully
- `grep` shows new code in files on disk
- But application behavior doesn't change
- Tests pass locally but fail on server
- Import errors for newly added modules (e.g., `ModuleNotFoundError: No module named 'pytz'`)

**Verification:**
```bash
# Check if code is on disk (should show new code)
grep "new_feature" backend/apps/myapp/file.py

# Check if container has new code (may show old code)
docker compose exec backend grep "new_feature" /app/apps/myapp/file.py

# If these differ, image needs rebuild
```

**Exception - When Restart is Sufficient:**
- Configuration file changes (if not baked into image)
- Environment variable changes
- Django settings changes (if code itself didn't change)
- Static file changes (if volume-mounted)

**Build Caching Issues:**
Docker may use cached layers even with `build`:
```bash
# Force complete rebuild
docker compose build --no-cache backend
```

**Related Issue - Frontend Container Networking:**
When backend is rebuilt, it gets a new IP address. Frontend may cache old IP:
```bash
# Fix: Restart frontend to refresh backend hostname resolution
docker compose restart frontend
```

## Timezone Implementation Strategy

### pytz Dependency for Timezone Conversion

When implementing dual timezone display (UTC + local time), add `pytz` to requirements:

```python
# requirements/base.txt
pytz==2024.1  # Required for timezone conversion to display local time
```

**Without pytz:**
- Code compiles successfully
- Imports don't fail at startup
- But crashes at runtime when timezone conversion is attempted
- Results in 500 errors when feature is used

**Symptom:**
```python
import pytz  # No error at import time
display_tz = pytz.timezone('Asia/Singapore')  # Crashes here if pytz not installed
```

### Display Timezone Implementation

**Settings Configuration:**
```python
# settings/base.py
TIME_ZONE = 'UTC'  # Storage timezone (always UTC for database)
DISPLAY_TIMEZONE = 'Asia/Singapore'  # User-facing display timezone
USE_TZ = True  # Enable timezone-aware datetimes
```

**Code Pattern:**
```python
from django.utils import timezone
from django.conf import settings
import pytz

now_utc = timezone.now()
display_tz = pytz.timezone(getattr(settings, 'DISPLAY_TIMEZONE', 'Asia/Singapore'))
now_local = now_utc.astimezone(display_tz)

# Explicit timezone name (not strftime('%Z') which returns '+08')
local_name = 'SGT'  # Singapore Standard Time

result = f"{now_utc.strftime('%H:%M:%S')} UTC ({now_local.strftime('%H:%M:%S')} {local_name})"
# Output: "15:52:33 UTC (23:52:33 SGT)"
```

**Timezone Abbreviation Issue:**
`pytz` returns numeric offset ('+08') not abbreviation ('SGT'):
```python
# ❌ Returns '+08' not 'SGT'
local_name = now_local.strftime('%Z')

# ✅ Explicitly use abbreviation
local_name = 'SGT'  # For Singapore
```

### Date vs DateTime Display Strategy

**Date-only fields (no timezone needed):**
- Fields: CREATED_DATE, EFFECTIVE_DATE, APPROVAL_DATE
- Format: `2026-01-02` or `January 2, 2026`
- Timezone: None shown (dates same in UTC and local time)
- Users understand dates without timezone context

**DateTime fields (dual timezone recommended):**
- Fields: DOWNLOAD_TIME, CURRENT_DATETIME, VERSION_HISTORY generated
- Format: `15:52:33 UTC (23:52:33 SGT)`
- Timezone: Show both UTC and local time
- Critical for audit trails and compliance

**Backend vs Frontend:**
- **Backend (documents):** Show both UTC and local time (permanent record, audit compliance)
- **Frontend (web UI):** Can use browser local time (temporary display, user convenience)
- **API responses:** Always UTC ISO 8601
- **Database storage:** Always UTC

**Scheduler Timezone Handling:**
- Celery tasks should use `CELERY_TIMEZONE = 'UTC'`
- All date comparisons use `timezone.now()` (UTC-aware)
- Do NOT convert scheduler logic to local timezone
- Documents become effective at midnight UTC (8 AM SGT for Singapore)
- This is correct behavior - consistent across timezones

### Common Mistake - Multiple Timestamp Methods

When adding timezone display, check ALL locations that generate timestamps:
- `annotation_processor.py` - `_get_current_timestamp()`
- `docx_processor.py` - `_get_current_timestamp()` (separate copy!)
- `pdf_generator.py` - Inline timestamp generation
- `services.py` - VERSION_HISTORY timestamps
- `zip_processor.py` - Metadata timestamps

**Pattern:** Search for all timestamp generation patterns:
```bash
grep -r "datetime.now()" backend/apps/
grep -r "strftime" backend/apps/ | grep -i "time\|date"
grep -r "Generated:" backend/apps/
```

Each file may have its own timestamp method that needs updating.

## Admin Filter Implementation and Business Logic vs Access Control

### Distinguish Business Logic Filters from Access Control Filters
When implementing admin bypass for filters, carefully analyze whether the filter represents **business logic** (what belongs in this view) or **access control** (who can see this data).

**Problem Pattern from session:**
- Implemented admin bypass for "Document Library" filter
- Admin started seeing DRAFT documents in the library
- This was incorrect: Document Library = published documents for EVERYONE

**Root Cause:**
The "Document Library" filter defines what a "library" means (published/approved documents), not who can access it. This is business logic, not access control.

**Solution Pattern:**
```python
# WRONG - Admin bypass applied to business logic filter
elif filter_type == 'library':
    if not is_admin:
        queryset = queryset.filter(status__in=['EFFECTIVE', ...])
    # Admin sees ALL documents (breaks library concept)

# CORRECT - Business logic filter applies to everyone
elif filter_type == 'library':
    # Library = published documents for EVERYONE (admin AND users)
    queryset = queryset.filter(status__in=['EFFECTIVE', ...])
```

**Decision Framework:**

**Apply Admin Bypass When:**
- Filter controls **who sees what** (access control)
- Purpose: Monitoring, oversight, system management
- Example: "My Tasks" → Admin sees ALL users' tasks

**Do NOT Apply Admin Bypass When:**
- Filter defines **what the view represents** (business logic)
- Purpose: Consistent view for all users
- Example: "Document Library" → Published docs for everyone

**Analysis Questions:**
1. Does this filter define the **meaning** of the view? (business logic)
2. Or does it control **access** to data? (access control)
3. Would admin need a **different view** for oversight? (use separate view)
4. Should admin see the **same thing as users** here? (no bypass)

**From this session:**
- ✅ "My Tasks" filter: Access control → Admin bypass appropriate
- ❌ "Document Library" filter: Business logic → Admin bypass inappropriate
- ✅ "Default View" (no filter): Access control → Admin sees ALL documents

**Prevention:**
Before implementing admin bypass, ask: "Does this filter define what this view IS, or does it control who can see it?"

## Frontend Property Mapping for Document Features

### Check API Response Structure Before Implementing Frontend Features
When adding frontend features that depend on backend data (like document ownership indicators), always verify the exact property names returned by the API first.

**Problem Pattern from session:**
- Assumed API returns `author_id` for document author
- Implemented `isMyDocument()` using `document.author_id`
- Had to correct to `document.author` after checking serializer

**Root Cause:**
Django REST Framework serializers often return related objects by their primary key field name (`author`), not `author_id`.

**Solution Pattern:**
```bash
# FIRST: Check actual API response
docker compose exec backend python manage.py shell -c "
from apps.documents.models import Document
from apps.documents.serializers import DocumentListSerializer
doc = Document.objects.first()
serializer = DocumentListSerializer(doc)
print(serializer.data.keys())  # See actual field names
"

# THEN: Implement frontend with correct field names
```

**Common Django Serializer Patterns:**
- **Foreign Key**: Field name is `author`, not `author_id`
- **Display Fields**: Often includes `author_display`, `author_username`
- **Nested Objects**: May return full object or just ID based on serializer config

**From this session:**
```typescript
// WRONG - Assumed naming
interface Document {
  author_id?: number;  // Doesn't exist in API
}
const isMyDocument = (doc) => user.id === doc.author_id;

// CORRECT - Actual API fields
interface Document {
  author?: number;         // User ID
  author_display?: string; // Display name
  author_username?: string;// Username
}
const isMyDocument = (doc) => user.id === doc.author;
```

**Prevention:**
1. Check serializer field names in backend first
2. Test API response with curl or Django shell
3. Update TypeScript interfaces to match actual API
4. Don't assume field naming conventions

This saves multiple correction iterations and prevents runtime errors.

