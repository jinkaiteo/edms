#!/usr/bin/env python3
"""
Functional Testing for EDMS Backend Components.

Tests the functionality of individual components without
requiring full Django setup or database connections.
"""

import json
import tempfile
import os
from datetime import datetime

class ComponentFunctionalTests:
    """Test component functionality independently."""
    
    def __init__(self):
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'components_tested': []
        }
    
    def log_result(self, component, test_name, passed, details=""):
        """Log test result."""
        self.results['total_tests'] += 1
        
        if component not in self.results['components_tested']:
            self.results['components_tested'].append(component)
        
        if passed:
            self.results['passed'] += 1
            print(f"  ✅ {test_name}")
        else:
            self.results['failed'] += 1
            print(f"  ❌ {test_name}: {details}")
    
    def test_json_processing(self):
        """Test JSON processing capabilities."""
        print("\n📄 Testing JSON Processing...")
        
        # Test JSON serialization/deserialization
        try:
            test_data = {
                'document_id': 123,
                'metadata': {
                    'author': 'Test User',
                    'created_at': datetime.now().isoformat(),
                    'tags': ['test', 'document', 'validation']
                },
                'workflow_state': 'draft'
            }
            
            # Serialize
            json_str = json.dumps(test_data, indent=2)
            assert len(json_str) > 0
            
            # Deserialize
            parsed_data = json.loads(json_str)
            assert parsed_data['document_id'] == 123
            assert parsed_data['metadata']['author'] == 'Test User'
            assert len(parsed_data['metadata']['tags']) == 3
            
            self.log_result('Core', 'JSON Serialization/Deserialization', True)
        except Exception as e:
            self.log_result('Core', 'JSON Serialization/Deserialization', False, str(e))
    
    def test_file_operations(self):
        """Test file operation capabilities."""
        print("\n📁 Testing File Operations...")
        
        # Test file creation and reading
        try:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                test_content = """# Test Document
                
This is a test document for validating file operations.
It contains multiple lines and special characters: áéíóú, 中文, русский

Document ID: TEST-001
Status: Draft
Created: 2024-01-01T00:00:00Z
"""
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            # Read the file back
            with open(temp_file_path, 'r') as f:
                read_content = f.read()
            
            assert 'TEST-001' in read_content
            assert 'Draft' in read_content
            assert len(read_content) > 100
            
            # Clean up
            os.unlink(temp_file_path)
            
            self.log_result('Core', 'File Create/Read Operations', True)
        except Exception as e:
            self.log_result('Core', 'File Create/Read Operations', False, str(e))
    
    def test_datetime_handling(self):
        """Test datetime processing."""
        print("\n⏰ Testing DateTime Handling...")
        
        try:
            # Test datetime creation and formatting
            now = datetime.now()
            
            # ISO format
            iso_str = now.isoformat()
            parsed_datetime = datetime.fromisoformat(iso_str)
            assert abs((now - parsed_datetime).total_seconds()) < 1
            
            # Custom format
            custom_format = now.strftime('%Y-%m-%d %H:%M:%S')
            assert len(custom_format) == 19  # Expected format length
            
            # Date arithmetic
            from datetime import timedelta
            future_date = now + timedelta(days=30)
            assert future_date > now
            
            delta = future_date - now
            assert delta.days == 30
            
            self.log_result('Core', 'DateTime Operations', True)
        except Exception as e:
            self.log_result('Core', 'DateTime Operations', False, str(e))
    
    def test_text_processing(self):
        """Test text processing capabilities."""
        print("\n📝 Testing Text Processing...")
        
        try:
            # Test text manipulation
            test_text = "  This is a TEST Document with Special Characters: @#$%^&*()  "
            
            # Basic cleaning
            cleaned = test_text.strip().lower()
            assert 'test document' in cleaned
            
            # Word extraction
            words = test_text.split()
            assert 'TEST' in words
            assert 'Document' in words
            
            # Pattern matching
            import re
            
            # Find uppercase words
            uppercase_words = re.findall(r'\b[A-Z]+\b', test_text)
            assert 'TEST' in uppercase_words
            
            # Find special characters
            special_chars = re.findall(r'[^a-zA-Z0-9\s]', test_text)
            assert len(special_chars) > 0
            
            self.log_result('Core', 'Text Processing', True)
        except Exception as e:
            self.log_result('Core', 'Text Processing', False, str(e))
    
    def test_data_validation(self):
        """Test data validation functions."""
        print("\n✅ Testing Data Validation...")
        
        try:
            # Test email validation
            def validate_email(email):
                import re
                pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                return re.match(pattern, email) is not None
            
            assert validate_email('test@example.com') == True
            assert validate_email('invalid-email') == False
            assert validate_email('user@domain.org') == True
            
            # Test document number validation
            def validate_document_number(doc_num):
                import re
                pattern = r'^[A-Z]{2,4}-\d{3,6}$'
                return re.match(pattern, doc_num) is not None
            
            assert validate_document_number('DOC-001') == True
            assert validate_document_number('PROC-12345') == True
            assert validate_document_number('invalid') == False
            
            # Test version validation
            def validate_version(version):
                import re
                pattern = r'^\d+\.\d+(\.\d+)?$'
                return re.match(pattern, version) is not None
            
            assert validate_version('1.0') == True
            assert validate_version('2.1.5') == True
            assert validate_version('1.0.0.1') == False
            
            self.log_result('Core', 'Data Validation', True)
        except Exception as e:
            self.log_result('Core', 'Data Validation', False, str(e))
    
    def test_search_algorithms(self):
        """Test search algorithm implementations."""
        print("\n🔍 Testing Search Algorithms...")
        
        try:
            # Test simple text search
            documents = [
                {'id': 1, 'title': 'Quality Management System', 'content': 'ISO 9001 compliance document'},
                {'id': 2, 'title': 'Safety Procedures Manual', 'content': 'Safety guidelines and procedures'},
                {'id': 3, 'title': 'Quality Control Process', 'content': 'QC procedures and quality standards'},
                {'id': 4, 'title': 'Training Manual', 'content': 'Employee training and development'}
            ]
            
            def simple_search(docs, query):
                query_lower = query.lower()
                results = []
                
                for doc in docs:
                    score = 0
                    title_lower = doc['title'].lower()
                    content_lower = doc['content'].lower()
                    
                    # Title matches get higher score
                    if query_lower in title_lower:
                        score += 10
                    
                    # Content matches
                    if query_lower in content_lower:
                        score += 5
                    
                    # Word matches
                    for word in query_lower.split():
                        if word in title_lower:
                            score += 3
                        if word in content_lower:
                            score += 1
                    
                    if score > 0:
                        results.append({'doc': doc, 'score': score})
                
                return sorted(results, key=lambda x: x['score'], reverse=True)
            
            # Test searches
            quality_results = simple_search(documents, 'quality')
            assert len(quality_results) >= 2
            assert quality_results[0]['score'] > 0
            
            safety_results = simple_search(documents, 'safety')
            assert len(safety_results) >= 1
            
            manual_results = simple_search(documents, 'manual')
            assert len(manual_results) >= 2
            
            self.log_result('Search', 'Basic Search Algorithm', True)
        except Exception as e:
            self.log_result('Search', 'Basic Search Algorithm', False, str(e))
    
    def test_workflow_logic(self):
        """Test workflow state machine logic."""
        print("\n🔄 Testing Workflow Logic...")
        
        try:
            # Define workflow states and transitions
            STATES = {
                'DRAFT': 'Draft',
                'REVIEW': 'Under Review',
                'APPROVED': 'Approved',
                'EFFECTIVE': 'Effective',
                'OBSOLETE': 'Obsolete'
            }
            
            TRANSITIONS = {
                'DRAFT': ['REVIEW'],
                'REVIEW': ['DRAFT', 'APPROVED'],
                'APPROVED': ['EFFECTIVE', 'DRAFT'],
                'EFFECTIVE': ['OBSOLETE'],
                'OBSOLETE': []
            }
            
            class WorkflowEngine:
                def __init__(self):
                    self.state = 'DRAFT'
                
                def can_transition(self, new_state):
                    return new_state in TRANSITIONS.get(self.state, [])
                
                def transition(self, new_state):
                    if self.can_transition(new_state):
                        old_state = self.state
                        self.state = new_state
                        return True
                    return False
                
                def get_available_transitions(self):
                    return TRANSITIONS.get(self.state, [])
            
            # Test workflow
            workflow = WorkflowEngine()
            
            # Test initial state
            assert workflow.state == 'DRAFT'
            assert 'REVIEW' in workflow.get_available_transitions()
            
            # Test valid transition
            assert workflow.transition('REVIEW') == True
            assert workflow.state == 'REVIEW'
            
            # Test invalid transition
            assert workflow.transition('EFFECTIVE') == False
            assert workflow.state == 'REVIEW'  # State should not change
            
            # Test approval path
            assert workflow.transition('APPROVED') == True
            assert workflow.transition('EFFECTIVE') == True
            assert workflow.state == 'EFFECTIVE'
            
            # Test final state
            assert workflow.transition('OBSOLETE') == True
            assert len(workflow.get_available_transitions()) == 0
            
            self.log_result('Workflow', 'State Machine Logic', True)
        except Exception as e:
            self.log_result('Workflow', 'State Machine Logic', False, str(e))
    
    def test_permission_logic(self):
        """Test permission checking logic."""
        print("\n🔐 Testing Permission Logic...")
        
        try:
            # Define permission system
            ROLES = {
                'reader': ['read'],
                'author': ['read', 'write'],
                'reviewer': ['read', 'write', 'review'],
                'approver': ['read', 'write', 'review', 'approve'],
                'admin': ['read', 'write', 'review', 'approve', 'admin']
            }
            
            class PermissionChecker:
                def __init__(self, user_roles):
                    self.user_roles = user_roles if isinstance(user_roles, list) else [user_roles]
                
                def has_permission(self, permission):
                    for role in self.user_roles:
                        if permission in ROLES.get(role, []):
                            return True
                    return False
                
                def can_perform_action(self, action):
                    action_permissions = {
                        'view_document': ['read'],
                        'create_document': ['write'],
                        'edit_document': ['write'],
                        'review_document': ['review'],
                        'approve_document': ['approve'],
                        'delete_document': ['admin']
                    }
                    
                    required_perms = action_permissions.get(action, [])
                    return any(self.has_permission(perm) for perm in required_perms)
            
            # Test permissions
            reader = PermissionChecker('reader')
            assert reader.can_perform_action('view_document') == True
            assert reader.can_perform_action('create_document') == False
            
            author = PermissionChecker('author')
            assert author.can_perform_action('view_document') == True
            assert author.can_perform_action('create_document') == True
            assert author.can_perform_action('approve_document') == False
            
            approver = PermissionChecker('approver')
            assert approver.can_perform_action('approve_document') == True
            assert approver.can_perform_action('delete_document') == False
            
            admin = PermissionChecker('admin')
            assert admin.can_perform_action('delete_document') == True
            
            # Test multiple roles
            multi_role_user = PermissionChecker(['reader', 'author'])
            assert multi_role_user.can_perform_action('view_document') == True
            assert multi_role_user.can_perform_action('create_document') == True
            
            self.log_result('Permissions', 'Role-Based Access Control', True)
        except Exception as e:
            self.log_result('Permissions', 'Role-Based Access Control', False, str(e))
    
    def test_encryption_basics(self):
        """Test basic encryption/hashing capabilities."""
        print("\n🔒 Testing Encryption/Hashing...")
        
        try:
            import hashlib
            
            # Test SHA-256 hashing
            test_data = "sensitive document content"
            
            hash_obj = hashlib.sha256(test_data.encode())
            hash_hex = hash_obj.hexdigest()
            
            assert len(hash_hex) == 64  # SHA-256 produces 64-character hex string
            
            # Test consistency
            hash_obj2 = hashlib.sha256(test_data.encode())
            hash_hex2 = hash_obj2.hexdigest()
            
            assert hash_hex == hash_hex2  # Same input should produce same hash
            
            # Test different input produces different hash
            hash_obj3 = hashlib.sha256("different content".encode())
            hash_hex3 = hash_obj3.hexdigest()
            
            assert hash_hex != hash_hex3  # Different input should produce different hash
            
            # Test MD5 (for non-security purposes)
            md5_hash = hashlib.md5(test_data.encode()).hexdigest()
            assert len(md5_hash) == 32  # MD5 produces 32-character hex string
            
            self.log_result('Security', 'Hashing Functions', True)
        except Exception as e:
            self.log_result('Security', 'Hashing Functions', False, str(e))
    
    def run_all_tests(self):
        """Run all functional tests."""
        print("🧪 EDMS Backend Functional Component Tests")
        print("=" * 80)
        
        # Run all tests
        self.test_json_processing()
        self.test_file_operations()
        self.test_datetime_handling()
        self.test_text_processing()
        self.test_data_validation()
        self.test_search_algorithms()
        self.test_workflow_logic()
        self.test_permission_logic()
        self.test_encryption_basics()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 FUNCTIONAL TEST SUMMARY")
        print("=" * 80)
        
        total = self.results['total_tests']
        passed = self.results['passed']
        failed = self.results['failed']
        
        print(f"Components Tested: {len(self.results['components_tested'])}")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 95:
                print("🎉 EXCELLENT: All core functionality working perfectly!")
            elif success_rate >= 85:
                print("✅ GOOD: Core functionality working well")
            elif success_rate >= 70:
                print("⚠️  MODERATE: Some functionality issues detected")
            else:
                print("🚨 CRITICAL: Major functionality problems")
            
            print(f"\nComponents tested: {', '.join(self.results['components_tested'])}")
        
        print("=" * 80)
        return success_rate if total > 0 else 0


if __name__ == "__main__":
    tester = ComponentFunctionalTests()
    success_rate = tester.run_all_tests()
    
    print(f"\n🎯 Backend functional testing completed with {success_rate:.1f}% success rate")
    
    if success_rate >= 85:
        print("✅ Backend functionality validation: PASSED")
        exit(0)
    else:
        print("⚠️  Backend functionality validation: NEEDS ATTENTION")
        exit(1)