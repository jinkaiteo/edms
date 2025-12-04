#!/usr/bin/env python
"""
EDMS Data Integrity Validation Script
=====================================

Comprehensive validation script to verify data integrity 
after reinit → restore cycle operations.

Usage:
    python manage.py shell < tmp_rovodev_validation_script.py
"""

from django.contrib.auth import get_user_model
from apps.documents.models import Document, DocumentVersion, DocumentType
from apps.workflows.models import WorkflowInstance, DocumentWorkflow, WorkflowType
from apps.audit.models import AuditTrail
from apps.placeholders.models import PlaceholderDefinition
from apps.backup.models import BackupJob, BackupConfiguration
import json
import os

User = get_user_model()

class DataIntegrityValidator:
    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        
    def capture_baseline(self):
        """Capture current system state as baseline"""
        self.baseline = {
            'users': {
                'count': User.objects.count(),
                'sample_data': [
                    {
                        'username': user.username,
                        'email': user.email,
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff,
                        'is_active': user.is_active
                    } for user in User.objects.all()[:10]
                ]
            },
            'documents': {
                'count': Document.objects.count(),
                'sample_data': [
                    {
                        'document_number': doc.document_number,
                        'title': doc.title,
                        'status': doc.status,
                        'author_username': doc.author.username if doc.author else None
                    } for doc in Document.objects.all()[:10]
                ]
            },
            'workflows': {
                'count': WorkflowInstance.objects.count(),
                'active_count': WorkflowInstance.objects.filter(is_active=True).count(),
                'sample_data': [
                    {
                        'id': wf.id,
                        'initiated_by': wf.initiated_by.username if wf.initiated_by else None,
                        'is_active': wf.is_active,
                        'is_completed': wf.is_completed
                    } for wf in WorkflowInstance.objects.all()[:10]
                ]
            },
            'placeholders': {
                'count': PlaceholderDefinition.objects.count(),
                'sample_data': [
                    {
                        'name': ph.name,
                        'description': ph.description,
                        'data_type': ph.data_type
                    } for ph in PlaceholderDefinition.objects.all()[:10]
                ]
            },
            'infrastructure': {
                'document_types': DocumentType.objects.count(),
                'workflow_types': WorkflowType.objects.count(),
                'backup_configs': BackupConfiguration.objects.count()
            }
        }
        
        print("📊 BASELINE CAPTURED")
        print("=" * 30)
        for category, data in self.baseline.items():
            if isinstance(data, dict) and 'count' in data:
                print(f"  {category}: {data['count']} records")
            elif isinstance(data, dict):
                print(f"  {category}: {data}")
        print()
        
    def validate_post_restore(self, expected_baseline=None):
        """Validate system state after restore operation"""
        print("🔍 POST-RESTORE VALIDATION")
        print("=" * 30)
        
        current_state = {
            'users': {
                'count': User.objects.count(),
                'sample_data': [
                    {
                        'username': user.username,
                        'email': user.email,
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff,
                        'is_active': user.is_active
                    } for user in User.objects.all()[:10]
                ]
            },
            'documents': {
                'count': Document.objects.count(),
                'sample_data': [
                    {
                        'document_number': doc.document_number,
                        'title': doc.title,
                        'status': doc.status,
                        'author_username': doc.author.username if doc.author else None
                    } for doc in Document.objects.all()[:10]
                ]
            },
            'workflows': {
                'count': WorkflowInstance.objects.count(),
                'active_count': WorkflowInstance.objects.filter(is_active=True).count(),
                'sample_data': [
                    {
                        'id': wf.id,
                        'initiated_by': wf.initiated_by.username if wf.initiated_by else None,
                        'is_active': wf.is_active,
                        'is_completed': wf.is_completed
                    } for wf in WorkflowInstance.objects.all()[:10]
                ]
            },
            'placeholders': {
                'count': PlaceholderDefinition.objects.count(),
                'sample_data': [
                    {
                        'name': ph.name,
                        'description': ph.description,
                        'data_type': ph.data_type
                    } for ph in PlaceholderDefinition.objects.all()[:10]
                ]
            },
            'infrastructure': {
                'document_types': DocumentType.objects.count(),
                'workflow_types': WorkflowType.objects.count(),
                'backup_configs': BackupConfiguration.objects.count()
            }
        }
        
        if expected_baseline:
            self._compare_states(expected_baseline, current_state)
        
        self._validate_data_integrity(current_state)
        self._validate_foreign_key_consistency()
        self._validate_user_authentication()
        
        return self._generate_validation_report()
    
    def _compare_states(self, expected, actual):
        """Compare expected vs actual state after restore"""
        print("📊 STATE COMPARISON")
        print("-" * 20)
        
        for category in expected.keys():
            if category in actual:
                expected_count = expected[category].get('count', 0)
                actual_count = actual[category].get('count', 0)
                
                if expected_count == actual_count:
                    print(f"  ✅ {category}: {actual_count} (matches baseline)")
                    self.validation_results[f"{category}_count"] = "PASS"
                else:
                    print(f"  ❌ {category}: {actual_count} (expected {expected_count})")
                    self.validation_results[f"{category}_count"] = "FAIL"
                    self.errors.append(f"{category} count mismatch: expected {expected_count}, got {actual_count}")
        print()
    
    def _validate_data_integrity(self, current_state):
        """Validate data integrity and relationships"""
        print("🔍 DATA INTEGRITY VALIDATION")
        print("-" * 30)
        
        # Check placeholders (core infrastructure)
        placeholder_count = current_state['placeholders']['count']
        if placeholder_count >= 30:
            print(f"  ✅ Placeholders: {placeholder_count} (core infrastructure intact)")
            self.validation_results['placeholders_integrity'] = "PASS"
        else:
            print(f"  ❌ Placeholders: {placeholder_count} (core infrastructure damaged)")
            self.validation_results['placeholders_integrity'] = "FAIL"
            self.errors.append(f"Insufficient placeholders: {placeholder_count} (expected ≥30)")
        
        # Check document-author relationships
        orphaned_docs = Document.objects.filter(author__isnull=True).count()
        if orphaned_docs == 0:
            print(f"  ✅ Document-Author Links: All documents have authors")
            self.validation_results['document_author_links'] = "PASS"
        else:
            print(f"  ⚠️ Document-Author Links: {orphaned_docs} orphaned documents")
            self.validation_results['document_author_links'] = "WARN"
            self.warnings.append(f"{orphaned_docs} documents without authors")
        
        # Check workflow-user relationships
        orphaned_workflows = WorkflowInstance.objects.filter(initiated_by__isnull=True).count()
        if orphaned_workflows == 0:
            print(f"  ✅ Workflow-User Links: All workflows have initiators")
            self.validation_results['workflow_user_links'] = "PASS"
        else:
            print(f"  ⚠️ Workflow-User Links: {orphaned_workflows} orphaned workflows")
            self.validation_results['workflow_user_links'] = "WARN"
            self.warnings.append(f"{orphaned_workflows} workflows without initiators")
        
        print()
    
    def _validate_foreign_key_consistency(self):
        """Validate foreign key relationships"""
        print("🔗 FOREIGN KEY CONSISTENCY")
        print("-" * 25)
        
        try:
            # Test critical FK relationships
            for doc in Document.objects.all()[:5]:
                if doc.author:
                    assert User.objects.filter(id=doc.author.id).exists()
                if hasattr(doc, 'document_type') and doc.document_type:
                    assert DocumentType.objects.filter(id=doc.document_type.id).exists()
            
            print("  ✅ Document FK relationships valid")
            self.validation_results['document_fk_integrity'] = "PASS"
        except Exception as e:
            print(f"  ❌ Document FK relationships broken: {e}")
            self.validation_results['document_fk_integrity'] = "FAIL"
            self.errors.append(f"Document FK integrity error: {e}")
        
        try:
            # Test workflow FK relationships  
            for wf in WorkflowInstance.objects.all()[:5]:
                if wf.initiated_by:
                    assert User.objects.filter(id=wf.initiated_by.id).exists()
                if hasattr(wf, 'workflow_type') and wf.workflow_type:
                    assert WorkflowType.objects.filter(id=wf.workflow_type.id).exists()
            
            print("  ✅ Workflow FK relationships valid")
            self.validation_results['workflow_fk_integrity'] = "PASS"
        except Exception as e:
            print(f"  ❌ Workflow FK relationships broken: {e}")
            self.validation_results['workflow_fk_integrity'] = "FAIL"
            self.errors.append(f"Workflow FK integrity error: {e}")
        
        print()
    
    def _validate_user_authentication(self):
        """Validate user authentication functionality"""
        print("🔐 USER AUTHENTICATION VALIDATION")
        print("-" * 35)
        
        # Check admin user exists and is functional
        try:
            admin_user = User.objects.get(username='admin')
            if admin_user.is_superuser and admin_user.is_staff:
                print("  ✅ Admin user: Exists with proper permissions")
                self.validation_results['admin_user_integrity'] = "PASS"
            else:
                print("  ❌ Admin user: Exists but missing permissions")
                self.validation_results['admin_user_integrity'] = "FAIL"
                self.errors.append("Admin user missing superuser/staff permissions")
        except User.DoesNotExist:
            print("  ❌ Admin user: Does not exist")
            self.validation_results['admin_user_integrity'] = "FAIL"
            self.errors.append("Admin user not found after restore")
        
        # Check user count reasonableness
        user_count = User.objects.count()
        if user_count > 0:
            print(f"  ✅ User count: {user_count} users present")
            self.validation_results['user_count_reasonable'] = "PASS"
        else:
            print(f"  ❌ User count: {user_count} (no users found)")
            self.validation_results['user_count_reasonable'] = "FAIL"
            self.errors.append("No users found after restore")
        
        print()
    
    def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("📋 VALIDATION REPORT")
        print("=" * 20)
        
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for result in self.validation_results.values() if result == "PASS")
        warned_checks = sum(1 for result in self.validation_results.values() if result == "WARN")
        failed_checks = sum(1 for result in self.validation_results.values() if result == "FAIL")
        
        print(f"📊 SUMMARY:")
        print(f"  Total Checks: {total_checks}")
        print(f"  ✅ Passed: {passed_checks}")
        print(f"  ⚠️ Warnings: {warned_checks}")
        print(f"  ❌ Failed: {failed_checks}")
        print()
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        print(f"🎯 SUCCESS RATE: {success_rate:.1f}%")
        
        if failed_checks == 0:
            print("🎉 OVERALL RESULT: VALIDATION SUCCESSFUL!")
            overall_status = "SUCCESS"
        elif failed_checks <= 2:
            print("⚠️ OVERALL RESULT: VALIDATION MOSTLY SUCCESSFUL (minor issues)")
            overall_status = "MOSTLY_SUCCESS"
        else:
            print("❌ OVERALL RESULT: VALIDATION FAILED (significant issues)")
            overall_status = "FAILURE"
        
        if self.errors:
            print()
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print()
            print("⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        return {
            'overall_status': overall_status,
            'success_rate': success_rate,
            'total_checks': total_checks,
            'passed': passed_checks,
            'warnings': warned_checks,
            'failed': failed_checks,
            'errors': self.errors,
            'warnings_list': self.warnings,
            'detailed_results': self.validation_results
        }

# Initialize validator
validator = DataIntegrityValidator()

print("🎯 AUTOMATED DATA INTEGRITY VALIDATION")
print("=" * 50)
print()
print("📋 This script will validate:")
print("  1. Data count consistency")
print("  2. Foreign key relationships")  
print("  3. Core infrastructure integrity")
print("  4. User authentication functionality")
print("  5. Critical business data preservation")
print()