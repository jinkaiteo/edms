# 21 CFR Part 11 Compliant EDMS - Requirements, Architecture & Setup Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Detailed Requirements](#detailed-requirements)
3. [System Architecture](#system-architecture)
4. [Technical Specifications](#technical-specifications)
5. [Setup Instructions](#setup-instructions)
6. [Compliance Framework](#compliance-framework)
7. [Security Implementation](#security-implementation)
8. [Development Guidelines](#development-guidelines)

## 1. Project Overview

### 1.1 Purpose
Develop a 21 CFR Part 11 compliant Electronic Document Management System (EDMS) web application that adheres to ALCOA principles using compliant open-source components. The system must be robust, simple to use, and deployed on-premise for regulatory compliance in pharmaceutical and medical device industries.

### 1.2 Regulatory Context
- **21 CFR Part 11**: Electronic Records; Electronic Signatures
- **ALCOA Principles**: Attributable, Legible, Contemporaneous, Original, Accurate
- **On-premise Deployment**: Required for data sovereignty and regulatory compliance

### 1.3 Key Objectives
- Secure document lifecycle management
- Dynamic workflow capabilities
- Comprehensive audit trails
- Electronic signature functionality
- Integration capabilities with enterprise systems

## 2. Detailed Requirements

### 2.1 Functional Requirements

#### 2.1.1 User Management (S1)
- **Role-based Access Control**
  - Document Viewer (read permissions)
  - Document Author (write permissions)
  - Document Reviewer (review permissions)
  - Document Approver (approval permissions)
  - Document Admin (administrative permissions)
- **User Authentication**
  - Entra ID integration
  - Multi-factor authentication support
  - Session management with timeout
  - Password policy enforcement

#### 2.1.2 Document Management (O1)
- **Document Types Support**
  - Policy documents
  - Manuals
  - Procedures
  - Work Instructions (SOPs)
  - Forms and Templates
  - Records
- **Document Sources**
  - Original Digital Draft
  - Scanned Original
  - Scanned Copy
- **Document Operations**
  - Upload with metadata
  - Version control (major.minor)
  - Workflow routing
  - Download (Original, Annotated, Official PDF)
  - Search and filter capabilities

#### 2.1.3 Workflow Management (S5)
- **Review Workflow**
  - Draft → Pending Review → Reviewed → Pending Approval → Approved → Effective
- **Up-versioning Workflow**
  - Version increment with impact analysis
  - Dependency notification
- **Obsolete Workflow**
  - Dependency validation
  - Approval process for obsolescence
- **Dynamic Workflow Modification**
  - On-the-fly workflow changes
  - Workflow templates
  - State transition rules

#### 2.1.4 Audit Trail (S2)
- **Complete Activity Logging**
  - Database changes tracking
  - User actions logging
  - System events monitoring
  - Immutable audit records
- **Compliance Reporting**
  - Audit trail reports
  - User activity summaries
  - System health status

### 2.2 Non-Functional Requirements

#### 2.2.1 Performance
- **Response Times**
  - Page load: < 3 seconds
  - Document upload: < 30 seconds for 100MB files
  - Search results: < 2 seconds
- **Scalability**
  - Support 500+ concurrent users
  - Handle 100,000+ documents
  - 99.9% uptime availability

#### 2.2.2 Security
- **Data Protection**
  - AES-256 encryption at rest
  - TLS 1.3 for data in transit
  - Database encryption
- **Access Control**
  - Role-based permissions
  - Principle of least privilege
  - Regular access reviews

#### 2.2.3 Compliance
- **21 CFR Part 11**
  - Electronic signatures validation
  - Audit trail integrity
  - System validation documentation
- **Data Integrity**
  - Checksums for file integrity
  - Database constraints
  - Input validation

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Load Balancer                         │
│                      (HAProxy/Nginx)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                    Web Tier                                    │
├─────────────────────────┼───────────────────────────────────────┤
│  React Frontend         │        Django Backend               │
│  - Tailwind CSS         │        - Django REST Framework      │
│  - TypeScript           │        - Django-River               │
│  - Redux Toolkit        │        - Celery Workers             │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                   Service Tier                                 │
├─────────────────────────┼───────────────────────────────────────┤
│  Redis Cache            │        Elasticsearch                │
│  - Session Storage      │        - Document Search            │
│  - Task Queue           │        - Full-text Indexing         │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                    Data Tier                                   │
├─────────────────────────┼───────────────────────────────────────┤
│  PostgreSQL 18          │        File Storage                 │
│  - Document Metadata    │        - Original Documents         │
│  - User Data            │        - Signed PDFs                │
│  - Audit Logs           │        - Backup Archives            │
└─────────────────────────┴───────────────────────────────────────┘
```

### 3.2 Container Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Podman Pods                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   Frontend      │ │    Backend      │ │   Task Queue    │   │
│  │   Container     │ │   Container     │ │   Container     │   │
│  │   - Nginx       │ │   - Django      │ │   - Celery      │   │
│  │   - React App   │ │   - Gunicorn    │ │   - Workers     │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   Database      │ │     Cache       │ │     Search      │   │
│  │   Container     │ │   Container     │ │   Container     │   │
│  │   - PostgreSQL  │ │   - Redis       │ │ - Elasticsearch │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Module Architecture

#### Service Modules (Admin Only)
- **S1 - User Management**: Role assignment, user administration
- **S2 - Audit Trail**: Activity logging, compliance reporting
- **S3 - Scheduler**: Time-based tasks, automated workflows
- **S4 - Backup & Health Check**: System monitoring, data protection
- **S5 - Workflow Settings**: Dynamic workflow configuration
- **S6 - Placeholder Management**: Document template management
- **S7 - App Settings**: System configuration, UI customization

#### Operational Modules
- **O1 - EDMS Core**: Document management, workflow processing

## 4. Technical Specifications

### 4.1 Technology Stack

#### Backend Technologies
```yaml
Framework: Django 4.2 LTS
API: Django REST Framework 3.14
Workflow: Django-River 3.4
Task Queue: Celery 5.3
Cache: Redis 7.0
Database: PostgreSQL 18
Search: Elasticsearch 8.11
File Storage: Django-storage
Document Processing:
  - python-docx-template
  - PyPDF2
  - Tesseract OCR
Authentication: Django-allauth + Entra ID
```

#### Frontend Technologies
```yaml
Framework: React 18
Language: TypeScript 5.0
Styling: Tailwind CSS 3.3
State Management: Redux Toolkit
Routing: React Router 6
HTTP Client: Axios
Testing: Jest + React Testing Library
Build Tool: Vite
```

#### Infrastructure
```yaml
OS: Ubuntu 20.04.6 LTS
Containerization: Podman 4.0
Load Balancer: HAProxy/Nginx
SSL/TLS: Let's Encrypt/Custom CA
Monitoring: Prometheus + Grafana
Logging: ELK Stack (Optional)
```

### 4.2 Database Schema

#### Core Tables
```sql
-- Users and Permissions
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254),
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Management
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_number VARCHAR(50) UNIQUE NOT NULL,
    version_major INTEGER DEFAULT 1,
    version_minor INTEGER DEFAULT 0,
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    document_source VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'DRAFT',
    author_id INTEGER REFERENCES auth_user(id),
    reviewer_id INTEGER REFERENCES auth_user(id),
    approver_id INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    effective_date DATE,
    approval_date DATE,
    file_path VARCHAR(500),
    file_checksum VARCHAR(64),
    metadata JSONB
);

-- Document Dependencies
CREATE TABLE document_dependencies (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    depends_on_id UUID REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow States (Django-River)
CREATE TABLE river_state (
    id SERIAL PRIMARY KEY,
    label VARCHAR(200) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL
);

-- Audit Trail
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES auth_user(id),
    action VARCHAR(100) NOT NULL,
    object_type VARCHAR(100),
    object_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    is_system_action BOOLEAN DEFAULT FALSE
);

-- Electronic Signatures
CREATE TABLE electronic_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    signer_id INTEGER REFERENCES auth_user(id),
    signature_hash VARCHAR(512) NOT NULL,
    signing_reason TEXT,
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    certificate_info JSONB,
    is_valid BOOLEAN DEFAULT TRUE
);
```

### 4.3 API Specifications

#### REST API Endpoints
```yaml
Authentication:
  POST /api/auth/login/
  POST /api/auth/logout/
  GET /api/auth/user/
  PUT /api/auth/user/

Documents:
  GET /api/documents/
  POST /api/documents/
  GET /api/documents/{id}/
  PUT /api/documents/{id}/
  DELETE /api/documents/{id}/
  POST /api/documents/{id}/upload/
  GET /api/documents/{id}/download/{type}/
  POST /api/documents/{id}/sign/

Workflows:
  GET /api/workflows/
  POST /api/workflows/{document_id}/transition/
  GET /api/workflows/{document_id}/history/
  POST /api/workflows/{document_id}/approve/
  POST /api/workflows/{document_id}/reject/

Admin:
  GET /api/admin/users/
  POST /api/admin/users/{id}/roles/
  GET /api/admin/audit-trail/
  GET /api/admin/system-health/
  POST /api/admin/backup/
```

## 5. Setup Instructions

### 5.1 Infrastructure Setup

#### 5.1.1 Ubuntu Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    curl wget git vim \
    build-essential python3-dev \
    postgresql-client \
    redis-tools \
    podman podman-compose \
    nginx certbot python3-certbot-nginx

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 5432/tcp  # PostgreSQL
sudo ufw allow 6379/tcp  # Redis
sudo ufw allow 9200/tcp  # Elasticsearch
```

#### 5.1.2 Container Setup
```bash
# Create project directory
mkdir -p /opt/edms
cd /opt/edms

# Create container network
podman network create edms-network

# Create volumes for persistent data
podman volume create edms-postgres-data
podman volume create edms-redis-data
podman volume create edms-elasticsearch-data
podman volume create edms-file-storage
```

### 5.2 Database Setup

#### 5.2.1 PostgreSQL Container
```bash
# Create PostgreSQL container
podman run -d \
    --name edms-postgres \
    --network edms-network \
    -e POSTGRES_DB=edms \
    -e POSTGRES_USER=edms_user \
    -e POSTGRES_PASSWORD=secure_password_here \
    -v edms-postgres-data:/var/lib/postgresql/data \
    -p 5432:5432 \
    postgres:18

# Wait for database to start
sleep 30

# Create database and user
podman exec -it edms-postgres psql -U postgres -c "
    CREATE DATABASE edms;
    CREATE USER edms_user WITH PASSWORD 'secure_password_here';
    GRANT ALL PRIVILEGES ON DATABASE edms TO edms_user;
    ALTER USER edms_user CREATEDB;
"
```

#### 5.2.2 Redis Container
```bash
# Create Redis container
podman run -d \
    --name edms-redis \
    --network edms-network \
    -v edms-redis-data:/data \
    -p 6379:6379 \
    redis:7-alpine redis-server --appendonly yes
```

#### 5.2.3 Elasticsearch Container
```bash
# Create Elasticsearch container
podman run -d \
    --name edms-elasticsearch \
    --network edms-network \
    -e "discovery.type=single-node" \
    -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" \
    -e "xpack.security.enabled=false" \
    -v edms-elasticsearch-data:/usr/share/elasticsearch/data \
    -p 9200:9200 \
    elasticsearch:8.11.0
```

### 5.3 Application Setup

#### 5.3.1 Backend Container
```bash
# Create Dockerfile for Django backend
cat > Dockerfile.backend << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ \
    postgresql-client \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create entrypoint script
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]
EOF

# Create requirements.txt
cat > requirements.txt << EOF
Django==4.2.7
djangorestframework==3.14.0
django-river==3.4.0
celery==5.3.4
redis==5.0.1
psycopg2-binary==2.9.7
django-storages==1.14.2
python-docx-template==0.16.7
PyPDF2==3.0.1
pytesseract==0.3.10
cryptography==41.0.7
django-cors-headers==4.3.1
gunicorn==21.2.0
whitenoise==6.6.0
django-extensions==3.2.3
django-filter==23.4
drf-spectacular==0.27.0
pillow==10.1.0
EOF

# Build backend container
podman build -t edms-backend -f Dockerfile.backend .
```

#### 5.3.2 Frontend Container
```bash
# Create Dockerfile for React frontend
cat > Dockerfile.frontend << EOF
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# Build frontend container
podman build -t edms-frontend -f Dockerfile.frontend .
```

### 5.4 Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:18
    container_name: edms-postgres
    environment:
      POSTGRES_DB: edms
      POSTGRES_USER: edms_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - edms-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: edms-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - edms-network
    restart: unless-stopped

  elasticsearch:
    image: elasticsearch:8.11.0
    container_name: edms-elasticsearch
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - edms-network
    restart: unless-stopped

  backend:
    image: edms-backend
    container_name: edms-backend
    environment:
      - DATABASE_URL=postgresql://edms_user:${DB_PASSWORD}@postgres:5432/edms
      - REDIS_URL=redis://redis:6379/0
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - file_storage:/app/media
    networks:
      - edms-network
    depends_on:
      - postgres
      - redis
      - elasticsearch
    restart: unless-stopped

  celery:
    image: edms-backend
    container_name: edms-celery
    command: celery -A edms worker -l info
    environment:
      - DATABASE_URL=postgresql://edms_user:${DB_PASSWORD}@postgres:5432/edms
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - file_storage:/app/media
    networks:
      - edms-network
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery-beat:
    image: edms-backend
    container_name: edms-celery-beat
    command: celery -A edms beat -l info
    environment:
      - DATABASE_URL=postgresql://edms_user:${DB_PASSWORD}@postgres:5432/edms
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - file_storage:/app/media
    networks:
      - edms-network
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  frontend:
    image: edms-frontend
    container_name: edms-frontend
    ports:
      - "80:80"
      - "443:443"
    networks:
      - edms-network
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  file_storage:

networks:
  edms-network:
    driver: bridge
```

### 5.5 Environment Configuration

```bash
# Create .env file
cat > .env << EOF
# Database
DB_PASSWORD=your_secure_db_password_here
DATABASE_URL=postgresql://edms_user:your_secure_db_password_here@postgres:5432/edms

# Django
SECRET_KEY=your_secret_key_here_minimum_50_characters_long_random_string
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# Redis
REDIS_URL=redis://redis:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200

# Email (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password

# File Storage
MEDIA_ROOT=/app/media
MEDIA_URL=/media/

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Entra ID Integration
AZURE_AD_CLIENT_ID=your_azure_client_id
AZURE_AD_CLIENT_SECRET=your_azure_client_secret
AZURE_AD_TENANT_ID=your_azure_tenant_id

# Backup Configuration
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_ACCESS_KEY=your_backup_access_key
BACKUP_SECRET_KEY=your_backup_secret_key
EOF
```

## 6. Compliance Framework

### 6.1 21 CFR Part 11 Requirements

#### 6.1.1 Electronic Records (§11.10)
- **Validation**: System validation protocols and documentation
- **Access Control**: User authentication and authorization
- **Audit Trail**: Complete activity logging with tamper evidence
- **Data Integrity**: Checksums and encryption for data protection
- **Backup**: Regular backups with restoration procedures

#### 6.1.2 Electronic Signatures (§11.70)
- **Biometrics/Passwords**: Multi-factor authentication required
- **Unique Identification**: Each signature linked to specific user
- **Reliability**: Cryptographic integrity of signatures
- **Non-repudiation**: Signatures cannot be denied by signer

#### 6.1.3 Audit Trail Requirements
```python
# Audit trail must capture:
- User identification
- Date and time of action
- Action performed
- Previous value (for changes)
- New value (for changes)
- Reason for change (when applicable)
```

### 6.2 ALCOA Compliance

#### 6.2.1 Attributable
- Digital signatures with user identification
- User activity tracking
- Timestamp with user association

#### 6.2.2 Legible
- Clear document formatting
- Readable metadata display
- Proper document rendering

#### 6.2.3 Contemporaneous
- Real-time timestamp generation
- Immediate audit trail creation
- No backdating capabilities

#### 6.2.4 Original
- Immutable original documents
- Version control with original preservation
- No unauthorized modifications

#### 6.2.5 Accurate
- Input validation and error checking
- Data integrity verification
- Regular system validation

## 7. Security Implementation

### 7.1 Authentication & Authorization

#### 7.1.1 Multi-Factor Authentication
```python
# Django settings for MFA
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'edms.auth.EntraIDBackend',
]

# MFA configuration
MFA_REQUIRED = True
MFA_METHODS = ['totp', 'sms', 'email']
SESSION_TIMEOUT = 3600  # 1 hour
```

#### 7.1.2 Role-Based Access Control
```python
# Permission classes
class DocumentPermissions:
    READ = 'documents.view_document'
    WRITE = 'documents.add_document'
    REVIEW = 'documents.review_document'
    APPROVE = 'documents.approve_document'
    ADMIN = 'documents.admin_document'

# Role assignments
ROLES = {
    'viewer': [DocumentPermissions.READ],
    'author': [DocumentPermissions.READ, DocumentPermissions.WRITE],
    'reviewer': [DocumentPermissions.READ, DocumentPermissions.WRITE, DocumentPermissions.REVIEW],
    'approver': [DocumentPermissions.READ, DocumentPermissions.WRITE, DocumentPermissions.REVIEW, DocumentPermissions.APPROVE],
    'admin': [DocumentPermissions.READ, DocumentPermissions.WRITE, DocumentPermissions.REVIEW, DocumentPermissions.APPROVE, DocumentPermissions.ADMIN],
}
```

### 7.2 Data Encryption

#### 7.2.1 Database Encryption
```sql
-- Enable PostgreSQL encryption
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/path/to/server.crt';
ALTER SYSTEM SET ssl_key_file = '/path/to/server.key';

-- Enable row-level security
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY documents_user_policy ON documents
    FOR ALL TO authenticated_users
    USING (author_id = current_user_id());
```

#### 7.2.2 File Encryption
```python
# Django settings for file encryption
from cryptography.fernet import Fernet

class EncryptedFileSystemStorage(FileSystemStorage):
    def _save(self, name, content):
        # Encrypt file before saving
        key = settings.FILE_ENCRYPTION_KEY
        fernet = Fernet(key)
        encrypted_content = fernet.encrypt(content.read())
        # Save encrypted content
        return super()._save(name, ContentFile(encrypted_content))
```

### 7.3 Network Security

#### 7.3.1 SSL/TLS Configuration
```nginx
# Nginx SSL configuration
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
}
```

## 8. Development Guidelines

### 8.1 Code Structure

```
edms/
├── backend/
│   ├── edms/                 # Django project
│   │   ├── settings/         # Environment-specific settings
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── documents/        # Document management
│   │   ├── workflows/        # Workflow management
│   │   ├── users/           # User management
│   │   ├── audit/           # Audit trail
│   │   └── common/          # Shared utilities
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── store/           # Redux store
│   │   ├── services/        # API services
│   │   └── utils/           # Utility functions
│   ├── package.json
│   └── vite.config.ts
├── docker/
│   ├── backend/
│   ├── frontend/
│   └── nginx/
├── scripts/
│   ├── deploy.sh
│   ├── backup.sh
│   └── restore.sh
└── docs/
    ├── api/
    ├── user-guide/
    └── admin-guide/
```

### 8.2 Development Workflow

#### 8.2.1 Git Workflow
```bash
# Feature development
git checkout -b feature/document-upload
git commit -m "feat: implement document upload functionality"
git push origin feature/document-upload

# Create pull request for code review
# Merge after approval and testing
```

#### 8.2.2 Testing Strategy
```python
# Unit tests
class DocumentTestCase(TestCase):
    def test_document_creation(self):
        # Test document creation logic
        pass
    
    def test_workflow_transitions(self):
        # Test workflow state transitions
        pass

# Integration tests
class APITestCase(APITestCase):
    def test_document_upload_api(self):
        # Test document upload endpoint
        pass
```

### 8.3 Deployment Process

#### 8.3.1 Staging Deployment
```bash
# Deploy to staging
./scripts/deploy.sh staging

# Run tests
./scripts/run-tests.sh staging

# Validate compliance
./scripts/validate-compliance.sh staging
```

#### 8.3.2 Production Deployment
```bash
# Deploy to production
./scripts/deploy.sh production

# Monitor system health
./scripts/health-check.sh

# Backup before deployment
./scripts/backup.sh
```

This comprehensive guide provides the foundation for building a robust, compliant EDMS system. Each section can be expanded as development progresses and requirements evolve.