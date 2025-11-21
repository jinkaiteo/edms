# Missing Configuration Templates

## Overview
This document provides templates for all missing configuration items required for EDMS production deployment. Copy these templates and customize them for your organization.

## 1. Organization Configuration Template

### Company Information Template

```yaml
# config/organization.yaml
organization:
  # Basic Company Information
  company_name: "Your Company Name Inc."
  company_short_name: "YourCompany"
  domain: "yourcompany.com"
  
  # EDMS Specific Configuration
  edms_url: "edms.yourcompany.com"
  edms_system_name: "Electronic Document Management System"
  edms_version: "1.0.0"
  
  # Contact Information
  support_email: "edms-support@yourcompany.com"
  admin_email: "edms-admin@yourcompany.com"
  it_contact: "it-helpdesk@yourcompany.com"
  compliance_contact: "compliance@yourcompany.com"
  
  # Legal Information
  address: |
    Your Company Inc.
    123 Business Street
    Business City, ST 12345
    United States
  
  # Compliance Information
  regulatory_authority: "FDA"  # FDA, EMA, Health Canada, etc.
  gmp_license_number: "LICENSE-123456"
  
  # Logo and Branding
  logo_url: "/static/images/company-logo.png"
  favicon_url: "/static/images/favicon.ico"
  primary_color: "#1e40af"  # Blue
  secondary_color: "#059669"  # Green
  
  # Footer Text for Documents
  document_footer: |
    This document is controlled when maintained in the EDMS.
    Printed copies are uncontrolled unless otherwise specified.
    Property of {{ company_name }} - Confidential and Proprietary
```

## 2. Document Numbering Configuration Template

### Document Numbering Rules Template

```yaml
# config/document_numbering.yaml
document_numbering:
  # Global Settings
  separator: "-"
  year_format: "YYYY"  # YYYY or YY
  sequence_digits: 4   # Number of digits for sequence (0001, 0002, etc.)
  
  # Document Type Specific Rules
  rules:
    Policy:
      prefix: "POL"
      format: "POL-{YYYY}-{NNNN}"
      description: "Company policies and high-level procedures"
      example: "POL-2024-0001"
      retention_years: 10
      
    Manual:
      prefix: "MAN" 
      format: "MAN-{YYYY}-{NNNN}"
      description: "Comprehensive operational manuals"
      example: "MAN-2024-0001"
      retention_years: 7
      
    Procedures:
      prefix: "PROC"
      format: "PROC-{YYYY}-{NNNN}" 
      description: "Detailed step-by-step procedures"
      example: "PROC-2024-0001"
      retention_years: 7
      
    "Work Instructions (SOP)":
      prefix: "SOP"
      format: "SOP-{YYYY}-{NNNN}"
      description: "Standard Operating Procedures"
      example: "SOP-2024-0001"
      retention_years: 5
      
    "Forms and Templates":
      prefix: "FORM"
      format: "FORM-{YYYY}-{NNNN}"
      description: "Standardized forms and templates"
      example: "FORM-2024-0001"
      retention_years: 5
      
    Records:
      prefix: "REC"
      format: "REC-{YYYY}-{NNNN}"
      description: "Documentation records and evidence"
      example: "REC-2024-0001"
      retention_years: 15
  
  # Department/Site Specific Prefixes (Optional)
  site_prefixes:
    enabled: false
    rules:
      manufacturing:
        prefix: "MFG"
        format: "MFG-{DOC_TYPE}-{YYYY}-{NNNN}"
        example: "MFG-SOP-2024-0001"
      quality:
        prefix: "QA"
        format: "QA-{DOC_TYPE}-{YYYY}-{NNNN}"
        example: "QA-SOP-2024-0001"
      regulatory:
        prefix: "REG"
        format: "REG-{DOC_TYPE}-{YYYY}-{NNNN}"
        example: "REG-PROC-2024-0001"
  
  # Version Control
  version_format: "{MAJOR}.{MINOR}"
  initial_version: "1.0"
  version_increment_rules:
    major_change: "Complete rewrite, significant changes affecting other documents"
    minor_change: "Updates, corrections, additions that don't affect dependencies"
```

## 3. File Format Validation Template

### File Type Configuration Template

