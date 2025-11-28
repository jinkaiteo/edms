# EDMS API Architecture Documentation - January 2025

## 📋 API Overview

**API Version:** v1  
**Base URL:** `/api/v1/`  
**Authentication:** JWT Bearer tokens  
**Content Type:** `application/json` (forms: `multipart/form-data`)  

---

## 🔐 Authentication & Authorization

### **JWT Authentication**
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### **Authorization Header**
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### **Role-Based Access Control**
| Role | Documents | Workflows | Users | Admin |
|------|-----------|-----------|-------|-------|
| **Author** | Create/Edit Own | Submit for Review | Read Own | ❌ |
| **Reviewer** | Read Assigned | Review Documents | Read Own | ❌ |
| **Approver** | Read Assigned | Approve Documents | Read Own | ❌ |
| **Admin** | Full Access | Full Access | Full Access | ✅ |

---

## 📄 Document Management API

### **Document Endpoints**

#### **List Documents**
```http
GET /api/v1/documents/documents/
```

**Query Parameters:**
- `status` - Filter by document status (DRAFT, EFFECTIVE, etc.)
- `document_type` - Filter by document type ID
- `search` - Full-text search in title/description
- `ordering` - Sort field (document_number, created_at, etc.)
- `limit` - Pagination limit (default: 20)
- `offset` - Pagination offset

**Response:**
```json
{
  "count": 150,
  "next": "/api/v1/documents/documents/?limit=20&offset=20",
  "previous": null,
  "results": [
    {
      "id": 1,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "document_number": "SOP-2025-0001",
      "title": "Quality Control Procedures",
      "status": "APPROVED_AND_EFFECTIVE",
      "version_major": 1,
      "version_minor": 0,
      "version_string": "v1.0",
      "document_type": {
        "id": 1,
        "name": "Standard Operating Procedure",
        "code": "SOP"
      },
      "author": {
        "id": 1,
        "username": "author01",
        "full_name": "John Author"
      },
      "created_at": "2025-01-28T10:00:00Z",
      "effective_date": "2025-01-28",
      "file_url": "/api/v1/documents/documents/550e8400-e29b-41d4-a716-446655440000/download/"
    }
  ]
}
```

#### **Create Document**
```http
POST /api/v1/documents/documents/
Content-Type: multipart/form-data

title=Quality Control Procedures
description=Detailed procedures for QC testing
document_type=1
document_source=1
priority=normal
requires_training=false
is_controlled=true
keywords=quality,control,testing
file=@document.pdf
dependencies[0]=123
dependencies[1]=456
```

**Response:**
```json
{
  "id": 1,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "document_number": "SOP-2025-0001",
  "title": "Quality Control Procedures",
  "status": "DRAFT",
  "version_major": 1,
  "version_minor": 0,
  "author": {
    "id": 1,
    "username": "author01",
    "full_name": "John Author"
  },
  "created_at": "2025-01-28T10:00:00Z"
}
```

#### **Get Document Details**
```http
GET /api/v1/documents/documents/{uuid}/
```

**Response:**
```json
{
  "id": 1,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "document_number": "SOP-2025-0001",
  "title": "Quality Control Procedures",
  "description": "Detailed procedures for QC testing",
  "status": "APPROVED_AND_EFFECTIVE",
  "version_major": 1,
  "version_minor": 0,
  "version_string": "v1.0",
  "document_type": {
    "id": 1,
    "name": "Standard Operating Procedure",
    "code": "SOP"
  },
  "document_source": {
    "id": 1,
    "name": "Original Digital Draft"
  },
  "author": {
    "id": 1,
    "username": "author01",
    "full_name": "John Author"
  },
  "reviewer": {
    "id": 2,
    "username": "reviewer01",
    "full_name": "Jane Reviewer"
  },
  "approver": {
    "id": 3,
    "username": "approver01", 
    "full_name": "Bob Approver"
  },
  "priority": "normal",
  "requires_training": false,
  "is_controlled": true,
  "keywords": "quality,control,testing",
  "created_at": "2025-01-28T10:00:00Z",
  "updated_at": "2025-01-28T10:00:00Z",
  "effective_date": "2025-01-28",
  "file_url": "/api/v1/documents/documents/550e8400-e29b-41d4-a716-446655440000/download/"
}
```

