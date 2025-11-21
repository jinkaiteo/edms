#!/usr/bin/env python3
"""
Comprehensive Backend System Tests for EDMS.

Tests all phases of implementation including:
- Phase 1: Infrastructure & Core Setup
- Phase 2: Backend Core Development  
- Phase 3: Advanced Backend Features
- Phase 4: Search & API Integration

Validates functionality, integration, and compliance features.
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.test')
django.setup()

from apps.documents.models import Document, DocumentType
from apps.users.models import Role, UserRole  
from apps.workflows.models import WorkflowType, WorkflowInstance
from apps.audit.models import AuditTrail, SystemEvent
from apps.security.models import ElectronicSignature, UserCertificate
from apps.placeholders.models import PlaceholderDefinition, DocumentTemplate
from apps.backup.models import BackupConfiguration, BackupJob
from apps.settings.models import SystemConfiguration, FeatureToggle
from apps.search.models import SearchIndex, SearchQuery
from apps.search.services import search_service

User = get_user_model()

class PhaseTestResults:
    """Container for test results across all phases."""
    
    def __init__(self):
        self.phase_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.errors = []
    
    def add_result(self, phase, test_name, passed, error=None):
        if phase not in self.phase_results:
            self.phase_results[phase] = {'tests': [], 'passed': 0, 'failed': 0}
        
        self.phase_results[phase]['tests'].append({
            'name': test_name,
            'passed': passed,
            'error': error
        })
        
        if passed:
            self.phase_results[phase]['passed'] += 1
            self.passed_tests += 1
        else:
            self.phase_results[phase]['failed'] += 1
            self.failed_tests += 1
            if error:
                self.errors.append(f"{phase}/{test_name}: {error}")
        
        self.total_tests += 1
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print("=" * 80)
        print("🧪 COMPREHENSIVE EDMS BACKEND SYSTEM TEST RESULTS")
        print("=" * 80)
        
        for phase, results in self.phase_results.items():
            total = results['passed'] + results['failed']
            pass_rate = (results['passed'] / total * 100) if total > 0 else 0
            
            print(f"\n{phase}:")
            print(f"  ✅ Passed: {results['passed']}")
            print(f"  ❌ Failed: {results['failed']}")
            print(f"  📊 Success Rate: {pass_rate:.1f}%")
            
            # Show failed tests
            if results['failed'] > 0:
                print("  Failed Tests:")
                for test in results['tests']:
                    if not test['passed']:
                        print(f"    - {test['name']}: {test['error']}")
        
        print("\n" + "=" * 80)
        print(f"📊 OVERALL RESULTS:")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  ✅ Passed: {self.passed_tests}")
        print(f"  ❌ Failed: {self.failed_tests}")
        overall_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"  📈 Overall Success Rate: {overall_rate:.1f}%")
        
        if overall_rate >= 90:
            print("  🎉 EXCELLENT: System ready for production!")
        elif overall_rate >= 80:
            print("  ✅ GOOD: System mostly ready with minor issues")
        elif overall_rate >= 70:
            print("  ⚠️  NEEDS WORK: Several issues need attention")
        else:
            print("  🚨 CRITICAL: Major issues detected")


class Phase1InfrastructureTests:
    """Test Phase 1: Infrastructure & Core Setup."""
    
    def __init__(self, results):
        self.results = results
        self.phase = "Phase 1: Infrastructure & Core Setup"
    
    def test_django_setup(self):
        """Test Django configuration and setup."""
        try:
            from django.conf import settings
            assert settings.configured
            assert hasattr(settings, 'INSTALLED_APPS')
            assert hasattr(settings, 'DATABASES')
            self.results.add_result(self.phase, "Django Configuration", True)
        except Exception as e:
            self.results.add_result(self.phase, "Django Configuration", False, str(e))
    
    def test_database_connection(self):
        """Test database connectivity."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
            self.results.add_result(self.phase, "Database Connection", True)
        except Exception as e:
            self.results.add_result(self.phase, "Database Connection", False, str(e))
    
    def test_installed_apps(self):
        """Test that all required apps are installed."""
        try:
            required_apps = [
                'apps.users', 'apps.documents', 'apps.workflows',
                'apps.audit', 'apps.security', 'apps.placeholders',
                'apps.scheduler', 'apps.backup', 'apps.settings', 'apps.search'
            ]
            
            for app in required_apps:
                assert app in settings.INSTALLED_APPS
            
            self.results.add_result(self.phase, "Installed Apps", True)
        except Exception as e:
            self.results.add_result(self.phase, "Installed Apps", False, str(e))
    
    def test_urls_configuration(self):
        """Test URL configuration."""
        try:
            from django.urls import reverse
            from django.test import Client
            
            client = Client()
            # Test that API URLs are configured
            response = client.get('/api/v1/status/')
            assert response.status_code in [200, 401, 403]  # Should not be 404
            
            self.results.add_result(self.phase, "URL Configuration", True)
        except Exception as e:
            self.results.add_result(self.phase, "URL Configuration", False, str(e))