```yaml
# config/file_validation.yaml
file_validation:
  # Maximum file sizes (in bytes)
  max_file_sizes:
    default: 104857600      # 100MB
    pdf: 52428800          # 50MB
    docx: 104857600        # 100MB
    xlsx: 52428800         # 50MB
    images: 10485760       # 10MB
    
  # Allowed file extensions and MIME types
  allowed_formats:
    documents:
      - extension: ".pdf"
        mime_types: ["application/pdf"]
        description: "Portable Document Format"
        max_size: 52428800
        virus_scan: true
        content_validation: true
        
      - extension: ".doc"
        mime_types: ["application/msword"]
        description: "Microsoft Word Document (Legacy)"
        max_size: 104857600
        virus_scan: true
        content_validation: true
        
      - extension: ".docx"
        mime_types: [
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        description: "Microsoft Word Document"
        max_size: 104857600
        virus_scan: true
        content_validation: true
        placeholder_replacement: true
        
      - extension: ".xls"
        mime_types: ["application/vnd.ms-excel"]
        description: "Microsoft Excel Spreadsheet (Legacy)"
        max_size: 52428800
        virus_scan: true
        content_validation: true
        
      - extension: ".xlsx"
        mime_types: [
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]
        description: "Microsoft Excel Spreadsheet"
        max_size: 52428800
        virus_scan: true
        content_validation: true
        
      - extension: ".ppt"
        mime_types: ["application/vnd.ms-powerpoint"]
        description: "Microsoft PowerPoint Presentation (Legacy)"
        max_size: 104857600
        virus_scan: true
        content_validation: true
        
      - extension: ".pptx"
        mime_types: [
          "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ]
        description: "Microsoft PowerPoint Presentation"
        max_size: 104857600
        virus_scan: true
        content_validation: true
        
      - extension: ".txt"
        mime_types: ["text/plain"]
        description: "Plain Text File"
        max_size: 1048576  # 1MB
        virus_scan: true
        content_validation: false
        
      - extension: ".rtf"
        mime_types: ["application/rtf", "text/rtf"]
        description: "Rich Text Format"
        max_size: 10485760  # 10MB
        virus_scan: true
        content_validation: true
    
    images:
      - extension: ".jpg"
        mime_types: ["image/jpeg"]
        description: "JPEG Image"
        max_size: 10485760
        virus_scan: true
        
      - extension: ".jpeg"
        mime_types: ["image/jpeg"]
        description: "JPEG Image"
        max_size: 10485760
        virus_scan: true
        
      - extension: ".png"
        mime_types: ["image/png"]
        description: "PNG Image"
        max_size: 10485760
        virus_scan: true
        
      - extension: ".tiff"
        mime_types: ["image/tiff"]
        description: "TIFF Image"
        max_size: 10485760
        virus_scan: true
        
      - extension: ".bmp"
        mime_types: ["image/bmp"]
        description: "Bitmap Image"
        max_size: 10485760
        virus_scan: true
        
  # Content validation rules
  validation_rules:
    pdf:
      check_encryption: false  # Allow encrypted PDFs
      check_password_protection: false
      check_digital_signatures: true
      max_pages: 1000
      
    office_documents:
      check_macros: true  # Block documents with macros
      check_embedded_objects: true
      check_external_links: true
      scan_metadata: true
      
    images:
      check_exif_data: true
      max_resolution: "10000x10000"
      min_resolution: "50x50"
      
  # Virus scanning configuration
  virus_scanning:
    enabled: true
    engine: "clamav"  # clamav, windows_defender, custom
    quarantine_infected: true
    scan_timeout_seconds: 30
    
  # File naming restrictions
  filename_rules:
    max_length: 255
    forbidden_characters: ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    forbidden_names: [
      'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
      'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
      'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    case_sensitive: false
```

## 4. Digital Certificate & PKI Configuration Template

### Certificate Authority Setup Template

