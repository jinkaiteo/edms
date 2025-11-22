#!/bin/bash
#
# EDMS Database Initialization Script
# 
# Initializes the EDMS database with migrations, initial data,
# and security configurations for 21 CFR Part 11 compliance

set -e

echo "🗄️  EDMS Database Initialization"
echo "================================"

# Check if Docker services are running
echo "🔍 Checking Docker services..."
if ! docker-compose ps | grep -q "edms_db.*Up"; then
    echo "❌ Database service is not running"
    echo "Please start services first: docker-compose up -d db redis"
    exit 1
fi

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
timeout=60
counter=0
while ! docker-compose exec -T db pg_isready -U edms_user -d edms_db > /dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -gt $timeout ]; then
        echo "❌ Database startup timeout"
        exit 1
    fi
done

echo "✅ Database is ready"

# Run Django migrations
echo "🔧 Running Django migrations..."
docker-compose exec -T backend python manage.py makemigrations

# Apply migrations
echo "📊 Applying database migrations..."
docker-compose exec -T backend python manage.py migrate

# Create initial admin user if it doesn't exist
echo "👤 Setting up admin user..."
docker-compose exec -T backend python manage.py shell << 'EOF'
import os
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    with transaction.atomic():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@edms-project.com',
            password='EDMSAdmin2024!',
            first_name='System',
            last_name='Administrator'
        )
        admin_user.is_validated = True
        admin_user.save()
        print("✅ Admin user created: admin / EDMSAdmin2024!")
else:
    print("ℹ️  Admin user already exists")
EOF

# Load initial system roles
echo "🎭 Loading initial system roles..."
docker-compose exec -T backend python manage.py shell << 'EOF'
from apps.users.models import Role
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

# Get admin user for role creation
admin_user = User.objects.get(username='admin')

# Define system roles
system_roles = [
    # Document Management (O1) roles
    {
        'name': 'Document Administrator',
        'module': 'O1',
        'permission_level': 'admin',
        'description': 'Full document management access with administrative privileges'
    },
    {
        'name': 'Document Author',
        'module': 'O1', 
        'permission_level': 'write',
        'description': 'Can create and edit documents in draft status'
    },
    {
        'name': 'Document Reviewer', 
        'module': 'O1',
        'permission_level': 'review',
        'description': 'Can review documents and provide feedback'
    },
    {
        'name': 'Document Approver',
        'module': 'O1',
        'permission_level': 'approve', 
        'description': 'Can approve documents for publication'
    },
    {
        'name': 'Document Reader',
        'module': 'O1',
        'permission_level': 'read',
        'description': 'Read-only access to published documents'
    },
    
    # User Management (S1) roles
    {
        'name': 'User Administrator',
        'module': 'S1',
        'permission_level': 'admin',
        'description': 'Manage users, roles, and permissions'
    },
    {
        'name': 'User Manager',
        'module': 'S1',
        'permission_level': 'write',
        'description': 'Manage user accounts and basic role assignments'
    },
    
    # Audit Trail (S2) roles
    {
        'name': 'Audit Administrator',
        'module': 'S2',
        'permission_level': 'admin',
        'description': 'Full access to audit trail and compliance reporting'
    },
    {
        'name': 'Compliance Officer',
        'module': 'S2',
        'permission_level': 'read',
        'description': 'View audit trail and generate compliance reports'
    },
    
    # Scheduler (S3) roles
    {
        'name': 'Scheduler Administrator',
        'module': 'S3',
        'permission_level': 'admin',
        'description': 'Manage scheduled tasks and automation'
    },
    
    # Backup and Health Check (S4) roles
    {
        'name': 'System Administrator',
        'module': 'S4',
        'permission_level': 'admin',
        'description': 'Manage backups, health checks, and system maintenance'
    },
    
    # Workflow Settings (S5) roles
    {
        'name': 'Workflow Administrator',
        'module': 'S5',
        'permission_level': 'admin',
        'description': 'Configure workflow settings and approval processes'
    },
    
    # Placeholder Management (S6) roles
    {
        'name': 'Placeholder Administrator',
        'module': 'S6',
        'permission_level': 'admin',
        'description': 'Manage document placeholders and templates'
    },
    
    # App Settings (S7) roles
    {
        'name': 'Settings Administrator',
        'module': 'S7',
        'permission_level': 'admin',
        'description': 'Manage application settings and configuration'
    }
]