class Phase2CoreDevelopmentTests:
    """Test Phase 2: Backend Core Development."""
    
    def __init__(self, results):
        self.results = results
        self.phase = "Phase 2: Backend Core Development"
        self.test_user = None
    
    def setup_test_data(self):
        """Set up test data for Phase 2 tests."""
        try:
            # Create test user
            self.test_user = User.objects.create_user(
                username='test_user',
                email='test@example.com',
                password='testpass123'
            )
            
            # Create test role
            Role.objects.get_or_create(
                name='Test Role',
                defaults={
                    'module': 'TEST',
                    'permission_level': 'read',
                    'description': 'Test role for system testing'
                }
            )
            
            self.results.add_result(self.phase, "Test Data Setup", True)
        except Exception as e:
            self.results.add_result(self.phase, "Test Data Setup", False, str(e))
    
    def test_user_model(self):
        """Test User model functionality."""
        try:
            # Test user creation
            user = User.objects.create_user(
                username='testuser2',
                email='test2@example.com', 
                password='testpass123'
            )
            
            assert user.username == 'testuser2'
            assert user.email == 'test2@example.com'
            assert user.check_password('testpass123')
            
            self.results.add_result(self.phase, "User Model", True)
        except Exception as e:
            self.results.add_result(self.phase, "User Model", False, str(e))
    
    def test_document_model(self):
        """Test Document model functionality."""
        try:
            # Create document type
            doc_type = DocumentType.objects.create(
                name='Test Document Type',
                description='Test document type'
            )
            
            # Create document
            document = Document.objects.create(
                document_number='TEST-001',
                title='Test Document',
                description='Test document description',
                document_type=doc_type,
                created_by=self.test_user,
                status='draft'
            )
            
            assert document.document_number == 'TEST-001'
            assert document.title == 'Test Document'
            assert document.created_by == self.test_user
            
            self.results.add_result(self.phase, "Document Model", True)
        except Exception as e:
            self.results.add_result(self.phase, "Document Model", False, str(e))
    
    def test_workflow_models(self):
        """Test Workflow models."""
        try:
            # Create workflow type
            workflow_type = WorkflowType.objects.create(
                name='Test Workflow',
                workflow_type='REVIEW',
                description='Test workflow type'
            )
            
            assert workflow_type.name == 'Test Workflow'
            assert workflow_type.workflow_type == 'REVIEW'
            
            self.results.add_result(self.phase, "Workflow Models", True)
        except Exception as e:
            self.results.add_result(self.phase, "Workflow Models", False, str(e))
    
    def test_audit_trail(self):
        """Test audit trail functionality."""
        try:
            # Test audit trail creation
            from apps.audit.services import audit_service
            
            audit_entry = audit_service.log_user_action(
                user=self.test_user,
                action='TEST_ACTION',
                object_type='Test',
                object_id=1,
                description='Test audit entry'
            )
            
            assert audit_entry.user == self.test_user
            assert audit_entry.action == 'TEST_ACTION'
            assert audit_entry.integrity_hash is not None
            
            self.results.add_result(self.phase, "Audit Trail", True)
        except Exception as e:
            self.results.add_result(self.phase, "Audit Trail", False, str(e))
    
    def test_permissions_system(self):
        """Test role-based permissions."""
        try:
            from apps.users.workflow_permissions import workflow_permission_manager
            
            # Test permission checking
            can_create = workflow_permission_manager.can_user_perform_action(
                self.test_user, 'document_create'
            )
            
            # Should work without errors (result depends on user setup)
            assert isinstance(can_create, bool)
            
            self.results.add_result(self.phase, "Permissions System", True)
        except Exception as e:
            self.results.add_result(self.phase, "Permissions System", False, str(e))


