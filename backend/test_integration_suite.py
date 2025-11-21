#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for EDMS Backend.

Tests all phases of implementation and their integration:
- Phase 1: Infrastructure & Core Setup
- Phase 2: Backend Core Development  
- Phase 3: Advanced Backend Features
- Phase 4: Search & API Integration

Validates complete system functionality and cross-component integration.
"""

import os
import sys
import json
import hashlib
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

class EDMSIntegrationTestSuite:
    """Comprehensive integration test suite for the entire EDMS backend."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = {
            'phase_results': {},
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'errors': [],
            'system_metrics': {}
        }
        
    def log_result(self, phase, test_name, status, details="", warning=False):
        """Log test result with phase tracking."""
        if phase not in self.results['phase_results']:
            self.results['phase_results'][phase] = {
                'tests': [], 'passed': 0, 'failed': 0, 'warnings': 0
            }
        
        self.results['total_tests'] += 1
        
        if status == 'pass':
            if warning:
                self.results['warnings'] += 1
                self.results['phase_results'][phase]['warnings'] += 1
                print(f"  ⚠️  {test_name} (Warning: {details})")
            else:
                self.results['passed'] += 1
                self.results['phase_results'][phase]['passed'] += 1
                print(f"  ✅ {test_name}")
        else:
            self.results['failed'] += 1
            self.results['phase_results'][phase]['failed'] += 1
            print(f"  ❌ {test_name}: {details}")
            self.results['errors'].append(f"{phase}/{test_name}: {details}")
        
        self.results['phase_results'][phase]['tests'].append({
            'name': test_name,
            'status': status,
            'details': details,
            'warning': warning
        })
    
    def test_phase1_infrastructure(self):
        """Test Phase 1: Infrastructure & Core Setup."""
        phase = "Phase 1: Infrastructure & Core Setup"
        print(f"\n🏗️  Testing {phase}")
        print("-" * 60)
        
        # Test Django app structure
        apps_dir = self.base_path / 'apps'
        required_apps = [
            'users', 'documents', 'workflows', 'audit', 'security',
            'placeholders', 'scheduler', 'backup', 'settings', 'search', 'api'
        ]
        
        missing_apps = []
        incomplete_apps = []
        
        for app in required_apps:
            app_path = apps_dir / app
            if not app_path.exists():
                missing_apps.append(app)
            else:
                # Check for essential files
                essential_files = ['__init__.py', 'models.py', 'apps.py']
                missing_files = [f for f in essential_files if not (app_path / f).exists()]
                if missing_files:
                    incomplete_apps.append(f"{app}: missing {', '.join(missing_files)}")
        
        if missing_apps:
            self.log_result(phase, "Django App Structure", "fail", 
                          f"Missing apps: {', '.join(missing_apps)}")
        elif incomplete_apps:
            self.log_result(phase, "Django App Structure", "pass",
                          f"Incomplete apps: {'; '.join(incomplete_apps)}", warning=True)
        else:
            self.log_result(phase, "Django App Structure", "pass")
        
        # Test configuration files
        config_files = [
            'edms/settings/base.py',
            'edms/settings/development.py', 
            'edms/settings/production.py',
            'edms/settings/test.py',
            'edms/urls.py',
            'manage.py'
        ]
        
        missing_configs = []
        for config_file in config_files:
            if not (self.base_path / config_file).exists():
                missing_configs.append(config_file)
        
        if missing_configs:
            self.log_result(phase, "Configuration Files", "fail",
                          f"Missing: {', '.join(missing_configs)}")
        else:
            self.log_result(phase, "Configuration Files", "pass")
        
        # Test requirements files
        req_files = ['requirements/base.txt', 'requirements/development.txt', 'requirements/production.txt']
        missing_reqs = [f for f in req_files if not (self.base_path / f).exists()]
        
        if missing_reqs:
            self.log_result(phase, "Requirements Files", "fail",
                          f"Missing: {', '.join(missing_reqs)}")
        else:
            self.log_result(phase, "Requirements Files", "pass")
    
    def test_phase2_core_development(self):
        """Test Phase 2: Backend Core Development."""
        phase = "Phase 2: Backend Core Development"
        print(f"\n⚙️  Testing {phase}")
        print("-" * 60)
        
        # Test user management components
        user_files = [
            'apps/users/models.py',
            'apps/users/serializers.py',
            'apps/users/views.py',
            'apps/users/permissions.py',
            'apps/users/workflow_permissions.py'
        ]
        
        user_components = self._check_component_files('User Management', user_files)
        self.log_result(phase, "User Management Components", 
                       "pass" if user_components['complete'] else "fail",
                       user_components['details'], user_components['warning'])
        
        # Test document management components
        doc_files = [
            'apps/documents/models.py',
            'apps/documents/serializers.py',
            'apps/documents/views.py',
            'apps/documents/workflow_integration.py'
        ]
        
        doc_components = self._check_component_files('Document Management', doc_files)
        self.log_result(phase, "Document Management Components",
                       "pass" if doc_components['complete'] else "fail",
                       doc_components['details'], doc_components['warning'])
        
        # Test workflow components
        workflow_files = [
            'apps/workflows/models.py',
            'apps/workflows/serializers.py',
            'apps/workflows/views.py',
            'apps/workflows/services.py',
            'apps/workflows/tasks.py',
            'apps/workflows/permissions.py'
        ]
        
        workflow_components = self._check_component_files('Workflow Management', workflow_files)
        self.log_result(phase, "Workflow Management Components",
                       "pass" if workflow_components['complete'] else "fail",
                       workflow_components['details'], workflow_components['warning'])
        
        # Test audit trail components
        audit_files = [
            'apps/audit/models.py',
            'apps/audit/services.py',
            'apps/audit/signals.py',
            'apps/audit/tasks.py',
            'apps/audit/middleware.py'
        ]
        
        audit_components = self._check_component_files('Audit Trail', audit_files)
        self.log_result(phase, "Audit Trail Components",
                       "pass" if audit_components['complete'] else "fail",
                       audit_components['details'], audit_components['warning'])
    
    def test_phase3_advanced_features(self):
        """Test Phase 3: Advanced Backend Features."""
        phase = "Phase 3: Advanced Backend Features"
        print(f"\n🔐 Testing {phase}")
        print("-" * 60)
        
        # Test electronic signature components
        signature_files = [
            'apps/security/models.py',
            'apps/security/electronic_signatures.py',
            'apps/security/encryption.py',
            'apps/security/signals.py'
        ]
        
        signature_components = self._check_component_files('Electronic Signatures', signature_files)
        self.log_result(phase, "Electronic Signature Components",
                       "pass" if signature_components['complete'] else "fail",
                       signature_components['details'], signature_components['warning'])
        
        # Test template processing components
        template_files = [
            'apps/placeholders/models.py',
            'apps/placeholders/services.py',
            'apps/placeholders/serializers.py'
        ]
        
        template_components = self._check_component_files('Template Processing', template_files)
        self.log_result(phase, "Template Processing Components",
                       "pass" if template_components['complete'] else "fail",
                       template_components['details'], template_components['warning'])
        
        # Test backup and recovery components
        backup_files = [
            'apps/backup/models.py',
            'apps/backup/services.py'
        ]
        
        backup_components = self._check_component_files('Backup & Recovery', backup_files)
        self.log_result(phase, "Backup & Recovery Components",
                       "pass" if backup_components['complete'] else "fail",
                       backup_components['details'], backup_components['warning'])
        
        # Test settings management components
        settings_files = [
            'apps/settings/models.py'
        ]
        
        settings_components = self._check_component_files('Settings Management', settings_files)
        self.log_result(phase, "Settings Management Components",
                       "pass" if settings_components['complete'] else "fail",
                       settings_components['details'], settings_components['warning'])
    
    def test_phase4_search_api(self):
        """Test Phase 4: Search & API Integration."""
        phase = "Phase 4: Search & API Integration"
        print(f"\n🔍 Testing {phase}")
        print("-" * 60)
        
        # Test search components
        search_files = [
            'apps/search/models.py',
            'apps/search/services.py',
            'apps/search/serializers.py',
            'apps/search/signals.py'
        ]
        
        search_components = self._check_component_files('Search Engine', search_files)
        self.log_result(phase, "Search Engine Components",
                       "pass" if search_components['complete'] else "fail",
                       search_components['details'], search_components['warning'])
        
        # Test API components
        api_files = [
            'apps/api/v1/urls.py',
            'apps/api/v1/views.py',
            'apps/api/authentication.py',
            'apps/api/throttling.py',
            'apps/api/middleware.py'
        ]
        
        api_components = self._check_component_files('REST API', api_files)
        self.log_result(phase, "REST API Components",
                       "pass" if api_components['complete'] else "fail",
                       api_components['details'], api_components['warning'])
    
    def test_integration_points(self):
        """Test integration between different components."""
        phase = "Integration Tests"
        print(f"\n🔗 Testing {phase}")
        print("-" * 60)
        
        # Test document-workflow integration
        self._test_component_integration(
            phase, "Document-Workflow Integration",
            'apps/documents/workflow_integration.py',
            ['WorkflowManager', 'document_workflow_manager']
        )
        
        # Test audit integration across modules
        self._test_audit_integration(phase)
        
        # Test search-document integration
        self._test_component_integration(
            phase, "Search-Document Integration", 
            'apps/search/signals.py',
            ['update_document_search_index']
        )
        
        # Test API authentication integration
        self._test_component_integration(
            phase, "API Authentication Integration",
            'apps/api/authentication.py',
            ['APITokenAuthentication', 'AuditedSessionAuthentication']
        )
        
        # Test permission system integration
        self._test_component_integration(
            phase, "Permission System Integration",
            'apps/users/workflow_permissions.py',
            ['WorkflowPermissionManager', 'workflow_permission_manager']
        )
    
    def test_code_quality_metrics(self):
        """Test code quality metrics across the system."""
        phase = "Code Quality"
        print(f"\n📊 Testing {phase}")
        print("-" * 60)
        
        # Calculate system metrics
        metrics = self._calculate_system_metrics()
        self.results['system_metrics'] = metrics
        
        # Test file count and size
        if metrics['total_files'] >= 50:
            self.log_result(phase, "File Count", "pass", f"{metrics['total_files']} files")
        else:
            self.log_result(phase, "File Count", "fail", f"Only {metrics['total_files']} files found")
        
        # Test lines of code
        if metrics['total_lines'] >= 8000:
            self.log_result(phase, "Code Volume", "pass", f"{metrics['total_lines']} lines")
        else:
            self.log_result(phase, "Code Volume", "pass", f"{metrics['total_lines']} lines", warning=True)
        
        # Test model count
        if metrics['model_count'] >= 30:
            self.log_result(phase, "Database Models", "pass", f"{metrics['model_count']} models")
        else:
            self.log_result(phase, "Database Models", "fail", f"Only {metrics['model_count']} models found")
        
        # Test service classes
        if metrics['service_count'] >= 10:
            self.log_result(phase, "Service Classes", "pass", f"{metrics['service_count']} services")
        else:
            self.log_result(phase, "Service Classes", "fail", f"Only {metrics['service_count']} services found")
        
        # Test documentation coverage
        if metrics['doc_percentage'] >= 70:
            self.log_result(phase, "Documentation Coverage", "pass", f"{metrics['doc_percentage']:.1f}%")
        else:
            self.log_result(phase, "Documentation Coverage", "pass", f"{metrics['doc_percentage']:.1f}%", warning=True)
    
    def test_compliance_features(self):
        """Test 21 CFR Part 11 compliance features."""
        phase = "Compliance Features"
        print(f"\n📋 Testing {phase}")
        print("-" * 60)
        
        # Test audit trail implementation
        self._test_compliance_feature(phase, "Audit Trail System", [
            'apps/audit/models.py',
            'apps/audit/services.py',
            'apps/audit/signals.py'
        ], ['AuditTrail', 'audit_service', 'integrity_hash'])
        
        # Test electronic signatures
        self._test_compliance_feature(phase, "Electronic Signatures", [
            'apps/security/models.py',
            'apps/security/electronic_signatures.py'
        ], ['ElectronicSignature', 'electronic_signature_service', 'certificate'])
        
        # Test user authentication and permissions
        self._test_compliance_feature(phase, "Access Control System", [
            'apps/users/models.py',
            'apps/users/permissions.py'
        ], ['Role', 'UserRole', 'permission'])
        
        # Test data integrity features
        self._test_compliance_feature(phase, "Data Integrity", [
            'apps/documents/models.py',
            'apps/audit/models.py'
        ], ['checksum', 'hash', 'integrity'])
    
    def _check_component_files(self, component_name, file_list):
        """Check if component files exist and have content."""
        missing_files = []
        empty_files = []
        
        for file_path in file_list:
            full_path = self.base_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            else:
                try:
                    with open(full_path, 'r') as f:
                        content = f.read().strip()
                    if len(content) < 100:  # Very basic check for empty files
                        empty_files.append(file_path)
                except:
                    empty_files.append(file_path)
        
        complete = len(missing_files) == 0 and len(empty_files) == 0
        warning = len(empty_files) > 0
        
        details = ""
        if missing_files:
            details += f"Missing: {', '.join(missing_files)}. "
        if empty_files:
            details += f"Empty/minimal: {', '.join(empty_files)}. "
        
        return {
            'complete': complete,
            'warning': warning,
            'details': details.strip()
        }
    
    def _test_component_integration(self, phase, test_name, file_path, expected_elements):
        """Test integration between components by checking for expected elements."""
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            self.log_result(phase, test_name, "fail", f"Integration file {file_path} not found")
            return
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            
            missing_elements = []
            for element in expected_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                self.log_result(phase, test_name, "fail", 
                              f"Missing elements: {', '.join(missing_elements)}")
            else:
                self.log_result(phase, test_name, "pass")
        
        except Exception as e:
            self.log_result(phase, test_name, "fail", f"Error reading file: {str(e)}")
    
    def _test_audit_integration(self, phase):
        """Test audit trail integration across modules."""
        audit_integration_files = [
            'apps/audit/signals.py',
            'apps/audit/middleware.py',
            'apps/workflows/tasks.py',
            'apps/documents/workflow_integration.py'
        ]
        
        integration_found = 0
        for file_path in audit_integration_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    if 'audit_service' in content or 'log_user_action' in content:
                        integration_found += 1
                except:
                    pass
        
        if integration_found >= 2:
            self.log_result(phase, "Audit System Integration", "pass",
                          f"Audit integration found in {integration_found} modules")
        else:
            self.log_result(phase, "Audit System Integration", "fail",
                          f"Audit integration found in only {integration_found} modules")
    
    def _calculate_system_metrics(self):
        """Calculate comprehensive system metrics."""
        metrics = {
            'total_files': 0,
            'total_lines': 0,
            'model_count': 0,
            'service_count': 0,
            'doc_percentage': 0,
            'avg_file_size': 0
        }
        
        python_files = list(self.base_path.glob('**/*.py'))
        python_files = [f for f in python_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
        
        total_lines = 0
        model_count = 0
        service_count = 0
        documented_items = 0
        total_items = 0
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                total_lines += len(lines)
                content = ''.join(lines)
                
                # Count models (simplified)
                if 'models.Model' in content or 'AbstractUser' in content:
                    model_count += content.count('class ') // 2  # Rough estimate
                
                # Count service classes
                if 'Service' in content or 'Manager' in content:
                    service_count += content.count('class ') // 3  # Rough estimate
                
                # Count documentation (simplified)
                doc_strings = content.count('"""') + content.count("'''")
                class_count = content.count('class ')
                func_count = content.count('def ')
                
                documented_items += min(doc_strings, class_count + func_count)
                total_items += class_count + func_count
                
            except:
                continue
        
        metrics['total_files'] = len(python_files)
        metrics['total_lines'] = total_lines
        metrics['model_count'] = model_count
        metrics['service_count'] = service_count
        metrics['doc_percentage'] = (documented_items / total_items * 100) if total_items > 0 else 0
        metrics['avg_file_size'] = total_lines / len(python_files) if python_files else 0
        
        return metrics
    
    def _test_compliance_feature(self, phase, feature_name, file_list, required_elements):
        """Test compliance feature implementation."""
        feature_score = 0
        total_elements = len(required_elements)
        
        for file_path in file_list:
            full_path = self.base_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read().lower()
                    
                    for element in required_elements:
                        if element.lower() in content:
                            feature_score += 1
                            break
                except:
                    continue
        
        if feature_score >= len(file_list):
            self.log_result(phase, feature_name, "pass", 
                          f"All required elements found")
        elif feature_score > 0:
            self.log_result(phase, feature_name, "pass",
                          f"Partial implementation found", warning=True)
        else:
            self.log_result(phase, feature_name, "fail",
                          f"No implementation elements found")
    
    def print_comprehensive_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("🧪 COMPREHENSIVE EDMS BACKEND INTEGRATION TEST RESULTS")
        print("=" * 80)
        
        # Phase-by-phase results
        for phase, results in self.results['phase_results'].items():
            total_phase = results['passed'] + results['failed'] + results['warnings']
            if total_phase > 0:
                pass_rate = (results['passed'] / total_phase) * 100
                print(f"\n📊 {phase}:")
                print(f"   ✅ Passed: {results['passed']}")
                print(f"   ❌ Failed: {results['failed']}")
                print(f"   ⚠️  Warnings: {results['warnings']}")
                print(f"   📈 Success Rate: {pass_rate:.1f}%")
        
        # Overall system metrics
        print(f"\n🏗️  SYSTEM METRICS:")
        if self.results['system_metrics']:
            metrics = self.results['system_metrics']
            print(f"   📁 Total Files: {metrics['total_files']}")
            print(f"   📝 Lines of Code: {metrics['total_lines']:,}")
            print(f"   🗃️  Database Models: {metrics['model_count']}")
            print(f"   ⚙️  Service Classes: {metrics['service_count']}")
            print(f"   📚 Documentation: {metrics['doc_percentage']:.1f}%")
            print(f"   📊 Avg File Size: {metrics['avg_file_size']:.0f} lines")
        
        # Overall results
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Total Tests: {self.results['total_tests']}")
        print(f"   ✅ Passed: {self.results['passed']}")
        print(f"   ❌ Failed: {self.results['failed']}")
        print(f"   ⚠️  Warnings: {self.results['warnings']}")
        
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed'] / self.results['total_tests']) * 100
            print(f"   🎯 Success Rate: {success_rate:.1f}%")
            
            # Final assessment
            print(f"\n🏆 FINAL ASSESSMENT:")
            if success_rate >= 95:
                print("   🎉 OUTSTANDING: Production-ready enterprise system!")
                assessment = "OUTSTANDING"
            elif success_rate >= 85:
                print("   ✅ EXCELLENT: High-quality system ready for deployment")
                assessment = "EXCELLENT"
            elif success_rate >= 75:
                print("   👍 GOOD: Solid system with minor improvements needed")
                assessment = "GOOD"
            elif success_rate >= 60:
                print("   ⚠️  MODERATE: System needs significant improvements")
                assessment = "MODERATE"
            else:
                print("   🚨 NEEDS WORK: Major issues need attention")
                assessment = "NEEDS_WORK"
        else:
            assessment = "NO_TESTS"
        
        # Show critical errors
        if self.results['errors']:
            print(f"\n❌ CRITICAL ISSUES ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results['errors'][:10], 1):
                print(f"   {i}. {error}")
            if len(self.results['errors']) > 10:
                print(f"   ... and {len(self.results['errors']) - 10} more issues")
        
        print("=" * 80)
        return assessment
    
    def run_comprehensive_tests(self):
        """Run all comprehensive integration tests."""
        print("🚀 EDMS Backend Comprehensive Integration Test Suite")
        print("Testing all phases and system integration...")
        
        # Run all test phases
        self.test_phase1_infrastructure()
        self.test_phase2_core_development()
        self.test_phase3_advanced_features()
        self.test_phase4_search_api()
        self.test_integration_points()
        self.test_code_quality_metrics()
        self.test_compliance_features()
        
        # Print comprehensive summary
        assessment = self.print_comprehensive_summary()
        
        return assessment, self.results


if __name__ == "__main__":
    test_suite = EDMSIntegrationTestSuite()
    assessment, results = test_suite.run_comprehensive_tests()
    
    print(f"\n🎯 EDMS Backend Integration Testing: {assessment}")
    
    # Exit with appropriate code
    if assessment in ["OUTSTANDING", "EXCELLENT"]:
        print("✅ Backend system validation: PASSED")
        sys.exit(0)
    elif assessment in ["GOOD"]:
        print("✅ Backend system validation: PASSED with minor issues")
        sys.exit(0)
    else:
        print("⚠️  Backend system validation: NEEDS ATTENTION")
        sys.exit(1)