# EDMS Backup and Restore API Documentation

## Overview

The EDMS Backup and Restore API provides programmatic access to create migration packages and restore system data. This API supports both CLI and web-based operations with enterprise-grade security.

## Authentication

All backup and restore operations require authentication with staff-level privileges.

### Supported Authentication Methods

1. **JWT Bearer Token** (Recommended)
2. **Django Session Authentication**

### Headers Required

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-CSRFToken: <csrf_token>  # For session auth only
```

## API Endpoints

### 1. Create Migration Package

Creates a complete migration package with all system data.

**Endpoint**: `POST /api/v1/backup/system/create_export_package/`

**Request Example**:
```http
POST /api/v1/backup/system/create_export_package/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "include_users": true,
  "compress": true,
  "encrypt": false
}
```

**Response Example**:
```http
HTTP/1.1 200 OK
Content-Type: application/gzip
Content-Disposition: attachment; filename="edms_migration_package_20251208_142301.tar.gz"
Content-Length: 5242880

<binary package data>
```

**Response Headers**:
- `Content-Type`: `application/gzip`
- `Content-Disposition`: Includes timestamped filename
- `Content-Length`: Package size in bytes

### 2. Restore from Migration Package

Restores system data from an uploaded migration package.

**Endpoint**: `POST /api/v1/backup/system/restore/`

**Request Example**:
```http
POST /api/v1/backup/system/restore/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data

backup_file: <migration_package.tar.gz>
restore_type: full
```

**Response Example**:
```json
{
  "success": true,
  "message": "Restore operation completed successfully",
  "restore_job_id": 123,
  "details": {
    "records_restored": 515,
    "files_restored": 12,
    "users_restored": 8,
    "sequences_reset": 79,
    "verification_passed": true
  },
  "timestamp": "2025-12-08T14:23:01Z"
}
```

### 3. Get Backup Status

Retrieves status of backup/restore operations.

**Endpoint**: `GET /api/v1/backup/jobs/{job_id}/`

**Response Example**:
```json
{
  "job_id": 123,
  "status": "COMPLETED",
  "created_at": "2025-12-08T14:20:00Z",
  "completed_at": "2025-12-08T14:23:01Z",
  "job_type": "restore",
  "details": {
    "total_records": 515,
    "processed_records": 515,
    "errors": 0,
    "warnings": 0
  }
}
```

## Response Codes

### Success Codes
- `200 OK`: Operation completed successfully
- `201 Created`: Backup package created successfully

### Error Codes
- `400 Bad Request`: Invalid request data or malformed package
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient privileges (staff access required)
- `413 Payload Too Large`: Uploaded package exceeds size limit
- `415 Unsupported Media Type`: Invalid package format
- `500 Internal Server Error`: Server-side processing error

### Error Response Format
```json
{
  "error": "Error type",
  "message": "Detailed error description",
  "code": "ERROR_CODE",
  "details": {
    "field": "specific error details"
  }
}
```

## Package Format Specification

### Migration Package Structure
```
migration_package.tar.gz
├── database/
│   ├── database_backup.json         # Django fixture format
│   └── backup_metadata.json         # Backup statistics
├── configuration/
│   ├── environment_variables.env    # Environment configuration
│   └── django_settings/            # Django settings files
├── storage/
│   ├── documents/                  # Document files
│   └── manifest.json              # File inventory
└── metadata.json                   # Package metadata
```

### Database Backup Format (Django Fixture)
```json
[
  {
    "model": "users.user",
    "pk": 1,
    "fields": {
      "username": "admin",
      "email": "admin@example.com",
      "password": "pbkdf2_sha256$600000$...",
      "is_active": true,
      "is_staff": true
    }
  },
  {
    "model": "users.userrole",
    "pk": 1,
    "fields": {
      "user": 1,
      "role": 2,
      "is_active": true,
      "assigned_by": 1
    }
  }
]
```

## Usage Examples

### JavaScript/Frontend Integration

```javascript
// Create migration package
async function createMigrationPackage() {
  const accessToken = localStorage.getItem('accessToken');
  
  const response = await fetch('/api/v1/backup/system/create_export_package/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      include_users: true,
      compress: true
    })
  });

  if (response.ok) {
    const blob = await response.blob();
    const filename = response.headers.get('content-disposition')
      .split('filename=')[1].replace(/"/g, '');
    
    // Trigger download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  }
}

// Restore from package
async function restoreFromPackage(packageFile) {
  const accessToken = localStorage.getItem('accessToken');
  const formData = new FormData();
  formData.append('backup_file', packageFile);
  formData.append('restore_type', 'full');

  const response = await fetch('/api/v1/backup/system/restore/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
    body: formData
  });

  if (response.ok) {
    const result = await response.json();
    console.log('Restore completed:', result);
    return result;
  } else {
    const error = await response.json();
    throw new Error(error.message);
  }
}
```

### Python/CLI Integration

```python
import requests
import os

