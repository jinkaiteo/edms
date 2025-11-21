# EDMS API Specifications

## Overview
This document defines the complete REST API specifications for the 21 CFR Part 11 compliant EDMS system, including all endpoints, request/response schemas, authentication, and error handling.

## Base Configuration

```yaml
API_BASE_URL: http://edms.company.com/api/v1
CONTENT_TYPE: application/json
AUTHENTICATION: JWT Bearer Token
API_VERSION: v1
```

## Authentication Endpoints

### User Authentication

#### Login
```http
POST /auth/login/
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response (200)**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "groups": ["string"],
    "permissions": ["string"]
  },
  "expires_in": "integer"
}
```

#### Token Refresh
```http
POST /auth/refresh/
Content-Type: application/json

{
  "refresh_token": "string"
}
```

#### Logout
```http
POST /auth/logout/
Authorization: Bearer {access_token}

{
  "refresh_token": "string"
}
```

## User Management Endpoints (S1)

### Users

#### List Users
```http
GET /users/?page=1&page_size=20&search=string&department=string
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "count": "integer",
  "next": "string|null",
  "previous": "string|null",
  "results": [
    {
      "id": "integer",
      "username": "string",
      "email": "string",
      "first_name": "string",
      "last_name": "string",
      "is_active": "boolean",
      "profile": {
        "department": "string",
        "employee_id": "string",
        "title": "string"
      },
      "groups": ["string"],
      "last_login": "datetime"
    }
  ]
}
```

#### Create User
```http
POST /users/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "password": "string",
  "profile": {
    "department": "string",
    "employee_id": "string",
    "phone": "string",
    "title": "string"
  },
  "groups": ["string"]
}
```

#### Update User
```http
PUT /users/{id}/
PATCH /users/{id}/
Authorization: Bearer {access_token}
```

#### Delete User
```http
DELETE /users/{id}/
Authorization: Bearer {access_token}
```

## Document Management Endpoints (O1)

### Documents

#### List Documents
```http
GET /documents/?page=1&page_size=20&status=string&type=integer&author=integer&search=string
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "count": "integer",
  "next": "string|null",
  "previous": "string|null",
  "results": [
    {
      "id": "uuid",
      "document_number": "string",
      "title": "string",
      "description": "string",
      "version": "string",
      "document_type": {
        "id": "integer",
        "name": "string"
      },
      "document_source": {
        "id": "integer",
        "name": "string"
      },
      "author": {
        "id": "integer",
        "username": "string",
        "first_name": "string",
        "last_name": "string"
      },
      "reviewer": {
        "id": "integer",
        "username": "string",
        "first_name": "string",
        "last_name": "string"
      },
      "approver": {
        "id": "integer",
        "username": "string",
        "first_name": "string",
        "last_name": "string"
      },
      "status": "string",
      "approval_date": "date|null",
      "effective_date": "date|null",
      "created_at": "datetime",
      "updated_at": "datetime",
      "file_info": {
        "file_name": "string",
        "file_size": "integer",
        "mime_type": "string"
      },
      "dependencies": ["uuid"],
      "can_download": "boolean",
      "can_edit": "boolean",
      "can_approve": "boolean"
    }
  ]
}
```

#### Create Document
```http
POST /documents/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

title: string
description: string
document_type_id: integer
document_source_id: integer
dependencies: [uuid] (optional)
metadata: json (optional)
file: file
```

**Response (201)**:
```json
{
  "id": "uuid",
  "document_number": "string",
  "title": "string",
  "status": "DRAFT",
  "created_at": "datetime"
}
```

#### Get Document Details
```http
GET /documents/{id}/
Authorization: Bearer {access_token}
```

#### Update Document
```http
PUT /documents/{id}/
PATCH /documents/{id}/
Authorization: Bearer {access_token}
```

#### Delete Document
```http
DELETE /documents/{id}/
Authorization: Bearer {access_token}
```

### Document Downloads

#### Download Original Document
```http
GET /documents/{id}/download/original/
Authorization: Bearer {access_token}
```

