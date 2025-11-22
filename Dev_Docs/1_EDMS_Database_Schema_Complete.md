# EDMS Complete Database Schema Design

## Overview
This document provides the complete PostgreSQL database schema for the 21 CFR Part 11 compliant EDMS system, including all tables, indexes, constraints, and Django model definitions.

## PostgreSQL Schema

### Core User and Authentication Tables

```sql
-- Users (extending Django's User model)
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- User Profiles
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    department VARCHAR(100),
    employee_id VARCHAR(50) UNIQUE,
    phone VARCHAR(20),
    title VARCHAR(100),
    manager_id INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Groups and Permissions
CREATE TABLE auth_group (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE auth_user_groups (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES auth_group(id) ON DELETE CASCADE,
    UNIQUE(user_id, group_id)
);
```

### Document Management Tables

```sql
-- Document Types
CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    template_path VARCHAR(500),
    retention_period INTEGER, -- days
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Sources
CREATE TABLE document_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Main Documents Table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    version_major INTEGER DEFAULT 1,
    version_minor INTEGER DEFAULT 0,
    document_type_id INTEGER REFERENCES document_types(id),
    document_source_id INTEGER REFERENCES document_sources(id),
    author_id INTEGER REFERENCES auth_user(id) NOT NULL,
    reviewer_id INTEGER REFERENCES auth_user(id),
    approver_id INTEGER REFERENCES auth_user(id),
    status VARCHAR(50) DEFAULT 'DRAFT',
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size BIGINT,
    file_checksum VARCHAR(64),
    mime_type VARCHAR(100),
    approval_date DATE,
    effective_date DATE,
    obsolete_date DATE,
    reason_for_change TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Dependencies
CREATE TABLE document_dependencies (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    depends_on_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'REFERENCE', -- REFERENCE, TEMPLATE, SUPERSEDES
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, depends_on_id)
);

-- Document Versions (History)
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    version_major INTEGER NOT NULL,
    version_minor INTEGER NOT NULL,
    file_path VARCHAR(500),
    file_checksum VARCHAR(64),
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT,
    metadata JSONB DEFAULT '{}'
);
```

### Workflow Management Tables (Enhanced Simple Workflow Engine)

```sql
-- Workflow States
CREATE TABLE river_state (
    id SERIAL PRIMARY KEY,
    label VARCHAR(50) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Transitions
CREATE TABLE river_transition (
    id SERIAL PRIMARY KEY,
    source_state_id INTEGER REFERENCES river_state(id),
    destination_state_id INTEGER REFERENCES river_state(id) NOT NULL,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Approval Metadata
CREATE TABLE river_transitionapprovalmeta (
    id SERIAL PRIMARY KEY,
    transition_id INTEGER REFERENCES river_transition(id) ON DELETE CASCADE,
    content_type_id INTEGER NOT NULL,
    field_name VARCHAR(200) NOT NULL,
    priority INTEGER DEFAULT 0,
    groups JSONB DEFAULT '[]',
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Approvals
CREATE TABLE river_transitionapproval (
    id SERIAL PRIMARY KEY,
    content_type_id INTEGER NOT NULL,
    object_id VARCHAR(100) NOT NULL,
    field_name VARCHAR(200) NOT NULL,
    transition_id INTEGER REFERENCES river_transition(id),
    meta_id INTEGER REFERENCES river_transitionapprovalmeta(id),
    transactioner_id INTEGER REFERENCES auth_user(id),
    status INTEGER DEFAULT 0, -- 0: Pending, 1: Approved, 2: Rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_date TIMESTAMP
);

-- Document Workflow States
CREATE TABLE document_workflow_states (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    state_id INTEGER REFERENCES river_state(id) NOT NULL,
    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    entered_by INTEGER REFERENCES auth_user(id),
    comments TEXT,
    is_current BOOLEAN DEFAULT TRUE
);
```

### Audit Trail Tables