def create_backup(jwt_token):
    """Create migration package via API."""
    url = 'http://localhost:8000/api/v1/backup/system/create_export_package/'
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'include_users': True,
        'compress': True
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        # Extract filename from Content-Disposition header
        content_disp = response.headers.get('content-disposition', '')
        filename = content_disp.split('filename=')[1].strip('"')
        
        # Save package
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Backup created: {filename} ({len(response.content)} bytes)")
        return filename
    else:
        print(f"Backup failed: {response.status_code} {response.text}")
        return None

def restore_backup(jwt_token, package_path):
    """Restore from migration package via API."""
    url = 'http://localhost:8000/api/v1/backup/system/restore/'
    headers = {
        'Authorization': f'Bearer {jwt_token}'
    }
    
    with open(package_path, 'rb') as f:
        files = {'backup_file': f}
        data = {'restore_type': 'full'}
        
        response = requests.post(url, files=files, data=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Restore completed: {result['details']['records_restored']} records")
        return result
    else:
        print(f"Restore failed: {response.status_code} {response.text}")
        return None
```

### cURL Examples

```bash
# Get JWT token
JWT_TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "test123"}' | \
  jq -r '.access')

# Create migration package
curl -X POST http://localhost:8000/api/v1/backup/system/create_export_package/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"include_users": true, "compress": true}' \
  --output migration_package.tar.gz

# Restore from package
curl -X POST http://localhost:8000/api/v1/backup/system/restore/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "backup_file=@migration_package.tar.gz" \
  -F "restore_type=full"
```

## Security Considerations

### Access Control
- Only staff users can access backup/restore APIs
- JWT tokens expire after 8 hours
- All operations are logged for audit purposes

### Data Protection
- Migration packages contain sensitive data (passwords, keys)
- Packages should be stored securely and encrypted at rest
- Transfer should use HTTPS in production

### Rate Limiting
- Backup creation: Maximum 1 request per 5 minutes per user
- Restore operations: Maximum 1 active restore per system
- Large package uploads have extended timeout limits

## Performance Characteristics

### Backup Creation
- **Time**: 20-60 seconds depending on data size
- **CPU Usage**: Moderate during compression
- **Memory Usage**: ~100MB for package creation
- **Disk Space**: Temporary space equal to package size

### Restore Process
- **Time**: 30-90 seconds depending on data size
- **CPU Usage**: High during database loading
- **Memory Usage**: ~200MB during restoration
- **Database Load**: Heavy during Django loaddata

### Package Sizes
- **Small System** (< 100 users): 2-5MB
- **Medium System** (100-1000 users): 5-20MB
- **Large System** (1000+ users): 20MB+

## Monitoring and Alerting

### Success Metrics
- Package creation success rate
- Average package size
- Restore success rate
- Performance benchmarks

### Error Monitoring
- Authentication failures
- Package corruption errors
- Restore failures
- Timeout issues

### Recommended Alerts
- Backup creation failures
- Large package size increases
- Restore operation failures
- API authentication issues

---

This API provides robust, secure access to EDMS backup and restore functionality suitable for production environments and automated disaster recovery systems.