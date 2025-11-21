#!/usr/bin/env python3
"""
Backend Structure and Code Quality Tests for EDMS.

Tests the structure, syntax, and basic functionality of the backend
without requiring full Django setup or database connections.
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path

class BackendStructureTests:
    """Test backend structure and code quality."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
    def log_result(self, test_name, passed, error=None):
        """Log test result."""
        self.results['total_tests'] += 1
        if passed:
            self.results['passed'] += 1
            print(f"✅ {test_name}")
        else:
            self.results['failed'] += 1
            print(f"❌ {test_name}: {error}")
            if error:
                self.results['errors'].append(f"{test_name}: {error}")
    
    def test_python_syntax(self):
        """Test Python syntax for all Python files."""
        print("\n🔍 Testing Python syntax across all modules...")
        
        python_files = []
        for pattern in ['**/*.py']:
            python_files.extend(self.base_path.glob(pattern))
        
        syntax_errors = []
        valid_files = 0
        
        for file_path in python_files:
            if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the file to check syntax
                ast.parse(content, filename=str(file_path))
                valid_files += 1
                
            except SyntaxError as e:
                syntax_errors.append(f"{file_path}: {e}")
            except Exception as e:
                syntax_errors.append(f"{file_path}: {e}")
        
        if syntax_errors:
            self.log_result(f"Python Syntax ({len(syntax_errors)} errors)", False, 
                          f"{len(syntax_errors)} files have syntax errors")
            for error in syntax_errors[:5]:  # Show first 5 errors
                print(f"    {error}")
        else:
            self.log_result(f"Python Syntax ({valid_files} files)", True)
    
    def test_app_structure(self):
        """Test Django app structure."""
        print("\n🏗️  Testing Django app structure...")
        
        required_apps = [
            'users', 'documents', 'workflows', 'audit', 'security',
            'placeholders', 'scheduler', 'backup', 'settings', 'search', 'api'
        ]
        
        missing_apps = []
        incomplete_apps = []
        
        for app_name in required_apps:
            app_path = self.base_path / 'apps' / app_name
            
            if not app_path.exists():
                missing_apps.append(app_name)
                continue
            
            # Check required files
            required_files = ['__init__.py', 'models.py', 'apps.py']
            missing_files = []
            
            for file_name in required_files:
                if not (app_path / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                incomplete_apps.append(f"{app_name}: missing {', '.join(missing_files)}")
        
        if missing_apps:
            self.log_result("App Structure - Missing Apps", False, 
                          f"Missing apps: {', '.join(missing_apps)}")
        elif incomplete_apps:
            self.log_result("App Structure - Incomplete Apps", False,
                          f"Incomplete apps: {'; '.join(incomplete_apps)}")
        else:
            self.log_result(f"App Structure ({len(required_apps)} apps)", True)
    
    def test_model_definitions(self):
        """Test model definitions in each app."""
        print("\n📋 Testing model definitions...")
        
        apps_with_models = [
            'users', 'documents', 'workflows', 'audit', 'security',
            'placeholders', 'backup', 'settings', 'search'
        ]
        
        model_issues = []
        total_models = 0
        
        for app_name in apps_with_models:
            models_file = self.base_path / 'apps' / app_name / 'models.py'
            
            if not models_file.exists():
                model_issues.append(f"{app_name}: models.py not found")
                continue
            
            try:
                with open(models_file, 'r') as f:
                    content = f.read()
                
                # Parse and count model classes
                tree = ast.parse(content)
                models_count = 0
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it inherits from models.Model
                        for base in node.bases:
                            if hasattr(base, 'attr') and base.attr == 'Model':
                                models_count += 1
                            elif hasattr(base, 'id') and base.id in ['Model', 'AbstractUser']:
                                models_count += 1
                
                total_models += models_count
                
                if models_count == 0:
                    model_issues.append(f"{app_name}: no model classes found")
                
            except Exception as e:
                model_issues.append(f"{app_name}: {e}")
        
        if model_issues:
            self.log_result("Model Definitions", False, 
                          f"{len(model_issues)} issues found")
            for issue in model_issues[:3]:
                print(f"    {issue}")
        else:
            self.log_result(f"Model Definitions ({total_models} models)", True)
    
    def test_service_classes(self):
        """Test service class definitions."""
        print("\n⚙️  Testing service classes...")
        
        expected_services = [
            ('workflows', 'services.py'),
            ('audit', 'services.py'),
            ('placeholders', 'services.py'),
            ('backup', 'services.py'),
            ('search', 'services.py'),
            ('security', 'electronic_signatures.py'),
            ('users', 'workflow_permissions.py'),
            ('documents', 'workflow_integration.py')
        ]
        
        service_issues = []
        total_services = 0
        
        for app_name, service_file in expected_services:
            service_path = self.base_path / 'apps' / app_name / service_file
            
            if not service_path.exists():
                service_issues.append(f"{app_name}/{service_file}: not found")
                continue
            
            try:
                with open(service_path, 'r') as f:
                    content = f.read()
                
                # Check for service classes
                tree = ast.parse(content)
                service_classes = 0
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if 'Service' in node.name or 'Manager' in node.name:
                            service_classes += 1
                
                total_services += service_classes
                
                if service_classes == 0:
                    service_issues.append(f"{app_name}/{service_file}: no service classes")
                
            except Exception as e:
                service_issues.append(f"{app_name}/{service_file}: {e}")
        
        if service_issues:
            self.log_result("Service Classes", False,
                          f"{len(service_issues)} issues found")
            for issue in service_issues[:3]:
                print(f"    {issue}")
        else:
            self.log_result(f"Service Classes ({total_services} services)", True)
    
    def test_api_structure(self):
        """Test API structure and endpoints."""
        print("\n🌐 Testing API structure...")
        
        api_files = [
            ('api/v1', 'urls.py'),
            ('api/v1', 'views.py'),
            ('api', 'authentication.py'),
            ('api', 'throttling.py'),
            ('api', 'middleware.py')
        ]
        
        api_issues = []
        
        for path, file_name in api_files:
            file_path = self.base_path / 'apps' / path / file_name
            
            if not file_path.exists():
                api_issues.append(f"{path}/{file_name}: not found")
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for API-specific patterns
                if file_name == 'urls.py':
                    if 'router' not in content or 'urlpatterns' not in content:
                        api_issues.append(f"{path}/{file_name}: missing URL configuration")
                elif file_name == 'views.py':
                    if 'ViewSet' not in content and 'APIView' not in content:
                        api_issues.append(f"{path}/{file_name}: missing view classes")
                
            except Exception as e:
                api_issues.append(f"{path}/{file_name}: {e}")
        
        if api_issues:
            self.log_result("API Structure", False, f"{len(api_issues)} issues found")
            for issue in api_issues[:3]:
                print(f"    {issue}")
        else:
            self.log_result(f"API Structure ({len(api_files)} files)", True)
    
    def test_documentation_strings(self):
        """Test for documentation strings in Python files."""
        print("\n📚 Testing documentation coverage...")
        
        important_files = [
            'apps/documents/models.py',
            'apps/workflows/services.py',
            'apps/audit/services.py',
            'apps/search/services.py'
        ]
        
        doc_issues = []
        well_documented = 0
        
        for file_path in important_files:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                doc_issues.append(f"{file_path}: file not found")
                continue
            
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                
                # Count docstrings
                tree = ast.parse(content)
                total_classes = 0
                documented_classes = 0
                total_functions = 0
                documented_functions = 0
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        total_classes += 1
                        if ast.get_docstring(node):
                            documented_classes += 1
                    elif isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1
                
                # Calculate documentation percentage
                total_items = total_classes + total_functions
                documented_items = documented_classes + documented_functions
                
                if total_items > 0:
                    doc_percentage = (documented_items / total_items) * 100
                    if doc_percentage >= 80:
                        well_documented += 1
                    else:
                        doc_issues.append(f"{file_path}: {doc_percentage:.1f}% documented")
                
            except Exception as e:
                doc_issues.append(f"{file_path}: {e}")
        
        if doc_issues:
            self.log_result("Documentation Coverage", False,
                          f"{len(doc_issues)} poorly documented files")
        else:
            self.log_result(f"Documentation Coverage ({well_documented} files)", True)
    
    def test_code_complexity(self):
        """Test basic code complexity metrics."""
        print("\n📊 Testing code complexity...")
        
        large_files = []
        complex_functions = []
        
        for python_file in self.base_path.glob('apps/**/*.py'):
            if 'venv' in str(python_file) or '__pycache__' in str(python_file):
                continue
            
            try:
                with open(python_file, 'r') as f:
                    lines = f.readlines()
                
                # Check file size
                if len(lines) > 1000:
                    large_files.append(f"{python_file.relative_to(self.base_path)}: {len(lines)} lines")
                
                # Parse and check function complexity
                content = ''.join(lines)
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Simple complexity measure: count nested blocks
                        complexity = self._count_complexity(node)
                        if complexity > 15:
                            complex_functions.append(
                                f"{python_file.relative_to(self.base_path)}:{node.name} (complexity: {complexity})"
                            )
            
            except Exception:
                continue
        
        issues = []
        if large_files:
            issues.extend(large_files[:3])  # Show top 3
        if complex_functions:
            issues.extend(complex_functions[:3])  # Show top 3
        
        if issues:
            self.log_result("Code Complexity", False, f"{len(issues)} complexity issues")
            for issue in issues:
                print(f"    {issue}")
        else:
            self.log_result("Code Complexity", True)
    
    def _count_complexity(self, node):
        """Count cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def test_import_structure(self):
        """Test import structure and dependencies."""
        print("\n📦 Testing import structure...")
        
        circular_imports = []
        missing_imports = []
        
        # This is a simplified check - in real scenario would need more sophisticated analysis
        python_files = list(self.base_path.glob('apps/**/*.py'))
        
        import_issues = 0
        for python_file in python_files[:20]:  # Check first 20 files to avoid too much output
            if 'venv' in str(python_file) or '__pycache__' in str(python_file):
                continue
            
            try:
                with open(python_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('apps.'):
                            # Check if the imported module might exist
                            module_parts = node.module.split('.')
                            if len(module_parts) >= 2:
                                app_name = module_parts[1]
                                app_path = self.base_path / 'apps' / app_name
                                if not app_path.exists():
                                    import_issues += 1
                                    break
            
            except Exception:
                continue
        
        if import_issues > 0:
            self.log_result("Import Structure", False, f"{import_issues} potential import issues")
        else:
            self.log_result("Import Structure", True)
    
    def run_all_tests(self):
        """Run all structure tests."""
        print("🧪 EDMS Backend Structure and Quality Tests")
        print("=" * 80)
        
        # Run all tests
        self.test_python_syntax()
        self.test_app_structure()
        self.test_model_definitions()
        self.test_service_classes()
        self.test_api_structure()
        self.test_documentation_strings()
        self.test_code_complexity()
        self.test_import_structure()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total = self.results['total_tests']
        passed = self.results['passed']
        failed = self.results['failed']
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("🎉 EXCELLENT: Backend structure is high quality!")
            elif success_rate >= 80:
                print("✅ GOOD: Backend structure is solid with minor issues")
            elif success_rate >= 70:
                print("⚠️  NEEDS IMPROVEMENT: Several structural issues")
            else:
                print("🚨 CRITICAL: Major structural problems")
        
        # Show errors if any
        if self.results['errors']:
            print(f"\n❌ ERRORS FOUND:")
            for error in self.results['errors'][:10]:  # Show first 10 errors
                print(f"  {error}")
        
        print("\n" + "=" * 80)
        return success_rate if total > 0 else 0


if __name__ == "__main__":
    tester = BackendStructureTests()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    if success_rate >= 80:
        print("✅ Backend structure tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Backend structure tests completed with issues!")
        sys.exit(1)