```yaml
# config/certificate_authority.yaml
certificate_authority:
  # CA Type
  ca_type: "internal"  # internal, external, hybrid
  
  # Internal CA Configuration
  internal_ca:
    # Root CA Configuration
    root_ca:
      common_name: "YourCompany Root CA"
      organization: "Your Company Inc."
      organizational_unit: "Information Technology"
      country: "US"
      state: "State"
      city: "City"
      email: "ca-admin@yourcompany.com"
      key_size: 4096
      validity_years: 20
      
    # Intermediate CA Configuration
    intermediate_ca:
      common_name: "YourCompany EDMS Intermediate CA"
      organization: "Your Company Inc."
      organizational_unit: "EDMS System"
      country: "US"
      state: "State"
      city: "City"
      email: "edms-ca@yourcompany.com"
      key_size: 2048
      validity_years: 10
      
  # External CA Configuration
  external_ca:
    provider: ""  # DigiCert, Entrust, GlobalSign, etc.
    api_endpoint: ""
    api_key: ""
    certificate_template: ""
    
  # Certificate Templates
  certificate_templates:
    user_signing:
      template_name: "EDMS User Signing Certificate"
      key_usage: ["digital_signature", "non_repudiation"]
      extended_key_usage: ["document_signing"]
      validity_years: 2
      key_size: 2048
      subject_format: "CN={first_name} {last_name} ({employee_id}),OU=Employees,O={organization},C={country}"
      
    system_tls:
      template_name: "EDMS System TLS Certificate"
      key_usage: ["key_encipherment", "digital_signature"]
      extended_key_usage: ["server_auth", "client_auth"]
      validity_years: 1
      key_size: 2048
      subject_format: "CN={hostname},O={organization},C={country}"
      san_dns: ["edms.yourcompany.com", "*.edms.yourcompany.com"]
      
  # Certificate Storage
  storage:
    certificates_path: "/edms-storage/certificates"
    private_keys_path: "/edms-storage/certificates/private"
    ca_bundle_path: "/edms-storage/certificates/ca-bundle.crt"
    crl_path: "/edms-storage/certificates/crl"
    
  # Certificate Lifecycle
  lifecycle:
    renewal_threshold_days: 30
    notification_threshold_days: 60
    auto_renewal: true
    backup_old_certificates: true
    
  # Certificate Revocation
  revocation:
    crl_enabled: true
    crl_update_interval_hours: 24
    ocsp_enabled: false
    ocsp_responder_url: ""
    
  # User Enrollment
  enrollment:
    self_enrollment: false
    admin_approval_required: true
    email_verification: true
    identity_verification_required: true
```

## 5. Azure Active Directory Integration Template

### Azure AD Configuration Template

```yaml
# config/azure_ad.yaml
azure_active_directory:
  # Basic Configuration
  tenant_id: "your-tenant-id-here"  # Get from Azure Portal
  client_id: "your-client-id-here"  # App Registration Client ID
  client_secret: "your-client-secret-here"  # App Registration Secret
  
  # OAuth/OIDC Configuration
  authority: "https://login.microsoftonline.com/{tenant_id}"
  redirect_uri: "https://edms.yourcompany.com/auth/azure/callback/"
  post_logout_redirect_uri: "https://edms.yourcompany.com/auth/logout/"
  
  # Scopes
  scopes:
    - "User.Read"
    - "User.ReadBasic.All"
    - "GroupMember.Read.All"
    
  # User Mapping
  user_mapping:
    username_field: "userPrincipalName"  # or "mail"
    email_field: "mail"
    first_name_field: "givenName"
    last_name_field: "surname"
    employee_id_field: "employeeId"
    department_field: "department"
    title_field: "jobTitle"
    manager_field: "manager"
    
  # Group Mapping to EDMS Roles
  group_mapping:
    # Azure AD Group Object IDs to EDMS Groups
    "azure-group-id-1": "Document Authors"
    "azure-group-id-2": "Document Reviewers"
    "azure-group-id-3": "Document Approvers"
    "azure-group-id-4": "Document Administrators"
    "azure-group-id-5": "EDMS Administrators"
    
  # User Synchronization
  user_sync:
    auto_create_users: true
    auto_update_users: true
    sync_disabled_users: true
    sync_interval_hours: 24
    sync_on_login: true
    
  # Multi-Factor Authentication
  mfa:
    enforce_mfa: true
    trusted_device_days: 30
    backup_codes_enabled: true
    
  # Conditional Access
  conditional_access:
    enforce_device_compliance: false
    require_managed_device: false
    allowed_locations: []  # IP ranges or named locations
    
  # Session Management
  session:
    token_lifetime_minutes: 60
    refresh_token_lifetime_days: 30
    remember_me_days: 30
```

### LDAP/On-Premises AD Template