**Response (200)**:
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="document.pdf"
```

#### Download Annotated Document
```http
GET /documents/{id}/download/annotated/
Authorization: Bearer {access_token}
```

#### Download Official PDF
```http
GET /documents/{id}/download/official/
Authorization: Bearer {access_token}
```

### Document Workflow

#### Start Review Workflow
```http
POST /documents/{id}/workflow/start-review/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "reviewer_id": "integer",
  "comments": "string"
}
```

#### Submit for Review
```http
POST /documents/{id}/workflow/submit-review/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "reviewer_id": "integer",
  "comments": "string"
}
```

#### Review Document
```http
POST /documents/{id}/workflow/review/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "action": "approve|reject",
  "comments": "string",
  "approver_id": "integer" (if approved)
}
```

#### Approve Document
```http
POST /documents/{id}/workflow/approve/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "action": "approve|reject",
  "comments": "string",
  "effective_date": "date" (if approved)
}
```

#### Start Up-versioning
```http
POST /documents/{id}/workflow/up-version/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "version_type": "major|minor",
  "reason": "string"
}
```

#### Start Obsolete Workflow
```http
POST /documents/{id}/workflow/obsolete/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "reason": "string",
  "obsolete_date": "date"
}
```

#### Terminate Workflow
```http
POST /documents/{id}/workflow/terminate/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "reason": "string"
}
```

### Document Types and Sources

#### List Document Types
```http
GET /document-types/
Authorization: Bearer {access_token}
```

#### List Document Sources
```http
GET /document-sources/
Authorization: Bearer {access_token}
```

## Audit Trail Endpoints (S2)

### Audit Logs

#### List Audit Entries
```http
GET /audit-trail/?page=1&page_size=50&table_name=string&user=integer&start_date=date&end_date=date
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "integer",
      "table_name": "string",
      "record_id": "string",
      "action": "string",
      "user": {
        "id": "integer",
        "username": "string",
        "first_name": "string",
        "last_name": "string"
      },
      "ip_address": "string",
      "old_values": "object|null",
      "new_values": "object|null",
      "changed_fields": "array",
      "reason": "string|null",
      "created_at": "datetime"
    }
  ]
}
```

#### Get Audit Entry Details
```http
GET /audit-trail/{id}/
Authorization: Bearer {access_token}
```

## Scheduler Endpoints (S3)

### Scheduled Tasks

#### List Tasks
```http
GET /scheduled-tasks/
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "results": [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "task_type": "string",
      "cron_expression": "string",
      "is_active": "boolean",
      "last_run": "datetime|null",
      "last_status": "string|null",
      "next_run": "datetime|null"
    }
  ]
}
```

#### Create Task
```http
POST /scheduled-tasks/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "task_type": "string",
  "cron_expression": "string",
  "is_active": "boolean"
}
```

#### Run Task Manually
```http
POST /scheduled-tasks/{id}/run/
Authorization: Bearer {access_token}
```

#### Task Execution History
```http
GET /scheduled-tasks/{id}/executions/
Authorization: Bearer {access_token}
```

## Backup Management Endpoints (S4)

### Backups

#### List Backups
```http
GET /backups/?backup_type=string
Authorization: Bearer {access_token}
```

#### Create Backup
```http
POST /backups/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "backup_type": "DATABASE|FILES|CONFIGURATION",
  "description": "string"
}
```

#### Download Backup
```http
GET /backups/{id}/download/
Authorization: Bearer {access_token}
```

#### Delete Backup
```http
DELETE /backups/{id}/
Authorization: Bearer {access_token}
```

## Placeholder Management Endpoints (S6)

### Placeholders

#### List Placeholders
```http
GET /placeholders/
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "results": [
    {
      "id": "integer",
      "placeholder_name": "string",
      "display_name": "string",
      "description": "string",
      "metadata_field": "string",
      "format_type": "string",
      "format_pattern": "string|null",
      "is_system": "boolean",
      "is_active": "boolean"
    }
  ]
}
```

#### Create Placeholder
```http
POST /placeholders/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "placeholder_name": "string",
  "display_name": "string",
  "description": "string",
  "metadata_field": "string",
  "format_type": "TEXT|DATE|NUMBER|BOOLEAN",
  "format_pattern": "string"
}
```

#### Update Placeholder
```http
PUT /placeholders/{id}/
Authorization: Bearer {access_token}
```

#### Delete Placeholder
```http
DELETE /placeholders/{id}/
Authorization: Bearer {access_token}
```

## App Settings Endpoints (S7)

### Settings

#### List Settings
```http
GET /settings/?category=string
Authorization: Bearer {access_token}
```

#### Update Setting
```http
PUT /settings/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "value": "string"
}
```

## Search Endpoints

### Global Search
```http
GET /search/?q=string&type=documents|users&page=1&page_size=20
Authorization: Bearer {access_token}
```

### Document Search (Elasticsearch)
```http
POST /documents/search/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "string",
  "filters": {
    "document_type": "integer",
    "status": "string",
    "author": "integer",
    "date_range": {
      "start": "date",
      "end": "date"
    }
  },
  "sort": {
    "field": "string",
    "order": "asc|desc"
  }
}
```

## Health Check Endpoints

### System Health
```http
GET /health/
```

**Response (200)**:
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "datetime",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": "integer"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": "integer"
    },
    "elasticsearch": {
      "status": "healthy",
      "response_time_ms": "integer"
    },
    "file_storage": {
      "status": "healthy",
      "available_space_gb": "float"
    }
  }
}
```

### Detailed Health
```http
GET /health/detailed/
Authorization: Bearer {access_token}
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object|null",
    "timestamp": "datetime",
    "request_id": "string"
  }
}
```

### HTTP Status Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **409**: Conflict
- **422**: Validation Error
- **429**: Rate Limited
- **500**: Internal Server Error
- **503**: Service Unavailable

### Error Codes
- `INVALID_REQUEST`: Malformed request
- `AUTHENTICATION_REQUIRED`: Missing or invalid token
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `VALIDATION_ERROR`: Data validation failed
- `WORKFLOW_ERROR`: Invalid workflow transition
- `FILE_TOO_LARGE`: File exceeds size limit
- `UNSUPPORTED_FILE_TYPE`: File type not allowed
- `RATE_LIMIT_EXCEEDED`: Too many requests

## Rate Limiting

```
Rate Limits:
- Authentication: 5 requests per minute
- Document uploads: 10 requests per minute
- General API: 100 requests per minute
- Search: 20 requests per minute

Headers:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## API Versioning

```
URL Versioning: /api/v1/
Header Versioning: API-Version: v1
Deprecation Notice: Deprecated-API-Version: v1
```

## Security Headers

```
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## Pagination

All list endpoints support pagination:

```
Query Parameters:
- page: Page number (default: 1)
- page_size: Items per page (default: 20, max: 100)

Response Format:
{
  "count": total_items,
  "next": "url_to_next_page",
  "previous": "url_to_previous_page", 
  "results": [...]
}
```

## Filtering and Sorting

```
Filtering:
GET /documents/?status=APPROVED&author=123&created_after=2024-01-01

Sorting:
GET /documents/?ordering=-created_at,title
```

This API specification provides comprehensive endpoint coverage for all EDMS modules while maintaining security, performance, and compliance standards.