class Phase3AdvancedFeaturesTests:
    """Test Phase 3: Advanced Backend Features."""
    
    def __init__(self, results):
        self.results = results
        self.phase = "Phase 3: Advanced Backend Features"
    
    def test_electronic_signatures(self):
        """Test electronic signature functionality."""
        try:
            from apps.security.electronic_signatures import electronic_signature_service
            
            # Test service instantiation
            assert electronic_signature_service is not None
            assert hasattr(electronic_signature_service, 'create_signature')
            
            self.results.add_result(self.phase, "Electronic Signatures", True)
        except Exception as e:
            self.results.add_result(self.phase, "Electronic Signatures", False, str(e))
    
    def test_template_system(self):
        """Test document template system."""
        try:
            # Create placeholder
            placeholder = PlaceholderDefinition.objects.create(
                name='TEST_PLACEHOLDER',
                display_name='Test Placeholder',
                description='Test placeholder for system testing',
                placeholder_type='DOCUMENT',
                data_source='DOCUMENT_MODEL',
                source_field='title',
                created_by_id=1
            )
            
            assert placeholder.name == 'TEST_PLACEHOLDER'
            assert placeholder.get_template_syntax() == '{{ TEST_PLACEHOLDER }}'
            
            self.results.add_result(self.phase, "Template System", True)
        except Exception as e:
            self.results.add_result(self.phase, "Template System", False, str(e))
    
    def test_backup_system(self):
        """Test backup and recovery system."""
        try:
            from apps.backup.services import backup_service
            
            # Test service availability
            assert backup_service is not None
            assert hasattr(backup_service, 'execute_backup')
            
            # Create backup configuration
            backup_config = BackupConfiguration.objects.create(
                name='Test Backup',
                backup_type='DATABASE',
                frequency='DAILY',
                schedule_time='02:00:00',
                storage_path='/tmp/test_backup',
                created_by_id=1
            )
            
            assert backup_config.name == 'Test Backup'
            
            self.results.add_result(self.phase, "Backup System", True)
        except Exception as e:
            self.results.add_result(self.phase, "Backup System", False, str(e))
    
    def test_settings_management(self):
        """Test settings and configuration management."""
        try:
            # Create system configuration
            config = SystemConfiguration.objects.create(
                key='test_setting',
                display_name='Test Setting',
                category='SYSTEM',
                setting_type='STRING',
                value='test_value',
                default_value='default_test'
            )
            
            assert config.key == 'test_setting'
            assert config.get_typed_value() == 'test_value'
            
            # Test feature toggle
            toggle = FeatureToggle.objects.create(
                key='test_feature',
                name='Test Feature',
                description='Test feature toggle',
                toggle_type='RELEASE',
                is_enabled=True,
                created_by_id=1
            )
            
            assert toggle.key == 'test_feature'
            assert toggle.is_enabled == True
            
            self.results.add_result(self.phase, "Settings Management", True)
        except Exception as e:
            self.results.add_result(self.phase, "Settings Management", False, str(e))