```yaml
# config/ldap.yaml
ldap_configuration:
  # LDAP Server Configuration
  server:
    host: "ldap.yourcompany.com"
    port: 636  # 389 for non-SSL, 636 for SSL
    use_ssl: true
    use_tls: false
    timeout: 10
    
  # Authentication
  bind_dn: "CN=EDMS Service Account,OU=Service Accounts,DC=yourcompany,DC=com"
  bind_password: "service-account-password"
  
  # Search Configuration
  search:
    base_dn: "DC=yourcompany,DC=com"
    user_dn: "OU=Users,DC=yourcompany,DC=com"
    group_dn: "OU=Groups,DC=yourcompany,DC=com"
    
  # User Attributes Mapping
  user_attributes:
    username: "sAMAccountName"
    email: "mail"
    first_name: "givenName"
    last_name: "sn"
    full_name: "displayName"
    employee_id: "employeeID"
    department: "department"
    title: "title"
    manager: "manager"
    phone: "telephoneNumber"
    
  # Group Attributes
  group_attributes:
    name: "cn"
    description: "description"
    members: "member"
    
  # Search Filters
  filters:
    user_filter: "(&(objectClass=user)(!(objectClass=computer)))"
    group_filter: "(objectClass=group)"
    active_user_filter: "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
    
  # Group Mapping
  group_mapping:
    "CN=EDMS Authors,OU=Groups,DC=yourcompany,DC=com": "Document Authors"
    "CN=EDMS Reviewers,OU=Groups,DC=yourcompany,DC=com": "Document Reviewers"
    "CN=EDMS Approvers,OU=Groups,DC=yourcompany,DC=com": "Document Approvers"
    "CN=EDMS Admins,OU=Groups,DC=yourcompany,DC=com": "Document Administrators"
```

## 6. Environment-Specific Configuration Template

### Development Environment Template

```yaml
# config/environments/development.yaml
environment: development

database:
  name: "edms_dev"
  host: "localhost"
  port: 5432
  user: "edms_dev_user"
  password: "dev_password_change_me"
  
security:
  secret_key: "dev-secret-key-change-in-production"
  debug: true
  allowed_hosts: ["localhost", "127.0.0.1", "0.0.0.0"]
  ssl_redirect: false
  session_cookie_secure: false
  csrf_cookie_secure: false
  
storage:
  root: "/path/to/development/storage"
  backup_enabled: false
  encryption_enabled: true
  
external_services:
  redis_url: "redis://localhost:6379/0"
  elasticsearch_url: "http://localhost:9200"
  email_backend: "console"
  
azure_ad:
  enabled: false  # Use local authentication in dev
  
logging:
  level: "DEBUG"
  file: "/tmp/edms_dev.log"
  
features:
  virus_scanning: false
  file_encryption: false
  compliance_mode: false
```

### Staging Environment Template

```yaml
# config/environments/staging.yaml
environment: staging

database:
  name: "edms_staging"
  host: "staging-db.internal"
  port: 5432
  user: "edms_staging_user"
  password: "${DATABASE_PASSWORD}"  # From environment variable
  
security:
  secret_key: "${DJANGO_SECRET_KEY}"
  debug: false
  allowed_hosts: ["staging-edms.yourcompany.com"]
  ssl_redirect: true
  session_cookie_secure: true
  csrf_cookie_secure: true
  
storage:
  root: "/edms-storage"
  backup_enabled: true
  encryption_enabled: true
  
external_services:
  redis_url: "redis://staging-redis.internal:6379/0"
  elasticsearch_url: "http://staging-elasticsearch.internal:9200"
  email_backend: "smtp"
  email_host: "staging-smtp.yourcompany.com"
  
azure_ad:
  enabled: true
  tenant_id: "${AZURE_TENANT_ID}"
  client_id: "${AZURE_CLIENT_ID_STAGING}"
  
logging:
  level: "INFO"
  file: "/edms-storage/logs/edms_staging.log"
  
features:
  virus_scanning: true
  file_encryption: true
  compliance_mode: true
```

### Production Environment Template