#### **Download Document**
```http
GET /api/v1/documents/documents/{uuid}/download/
```

**Response:**
- Content-Type: application/pdf (or original file type)
- Content-Disposition: attachment; filename="SOP-2025-0001.pdf"
- Binary file content

#### **Get Document Dependencies**
```http
GET /api/v1/documents/documents/{uuid}/dependencies/
```

**Response:**
```json
{
  "dependencies": [
    {
      "id": 1,
      "depends_on": {
        "id": 123,
        "document_number": "FORM-2025-0001",
        "title": "Quality Control Form"
      },
      "dependency_type": "REFERENCE",
      "is_critical": true,
      "description": "Required form for QC procedures"
    }
  ],
  "dependents": [
    {
      "id": 2,
      "document": {
        "id": 456,
        "document_number": "WI-2025-0001", 
        "title": "QC Work Instructions"
      },
      "dependency_type": "REFERENCE",
      "is_critical": true
    }
  ]
}
```

---

## 🔄 Workflow Management API

### **Workflow Endpoints**

#### **Execute Workflow Action**
```http
POST /api/v1/workflows/documents/{uuid}/
Content-Type: application/json

{
  "action": "submit_for_review",
  "comment": "Ready for review",
  "assignee": 2
}
```

### **Workflow Actions**

#### **1. Submit for Review**
```json
{
  "action": "submit_for_review",
  "comment": "Document ready for review",
  "reviewer_id": 2
}
```

#### **2. Complete Review**
```json
{
  "action": "complete_review", 
  "comment": "Review completed successfully",
  "approved": true
}
```

#### **3. Route for Approval**
```json
{
  "action": "route_for_approval",
  "comment": "Ready for final approval",
  "approver_id": 3
}
```

#### **4. Approve Document**
```json
{
  "action": "approve_document",
  "comment": "Approved for implementation",
  "effective_date": "2025-02-01"
}
```

#### **5. Create New Version**
```json
{
  "action": "start_version_workflow",
  "major_increment": false,
  "reason_for_change": "Updated procedures",
  "change_summary": "Added new quality checks",
  "title": "Quality Control Procedures v1.1"
}
```

#### **6. Direct Obsolescence (Approvers/Admins Only)**
```json
{
  "action": "obsolete_document_directly",
  "reason": "Superseded by new procedures",
  "obsolescence_date": "2025-12-31"
}
```

#### **7. Terminate Workflow**
```json
{
  "action": "terminate_workflow",
  "comment": "Workflow cancelled due to requirements change"
}
```

### **Workflow Response Format**
```json
{
  "success": true,
  "message": "Document submitted for review successfully",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "new_status": "PENDING_REVIEW",
  "next_assignee": {
    "id": 2,
    "username": "reviewer01",
    "full_name": "Jane Reviewer"
  },
  "available_actions": [
    "start_review",
    "terminate_workflow"
  ]
}
```

---

## 👥 User Management API

### **User Endpoints**