```sql
-- Audit Trail
CREATE TABLE audit_trail (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    user_id INTEGER REFERENCES auth_user(id),
    ip_address INET,
    user_agent TEXT,
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB,
    reason TEXT,
    session_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Events
CREATE TABLE system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'INFO', -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    user_id INTEGER REFERENCES auth_user(id),
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Login Attempts
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150),
    ip_address INET NOT NULL,
    user_agent TEXT,
    success BOOLEAN DEFAULT FALSE,
    failure_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Service Module Tables

```sql
-- Scheduled Tasks (S3)
CREATE TABLE scheduled_tasks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL, -- BACKUP, CLEANUP, NOTIFICATION, etc.
    cron_expression VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    last_status VARCHAR(20), -- SUCCESS, FAILED, RUNNING
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Task Execution Log
CREATE TABLE task_executions (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES scheduled_tasks(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'RUNNING',
    output TEXT,
    error_message TEXT,
    execution_time INTEGER -- seconds
);

-- Backup Records (S4)
CREATE TABLE backup_records (
    id SERIAL PRIMARY KEY,
    backup_type VARCHAR(50) NOT NULL, -- DATABASE, FILES, CONFIGURATION
    file_path VARCHAR(500),
    file_size BIGINT,
    checksum VARCHAR(64),
    compression_type VARCHAR(20),
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'COMPLETED',
    retention_until DATE
);

-- Placeholder Definitions (S6)
CREATE TABLE placeholder_definitions (
    id SERIAL PRIMARY KEY,
    placeholder_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150),
    description TEXT,
    metadata_field VARCHAR(100),
    format_type VARCHAR(50) DEFAULT 'TEXT', -- TEXT, DATE, NUMBER, BOOLEAN
    format_pattern VARCHAR(100),
    is_system BOOLEAN DEFAULT FALSE, -- Cannot be deleted
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- App Settings (S7)
CREATE TABLE app_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    data_type VARCHAR(20) DEFAULT 'STRING', -- STRING, INTEGER, BOOLEAN, JSON
    category VARCHAR(50),
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Document Download and Access Tracking

```sql
-- Document Downloads
CREATE TABLE document_downloads (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth_user(id) NOT NULL,
    download_type VARCHAR(50) NOT NULL, -- ORIGINAL, ANNOTATED, OFFICIAL_PDF
    ip_address INET,
    user_agent TEXT,
    file_checksum VARCHAR(64),
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Access Log
CREATE TABLE document_access_log (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth_user(id) NOT NULL,
    access_type VARCHAR(50) NOT NULL, -- VIEW, DOWNLOAD, EDIT, APPROVE
    ip_address INET,
    session_id VARCHAR(100),
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INTEGER
);
```

### Electronic Signatures

```sql
-- Digital Certificates
CREATE TABLE digital_certificates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) NOT NULL,
    certificate_data BYTEA NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    issuer VARCHAR(255),
    subject VARCHAR(255),
    valid_from DATE NOT NULL,
    valid_until DATE NOT NULL,
    fingerprint VARCHAR(64),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Electronic Signatures
CREATE TABLE electronic_signatures (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth_user(id) NOT NULL,
    certificate_id INTEGER REFERENCES digital_certificates(id),
    signature_data BYTEA NOT NULL,
    signature_hash VARCHAR(64),
    signature_algorithm VARCHAR(50),
    signature_reason VARCHAR(255),
    signature_location VARCHAR(100),
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);
```

## Indexes for Performance

```sql
-- Document indexes
CREATE INDEX idx_documents_number ON documents(document_number);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_author ON documents(author_id);
CREATE INDEX idx_documents_type ON documents(document_type_id);
CREATE INDEX idx_documents_created ON documents(created_at);
CREATE INDEX idx_documents_effective ON documents(effective_date);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);

-- Audit trail indexes
CREATE INDEX idx_audit_trail_table ON audit_trail(table_name);
CREATE INDEX idx_audit_trail_record ON audit_trail(record_id);
CREATE INDEX idx_audit_trail_user ON audit_trail(user_id);
CREATE INDEX idx_audit_trail_created ON audit_trail(created_at);

-- Workflow indexes
CREATE INDEX idx_workflow_states_document ON document_workflow_states(document_id);
CREATE INDEX idx_workflow_states_current ON document_workflow_states(is_current);

-- Download tracking indexes
CREATE INDEX idx_downloads_document ON document_downloads(document_id);
CREATE INDEX idx_downloads_user ON document_downloads(user_id);
CREATE INDEX idx_downloads_date ON document_downloads(downloaded_at);
```

## Row-Level Security Policies

```sql
-- Enable RLS on sensitive tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_trail ENABLE ROW LEVEL SECURITY;
ALTER TABLE electronic_signatures ENABLE ROW LEVEL SECURITY;

-- Document access policy (users can only see documents they have permission to)
CREATE POLICY document_access_policy ON documents
    FOR ALL TO authenticated_users
    USING (
        author_id = current_user_id() OR
        reviewer_id = current_user_id() OR
        approver_id = current_user_id() OR
        status IN ('Approved and Effective', 'Obsolete') OR
        has_document_permission(id, current_user_id())
    );

-- Audit trail read-only for non-admins
CREATE POLICY audit_read_policy ON audit_trail
    FOR SELECT TO authenticated_users
    USING (user_id = current_user_id() OR is_admin(current_user_id()));
```

## Triggers for Audit Trail

```sql
-- Function to capture changes
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_trail (
            table_name, record_id, action, user_id, 
            old_values, created_at
        ) VALUES (
            TG_TABLE_NAME, OLD.id::TEXT, 'DELETE', current_user_id(),
            row_to_json(OLD), CURRENT_TIMESTAMP
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_trail (
            table_name, record_id, action, user_id,
            old_values, new_values, created_at
        ) VALUES (
            TG_TABLE_NAME, NEW.id::TEXT, 'UPDATE', current_user_id(),
            row_to_json(OLD), row_to_json(NEW), CURRENT_TIMESTAMP
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_trail (
            table_name, record_id, action, user_id,
            new_values, created_at
        ) VALUES (
            TG_TABLE_NAME, NEW.id::TEXT, 'INSERT', current_user_id(),
            row_to_json(NEW), CURRENT_TIMESTAMP
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to key tables
CREATE TRIGGER documents_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON documents
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER user_profiles_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

## Initial Data Population

```sql
-- Insert default document types
INSERT INTO document_types (name, description) VALUES
('Policy', 'High-level organizational policies'),
('Manual', 'Comprehensive procedural manuals'),
('Procedures', 'Detailed step-by-step procedures'),
('Work Instructions (SOP)', 'Standard Operating Procedures'),
('Forms and Templates', 'Standardized forms and templates'),
('Records', 'Documented evidence of activities');

-- Insert default document sources
INSERT INTO document_sources (name, description) VALUES
('Original Digital Draft', 'Original draft uploaded to EDMS'),
('Scanned Original', 'Digital file created from original physical document'),
('Scanned Copy', 'Digital file created from photocopy of original');

-- Insert default workflow states
INSERT INTO river_state (label, slug) VALUES
('Draft', 'draft'),
('Pending Review', 'pending_review'),
('Reviewed', 'reviewed'),
('Pending Approval', 'pending_approval'),
('Approved, Pending Effective', 'approved_pending_effective'),
('Approved and Effective', 'approved_effective'),
('Superseded', 'superseded'),
('Pending Obsoleting', 'pending_obsoleting'),
('Obsolete', 'obsolete');

-- Insert default app settings
INSERT INTO app_settings (key, value, category, description) VALUES
('company_name', 'Acme Pharmaceuticals Inc.', 'general', 'Company name for documents'),
('system_name', 'Electronic Document Management System', 'general', 'EDMS system name'),
('footer_text', 'This document is controlled. Printed copies are uncontrolled.', 'general', 'Standard document footer'),
('document_number_prefix', 'DOC', 'documents', 'Prefix for auto-generated document numbers'),
('backup_retention_days', '90', 'backup', 'Number of days to retain backup files'),
('max_file_size_mb', '100', 'documents', 'Maximum file size for document uploads'),
('session_timeout_minutes', '30', 'security', 'User session timeout in minutes');
```

This complete database schema provides:

1. **All required tables** with proper relationships and constraints
2. **Row-level security** for data protection
3. **Audit trail automation** through triggers
4. **Performance optimization** through strategic indexing
5. **Initial data** for system startup
6. **21 CFR Part 11 compliance** structure
7. **Django-River integration** for workflow management
8. **Electronic signature** support
9. **Comprehensive tracking** of all user actions

The schema is designed to support all EDMS modules (O1, S1-S7) and maintains data integrity while enabling efficient querying and reporting.