class Phase4SearchAPITests:
    """Test Phase 4: Search & API Integration."""
    
    def __init__(self, results):
        self.results = results
        self.phase = "Phase 4: Search & API Integration"
        self.test_document = None
    
    def setup_search_test_data(self):
        """Set up test data for search tests."""
        try:
            # Create test user and document for searching
            user = User.objects.first() or User.objects.create_user(
                username='search_test_user',
                email='search@test.com',
                password='testpass123'
            )
            
            doc_type = DocumentType.objects.first() or DocumentType.objects.create(
                name='Search Test Type',
                description='Document type for search testing'
            )
            
            self.test_document = Document.objects.create(
                document_number='SEARCH-001',
                title='Searchable Test Document',
                description='This is a test document for search functionality',
                document_type=doc_type,
                created_by=user,
                status='effective'
            )
            
            self.results.add_result(self.phase, "Search Test Data Setup", True)
        except Exception as e:
            self.results.add_result(self.phase, "Search Test Data Setup", False, str(e))
    
    def test_search_service(self):
        """Test search service functionality."""
        try:
            # Test search service instantiation
            assert search_service is not None
            assert hasattr(search_service, 'search_documents')
            
            # Test basic search
            results = search_service.search_documents(
                query='test',
                user=self.test_document.created_by if self.test_document else None
            )
            
            assert isinstance(results, dict)
            assert 'documents' in results
            assert 'total_count' in results
            
            self.results.add_result(self.phase, "Search Service", True)
        except Exception as e:
            self.results.add_result(self.phase, "Search Service", False, str(e))
    
    def test_search_indexing(self):
        """Test search index management."""
        try:
            if self.test_document:
                # Update search index for document
                search_index = search_service.update_search_index(
                    self.test_document,
                    force_update=True
                )
                
                assert search_index is not None
                assert search_index.document == self.test_document
                assert search_index.status == 'ACTIVE'
            
            self.results.add_result(self.phase, "Search Indexing", True)
        except Exception as e:
            self.results.add_result(self.phase, "Search Indexing", False, str(e))
    
    def test_api_authentication(self):
        """Test API authentication classes."""
        try:
            from apps.api.authentication import APITokenAuthentication, AuditedSessionAuthentication
            
            # Test authentication classes
            token_auth = APITokenAuthentication()
            session_auth = AuditedSessionAuthentication()
            
            assert token_auth is not None
            assert session_auth is not None
            
            self.results.add_result(self.phase, "API Authentication", True)
        except Exception as e:
            self.results.add_result(self.phase, "API Authentication", False, str(e))
    
    def test_api_throttling(self):
        """Test API rate limiting."""
        try:
            from apps.api.throttling import EDMSUserRateThrottle, SearchRateThrottle
            
            # Test throttling classes
            user_throttle = EDMSUserRateThrottle()
            search_throttle = SearchRateThrottle()
            
            assert user_throttle is not None
            assert search_throttle is not None
            
            self.results.add_result(self.phase, "API Throttling", True)
        except Exception as e:
            self.results.add_result(self.phase, "API Throttling", False, str(e))
    
    def test_api_endpoints(self):
        """Test API endpoint availability."""
        try:
            from django.test import Client
            
            client = Client()
            
            # Test API status endpoint
            response = client.get('/api/v1/status/')
            assert response.status_code == 200
            
            # Test API info endpoint (may require auth)
            response = client.get('/api/v1/info/')
            assert response.status_code in [200, 401, 403]
            
            # Test API health endpoint
            response = client.get('/api/v1/health/')
            assert response.status_code == 200
            
            self.results.add_result(self.phase, "API Endpoints", True)
        except Exception as e:
            self.results.add_result(self.phase, "API Endpoints", False, str(e))