```yaml
# config/environments/production.yaml
environment: production

database:
  name: "edms_prod"
  host: "prod-db.internal"
  port: 5432
  user: "edms_prod_user"
  password: "${DATABASE_PASSWORD}"
  connection_pool_size: 20
  max_connections: 100
  
security:
  secret_key: "${DJANGO_SECRET_KEY}"
  debug: false
  allowed_hosts: ["edms.yourcompany.com"]
  ssl_redirect: true
  session_cookie_secure: true
  csrf_cookie_secure: true
  secure_hsts_seconds: 31536000
  secure_hsts_include_subdomains: true
  
storage:
  root: "/edms-storage"
  backup_enabled: true
  encryption_enabled: true
  backup_retention_days: 90
  
external_services:
  redis_url: "redis://prod-redis.internal:6379/0"
  elasticsearch_url: "http://prod-elasticsearch.internal:9200"
  email_backend: "smtp"
  email_host: "smtp.yourcompany.com"
  email_port: 587
  email_use_tls: true
  
azure_ad:
  enabled: true
  tenant_id: "${AZURE_TENANT_ID}"
  client_id: "${AZURE_CLIENT_ID_PROD}"
  
logging:
  level: "WARNING"
  file: "/edms-storage/logs/edms_prod.log"
  max_file_size: "100MB"
  backup_count: 5
  
monitoring:
  metrics_enabled: true
  health_check_url: "/health/"
  prometheus_metrics: true
  
features:
  virus_scanning: true
  file_encryption: true
  compliance_mode: true
  
performance:
  cache_timeout: 300
  session_timeout: 1800
  max_upload_size: 104857600
  
backup:
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention_policy:
    daily: 7
    weekly: 4
    monthly: 12
    yearly: 7
```

## 7. Infrastructure Specifications Template

### Server Requirements Template

```yaml
# config/infrastructure.yaml
infrastructure:
  # Production Server Specifications
  production:
    application_servers:
      count: 3
      cpu_cores: 8
      ram_gb: 32
      disk_space_gb: 500
      network_bandwidth: "1 Gbps"
      operating_system: "Ubuntu 20.04.6 LTS"
      
    database_server:
      cpu_cores: 16
      ram_gb: 64
      disk_space_gb: 1000
      disk_type: "NVMe SSD"
      iops: 10000
      backup_storage_gb: 5000
      
    cache_servers:
      count: 2
      cpu_cores: 4
      ram_gb: 16
      disk_space_gb: 100
      
    search_servers:
      count: 3
      cpu_cores: 8
      ram_gb: 32
      disk_space_gb: 1000
      
    load_balancer:
      count: 2
      cpu_cores: 4
      ram_gb: 8
      disk_space_gb: 100
      ssl_termination: true
      
  # Network Configuration
  network:
    subnets:
      web_tier: "10.0.1.0/24"
      app_tier: "10.0.2.0/24"
      data_tier: "10.0.3.0/24"
      
    firewall_rules:
      - source: "0.0.0.0/0"
        destination: "web_tier"
        ports: [80, 443]
        protocol: "TCP"
        
      - source: "web_tier"
        destination: "app_tier"
        ports: [8000]
        protocol: "TCP"
        
      - source: "app_tier"
        destination: "data_tier"
        ports: [5432, 6379, 9200]
        protocol: "TCP"
        
    dns:
      primary_domain: "edms.yourcompany.com"
      subdomains:
        - "api.edms.yourcompany.com"
        - "admin.edms.yourcompany.com"
        
  # Backup Storage
  backup:
    storage_type: "Network Attached Storage"
    capacity_tb: 10
    redundancy: "RAID 6"
    offsite_replication: true
    encryption: "AES-256"
    
  # Monitoring Infrastructure
  monitoring:
    prometheus_server:
      cpu_cores: 4
      ram_gb: 16
      disk_space_gb: 500
      
    grafana_server:
      cpu_cores: 2
      ram_gb: 8
      disk_space_gb: 100
      
    log_aggregation:
      storage_gb: 1000
      retention_days: 90
```

## 8. Security Configuration Template

### Security Hardening Template