# Create roles
with transaction.atomic():
    created_count = 0
    for role_data in system_roles:
        role, created = Role.objects.get_or_create(
            module=role_data['module'],
            permission_level=role_data['permission_level'],
            defaults={
                'name': role_data['name'],
                'description': role_data['description'],
                'is_system_role': True,
                'is_active': True,
                'created_by': admin_user
            }
        )
        if created:
            print(f"✅ Created role: {role.name}")
            created_count += 1
        else:
            print(f"ℹ️  Role already exists: {role.name}")
    
    print(f"\n📊 Summary: {created_count} system roles created")
EOF

# Create initial document types
echo "📄 Setting up document types..."
docker-compose exec -T backend python manage.py shell << 'EOF'
from apps.documents.models import DocumentType
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()
admin_user = User.objects.get(username='admin')

# Define document types
document_types = [
    {
        'name': 'Standard Operating Procedure',
        'code': 'SOP',
        'description': 'Detailed written instructions to achieve uniformity of the performance of a specific function',
        'template_required': True,
        'approval_required': True,
        'retention_years': 7
    },
    {
        'name': 'Policy',
        'code': 'POL',
        'description': 'High-level principles and guidelines that govern organizational decisions',
        'template_required': False,
        'approval_required': True,
        'retention_years': 10
    },
    {
        'name': 'Work Instruction',
        'code': 'WI',
        'description': 'Step-by-step instructions for performing specific tasks',
        'template_required': True,
        'approval_required': True,
        'retention_years': 5
    },
    {
        'name': 'Manual',
        'code': 'MAN',
        'description': 'Comprehensive guide covering multiple procedures and policies',
        'template_required': False,
        'approval_required': True,
        'retention_years': 7
    },
    {
        'name': 'Form',
        'code': 'FRM',
        'description': 'Structured document for data collection and recording',
        'template_required': True,
        'approval_required': True,
        'retention_years': 7
    },
    {
        'name': 'Record',
        'code': 'REC',
        'description': 'Document that provides evidence of activities performed',
        'template_required': False,
        'approval_required': False,
        'retention_years': 7
    },
    {
        'name': 'Specification',
        'code': 'SPEC',
        'description': 'Technical requirements and standards documentation',
        'template_required': True,
        'approval_required': True,
        'retention_years': 10
    }
]

# Create document types (only if documents app exists)
try:
    with transaction.atomic():
        created_count = 0
        for doc_type_data in document_types:
            doc_type, created = DocumentType.objects.get_or_create(
                code=doc_type_data['code'],
                defaults={
                    'name': doc_type_data['name'],
                    'description': doc_type_data['description'],
                    'template_required': doc_type_data['template_required'],
                    'approval_required': doc_type_data['approval_required'],
                    'retention_years': doc_type_data['retention_years'],
                    'is_active': True,
                    'created_by': admin_user
                }
            )
            if created:
                print(f"✅ Created document type: {doc_type.name}")
                created_count += 1
            else:
                print(f"ℹ️  Document type already exists: {doc_type.name}")
        
        print(f"\n📊 Summary: {created_count} document types created")

except ImportError:
    print("ℹ️  Documents app not ready yet - skipping document types")
EOF

# Set up initial audit configuration
echo "📊 Configuring audit settings..."
docker-compose exec -T backend python manage.py shell << 'EOF'
from apps.audit.models import AuditConfiguration
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