#### **List Users**
```http
GET /api/v1/users/users/
```

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "username": "author01",
      "first_name": "John",
      "last_name": "Author", 
      "email": "john.author@company.com",
      "is_active": true,
      "is_staff": false,
      "groups": [
        {
          "id": 1,
          "name": "Document Authors"
        }
      ],
      "user_permissions": []
    }
  ]
}
```

#### **Get Current User**
```http
GET /api/v1/users/me/
```

**Response:**
```json
{
  "id": 1,
  "username": "author01",
  "first_name": "John",
  "last_name": "Author",
  "email": "john.author@company.com",
  "is_active": true,
  "is_staff": false,
  "permissions": {
    "can_create_documents": true,
    "can_review_documents": false,
    "can_approve_documents": false,
    "is_admin": false
  }
}
```

---

## 📊 System Information API

### **Document Types**
```http
GET /api/v1/documents/types/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Standard Operating Procedure",
    "code": "SOP",
    "numbering_prefix": "SOP",
    "description": "Standard Operating Procedures"
  },
  {
    "id": 2,
    "name": "Work Instruction",
    "code": "WI", 
    "numbering_prefix": "WI",
    "description": "Detailed Work Instructions"
  }
]
```

### **Document Sources**
```http
GET /api/v1/documents/sources/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Original Digital Draft",
    "source_type": "DIGITAL"
  },
  {
    "id": 2,
    "name": "Scanned Original",
    "source_type": "SCANNED"
  }
]
```

---

## ⚠️ Error Handling

### **Standard Error Response Format**
```json
{
  "error": "Validation failed",
  "details": {
    "field_name": ["This field is required"],
    "another_field": ["Invalid value provided"]
  },
  "code": "VALIDATION_ERROR"
}
```

### **HTTP Status Codes**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (business logic violation)
- `500` - Internal Server Error

### **Common Error Scenarios**

#### **Authentication Errors**
```json
{
  "error": "Authentication credentials were not provided.",
  "code": "AUTHENTICATION_REQUIRED"
}
```

#### **Authorization Errors**
```json
{
  "error": "You do not have permission to perform this action.",
  "code": "PERMISSION_DENIED"
}
```

#### **Validation Errors**
```json
{
  "error": "Validation failed",
  "details": {
    "title": ["This field is required"],
    "document_type": ["Invalid choice"]
  },
  "code": "VALIDATION_ERROR"
}
```

#### **Business Logic Errors**
```json
{
  "error": "Cannot obsolete document while newer versions are in development. Complete or terminate these workflows first: SOP-2025-0001-v2.0 (v2.0) - PENDING_REVIEW",
  "code": "BUSINESS_LOGIC_VIOLATION"
}
```

---

## 🔗 API Integration Examples

### **JavaScript/Frontend Integration**
```javascript
// API Service Class
class EDMSApiService {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'API request failed');
    }

    return response.json();
  }

  // Document operations
  async getDocuments(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/documents/documents/?${query}`);
  }

  async createDocument(formData) {
    return this.request('/documents/documents/', {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set Content-Type for FormData
    });
  }

  // Workflow operations
  async executeWorkflowAction(documentUuid, actionData) {
    return this.request(`/workflows/documents/${documentUuid}/`, {
      method: 'POST',
      body: JSON.stringify(actionData)
    });
  }
}
```

### **Python Integration Example**
```python
import requests
import json

class EDMSClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.session = requests.Session()
        self.authenticate(username, password)
    
    def authenticate(self, username, password):
        """Get JWT token"""
        auth_data = {"username": username, "password": password}
        response = self.session.post(
            f"{self.base_url}/auth/token/", 
            json=auth_data
        )
        response.raise_for_status()
        
        tokens = response.json()
        self.session.headers.update({
            'Authorization': f'Bearer {tokens["access"]}'
        })
    
    def get_documents(self, **params):
        """List documents with optional filters"""
        response = self.session.get(
            f"{self.base_url}/documents/documents/", 
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def create_document(self, title, description, document_type, file_path, **kwargs):
        """Create new document"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'title': title,
                'description': description, 
                'document_type': document_type,
                **kwargs
            }
            response = self.session.post(
                f"{self.base_url}/documents/documents/",
                data=data,
                files=files
            )
        response.raise_for_status()
        return response.json()
    
    def submit_for_review(self, document_uuid, reviewer_id, comment=""):
        """Submit document for review"""
        action_data = {
            "action": "submit_for_review",
            "reviewer_id": reviewer_id,
            "comment": comment
        }
        response = self.session.post(
            f"{self.base_url}/workflows/documents/{document_uuid}/",
            json=action_data
        )
        response.raise_for_status()
        return response.json()
```

---

## 📈 Rate Limiting & Performance

### **Rate Limits**
- **General API**: 1000 requests/hour per user
- **File Upload**: 50 uploads/hour per user  
- **Authentication**: 20 login attempts/hour per IP

### **Pagination**
- **Default page size**: 20 items
- **Maximum page size**: 100 items
- **Pagination format**: Offset-based with next/previous links

### **Caching**
- **Document metadata**: 5 minutes
- **User permissions**: 10 minutes
- **System configuration**: 1 hour

---

**🎯 This API provides complete programmatic access to all EDMS functionality while maintaining security, compliance, and performance requirements.**