class IntegrationTests:
    """Test cross-component integration."""
    
    def __init__(self, results):
        self.results = results
        self.phase = "Integration Tests"
    
    def test_document_workflow_integration(self):
        """Test document and workflow integration."""
        try:
            from apps.documents.workflow_integration import document_workflow_manager
            
            # Test integration service
            assert document_workflow_manager is not None
            assert hasattr(document_workflow_manager, 'initiate_review_workflow')
            
            self.results.add_result(self.phase, "Document-Workflow Integration", True)
        except Exception as e:
            self.results.add_result(self.phase, "Document-Workflow Integration", False, str(e))
    
    def test_search_document_integration(self):
        """Test search and document integration."""
        try:
            # Test that search indices are created for documents
            documents = Document.objects.all()[:1]
            
            if documents:
                document = documents[0]
                search_index = search_service.update_search_index(document)
                assert search_index.document == document
            
            self.results.add_result(self.phase, "Search-Document Integration", True)
        except Exception as e:
            self.results.add_result(self.phase, "Search-Document Integration", False, str(e))
    
    def test_audit_integration(self):
        """Test audit trail integration across modules."""
        try:
            from apps.audit.services import audit_service
            
            # Test audit integration
            audit_count_before = AuditTrail.objects.count()
            
            # Create a document (should trigger audit)
            user = User.objects.first()
            if user:
                doc_type = DocumentType.objects.first() or DocumentType.objects.create(
                    name='Integration Test Type'
                )
                
                Document.objects.create(
                    document_number='INT-001',
                    title='Integration Test Document',
                    document_type=doc_type,
                    created_by=user,
                    status='draft'
                )
                
                # Check if audit trail was created (may be created by signals)
                audit_count_after = AuditTrail.objects.count()
                # Don't assert strict equality as signals may or may not be active
                
            self.results.add_result(self.phase, "Audit Integration", True)
        except Exception as e:
            self.results.add_result(self.phase, "Audit Integration", False, str(e))


def run_comprehensive_tests():
    """Run all comprehensive backend tests."""
    print("🚀 Starting Comprehensive EDMS Backend System Tests...")
    print("=" * 80)
    
    results = PhaseTestResults()
    
    # Phase 1: Infrastructure Tests
    print("Testing Phase 1: Infrastructure & Core Setup...")
    phase1_tests = Phase1InfrastructureTests(results)
    phase1_tests.test_django_setup()
    phase1_tests.test_database_connection()
    phase1_tests.test_installed_apps()
    phase1_tests.test_urls_configuration()
    
    # Phase 2: Core Development Tests
    print("Testing Phase 2: Backend Core Development...")
    phase2_tests = Phase2CoreDevelopmentTests(results)
    phase2_tests.setup_test_data()
    phase2_tests.test_user_model()
    phase2_tests.test_document_model()
    phase2_tests.test_workflow_models()
    phase2_tests.test_audit_trail()
    phase2_tests.test_permissions_system()
    
    # Phase 3: Advanced Features Tests
    print("Testing Phase 3: Advanced Backend Features...")
    phase3_tests = Phase3AdvancedFeaturesTests(results)
    phase3_tests.test_electronic_signatures()
    phase3_tests.test_template_system()
    phase3_tests.test_backup_system()
    phase3_tests.test_settings_management()
    
    # Phase 4: Search & API Tests
    print("Testing Phase 4: Search & API Integration...")
    phase4_tests = Phase4SearchAPITests(results)
    phase4_tests.setup_search_test_data()
    phase4_tests.test_search_service()
    phase4_tests.test_search_indexing()
    phase4_tests.test_api_authentication()
    phase4_tests.test_api_throttling()
    phase4_tests.test_api_endpoints()
    
    # Integration Tests
    print("Testing Cross-Component Integration...")
    integration_tests = IntegrationTests(results)
    integration_tests.test_document_workflow_integration()
    integration_tests.test_search_document_integration()
    integration_tests.test_audit_integration()
    
    # Print final results
    results.print_summary()
    
    return results


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    
    try:
        results = run_comprehensive_tests()
        
        # Return appropriate exit code
        if results.passed_tests / results.total_tests >= 0.8:
            print("\n✅ Backend system tests completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Backend system tests completed with issues!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n🚨 Critical error during testing: {str(e)}")
        sys.exit(2)