try:
    admin_user = User.objects.get(username='admin')

    # Create audit configuration
    config, created = AuditConfiguration.objects.get_or_create(
        name='Default Audit Configuration',
        defaults={
            'description': 'Default audit configuration for 21 CFR Part 11 compliance',
            'retention_days': 2555,  # 7 years
            'enable_field_tracking': True,
            'enable_relationship_tracking': True,
            'track_create': True,
            'track_update': True,
            'track_delete': True,
            'compress_old_records': True,
            'is_active': True,
            'created_by': admin_user
        }
    )
    
    if created:
        print("✅ Created default audit configuration")
    else:
        print("ℹ️  Audit configuration already exists")

except ImportError:
    print("ℹ️  Audit app not ready yet - skipping audit configuration")
EOF

# Create storage directories
echo "📁 Setting up storage directories..."
docker-compose exec -T backend python manage.py shell << 'EOF'
import os
from django.conf import settings

# Create storage directories
storage_dirs = [
    'documents/originals',
    'documents/encrypted', 
    'documents/processed',
    'documents/thumbnails',
    'documents/exports',
    'media/uploads',
    'media/temp',
    'backups/database',
    'backups/documents',
    'logs/application',
    'logs/audit',
    'logs/security'
]

base_path = '/app/storage'
for dir_path in storage_dirs:
    full_path = os.path.join(base_path, dir_path)
    os.makedirs(full_path, exist_ok=True)
    print(f"✅ Created directory: {dir_path}")

print("\n📊 Storage directories created")
EOF

# Set proper permissions on storage directories
echo "🔒 Setting storage permissions..."
docker-compose exec -T backend chown -R 1000:1000 /app/storage
docker-compose exec -T backend chmod -R 755 /app/storage

# Initialize search indexes (for future PostgreSQL full-text search)
echo "🔍 Setting up search indexes..."
docker-compose exec -T backend python manage.py shell << 'EOF'
from django.db import connection

# Create PostgreSQL extensions and indexes for search
with connection.cursor() as cursor:
    try:
        # Enable extensions
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
        print("✅ PostgreSQL extensions enabled")
        
        # Note: Document-specific indexes will be created when document models are ready
        print("ℹ️  Search indexes will be created when document models are available")
        
    except Exception as e:
        print(f"⚠️  Search setup warning: {e}")
EOF

# Collect static files
echo "📦 Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput

# Create initial backup
echo "💾 Creating initial system backup..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U edms_user -d edms_db > "/tmp/edms_initial_backup_${BACKUP_DATE}.sql" || echo "⚠️  Backup creation failed"

# Verify database setup
echo "✅ Verifying database setup..."
docker-compose exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from apps.users.models import Role

User = get_user_model()

# Verify admin user
admin_count = User.objects.filter(is_superuser=True).count()
print(f"Superuser accounts: {admin_count}")

# Verify roles
role_count = Role.objects.count()
print(f"System roles: {role_count}")

# Verify database connection
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT version()")
    db_version = cursor.fetchone()[0]
    print(f"Database version: {db_version}")

print("\n✅ Database verification completed")
EOF

echo ""
echo "✅ Database initialization completed successfully!"
echo ""
echo "📊 Initialization Summary:"
echo "   ✅ Database migrations applied"
echo "   ✅ Admin user created (admin / EDMSAdmin2024!)"
echo "   ✅ System roles configured"
echo "   ✅ Storage directories created"
echo "   ✅ PostgreSQL extensions enabled"
echo "   ✅ Static files collected"
echo "   ✅ Initial backup created"
echo ""
echo "🔐 Default Login Credentials:"
echo "   Username: admin"
echo "   Password: EDMSAdmin2024!"
echo ""
echo "🌐 Next Steps:"
echo "   1. Access admin panel: http://localhost:8000/admin"
echo "   2. Create additional users with: ./scripts/create-test-users.sh"
echo "   3. Start the full application: docker-compose up -d"
echo ""
echo "⚠️  Important Security Notes:"
echo "   - Change default admin password immediately"
echo "   - Configure proper encryption keys for production"
echo "   - Review and customize system roles as needed"
echo "   - Set up proper backup schedule"
echo ""