```yaml
# config/security.yaml
security_configuration:
  # Password Policy
  password_policy:
    minimum_length: 12
    require_uppercase: true
    require_lowercase: true
    require_numbers: true
    require_special_characters: true
    forbidden_patterns:
      - "password"
      - "123456"
      - "qwerty"
      - "{username}"
      - "{first_name}"
      - "{last_name}"
    password_history: 12
    max_age_days: 90
    
  # Account Security
  account_security:
    max_login_attempts: 5
    lockout_duration_minutes: 30
    session_timeout_minutes: 30
    max_concurrent_sessions: 3
    password_reset_token_timeout_hours: 24
    
  # Network Security
  network_security:
    allowed_ip_ranges:
      - "192.168.1.0/24"    # Corporate network
      - "10.0.0.0/8"        # VPN range
    blocked_countries: []   # ISO country codes
    rate_limiting:
      login_attempts: "5/minute"
      api_requests: "100/minute"
      file_uploads: "10/minute"
      
  # Data Protection
  data_protection:
    encryption_algorithm: "AES-256-GCM"
    key_rotation_days: 90
    data_classification:
      public: "No protection required"
      internal: "Internal use only"
      confidential: "Restricted access"
      restricted: "Highest security level"
      
  # Audit and Compliance
  audit:
    log_retention_days: 2555  # 7 years
    real_time_monitoring: true
    automated_compliance_checks: true
    security_scan_frequency: "weekly"
    vulnerability_scan_frequency: "monthly"
    
  # File Security
  file_security:
    virus_scanning_mandatory: true
    quarantine_suspicious_files: true
    content_inspection: true
    metadata_sanitization: true
    
  # Communication Security
  communication:
    force_https: true
    hsts_max_age: 31536000
    disable_http: true
    certificate_pinning: true
    perfect_forward_secrecy: true
```

## 9. Notification Configuration Template

### Email and Notification Template

```yaml
# config/notifications.yaml
notifications:
  # Email Configuration
  email:
    smtp_host: "smtp.yourcompany.com"
    smtp_port: 587
    smtp_use_tls: true
    smtp_username: "edms@yourcompany.com"
    smtp_password: "${EMAIL_PASSWORD}"
    from_email: "EDMS System <edms@yourcompany.com>"
    reply_to: "edms-support@yourcompany.com"
    
  # Notification Templates
  templates:
    document_submitted_for_review:
      subject: "Document Review Required: {document_title}"
      template: "emails/document_review_request.html"
      recipients: ["reviewer"]
      
    document_approved:
      subject: "Document Approved: {document_title}"
      template: "emails/document_approved.html"
      recipients: ["author", "reviewer"]
      
    document_rejected:
      subject: "Document Rejected: {document_title}"
      template: "emails/document_rejected.html"
      recipients: ["author"]
      
    document_effective:
      subject: "Document Now Effective: {document_title}"
      template: "emails/document_effective.html"
      recipients: ["all_users"]
      
    document_expiring:
      subject: "Document Expiring Soon: {document_title}"
      template: "emails/document_expiring.html"
      recipients: ["author", "document_admin"]
      
    user_account_locked:
      subject: "Account Security Alert"
      template: "emails/account_locked.html"
      recipients: ["user", "security_admin"]
      
    backup_failed:
      subject: "CRITICAL: Backup Failure"
      template: "emails/backup_failed.html"
      recipients: ["system_admin"]
      
  # Notification Channels
  channels:
    email: true
    sms: false
    in_app: true
    webhook: false
    
  # Delivery Settings
  delivery:
    batch_size: 50
    retry_attempts: 3
    retry_delay_minutes: 5
    delivery_timeout_seconds: 30
```

## 10. Configuration Usage Instructions

### How to Use These Templates

```bash
# 1. Copy templates to your project
cp Dev_Docs/Missing_Configuration_Templates.md config/

# 2. Create environment-specific files
mkdir -p config/environments
touch config/environments/development.yaml
touch config/environments/staging.yaml
touch config/environments/production.yaml

# 3. Fill in organization-specific values
# Edit each file and replace placeholder values with real data

# 4. Set environment variables
export ENVIRONMENT=development  # or staging, production
export DATABASE_PASSWORD="your-secure-password"
export DJANGO_SECRET_KEY="your-secret-key"
export AZURE_CLIENT_SECRET="your-azure-secret"

# 5. Load configuration in Django settings
# Add to settings.py:
import yaml
import os

env = os.getenv('ENVIRONMENT', 'development')
with open(f'config/environments/{env}.yaml') as f:
    CONFIG = yaml.safe_load(f)
```

## Next Steps

1. **Copy these templates** to your project configuration directory
2. **Replace placeholder values** with your organization's specific information
3. **Validate configuration** using the provided schemas
4. **Test each environment** before deploying to production
5. **Document any customizations** for your team

These templates provide a solid foundation for configuring your EDMS system for production use while maintaining security and compliance standards.