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

## Workflow Integration Patterns

### Notification System Architecture
- **Multi-layer integration required**: Notifications alone are insufficient - must create corresponding WorkflowTask objects for complete user experience
- **API response field alignment**: Frontend components often expect specific field names (e.g., `reviewer_username` vs `reviewer`) - add serializer fields to match frontend expectations rather than changing frontend logic
- **Database field validation**: Always verify actual model field names before writing code - assumptions about field names (`status` vs `is_active`, `created_by` vs `initiated_by`) cause runtime errors

### WebSocket vs HTTP Polling Strategy
- **HTTP polling as primary, WebSocket as enhancement**: Build reliable HTTP polling first, then add WebSocket as real-time improvement - this provides graceful degradation
- **Authentication complexity**: WebSocket authentication is more complex than HTTP - implement HTTP endpoints fully before adding WebSocket real-time features
- **User experience consideration**: Show connection status clearly (`🟢 Real-time` vs `🔄 Polling`) so users understand system behavior

### Database Migration and Development Flow
- **Incremental database changes**: Add fields via proper migrations rather than manual SQL to avoid dependency issues
- **Field existence verification**: Use `getattr()` and `hasattr()` when adding new fields to handle cases where migrations haven't run yet
- **Container service dependencies**: When modifying database schema, ensure Django Channels dependencies are properly installed and container is rebuilt

### Frontend-Backend Integration Debugging
- **API endpoint verification first**: Always verify API endpoints exist and return expected data structure before debugging frontend logic
- **Response structure mapping**: Frontend components may expect different data structures than backend provides - check actual API response format vs frontend expectations
- **URL pattern matching**: Ensure URL patterns match between frontend calls (`my-notifications`) and backend routes (`my_notifications`) - hyphens vs underscores matter

### Development Environment Architecture
- **Container networking over localhost**: Use service names (`backend:8000`) instead of `localhost:8000` for container-to-container communication
- **Development vs production patterns**: Keep both localhost development configs and containerized configs for different use cases
- **ASGI server requirements**: WebSocket functionality requires ASGI server (Daphne) instead of standard Django runserver