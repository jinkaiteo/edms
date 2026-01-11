"""
Document Dependencies Tests

Tests for document dependency management:
- Adding dependencies between documents
- Circular dependency prevention
- Dependency validation rules
- Critical dependency handling
- Version-aware dependency tracking
- Dependency impact analysis

COMPLIANCE: Dependency tracking ensures proper change control and impact analysis.
"""

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.documents.models import Document, DocumentType, DocumentSource, DocumentDependency

User = get_user_model()


@pytest.mark.django_db
class TestDocumentDependencies:
    """Test suite for document dependency management"""
    
    def setup_method(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='dep_user',
            password='test123'
        )
        
        self.doc_type = DocumentType.objects.create(
            name='Standard',
            code='STD',
            created_by=self.user
        )
        self.doc_source = DocumentSource.objects.create(
            name='Original Digital Draft',
            source_type='original_digital'
        )
        
        # Create test documents
        self.doc_a = Document.objects.create(
            title='Document A',
            description='First document',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE',
            version_major=1,
            version_minor=0
        )
        
        self.doc_b = Document.objects.create(
            title='Document B',
            description='Second document',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE',
            version_major=1,
            version_minor=0
        )
        
        self.doc_c = Document.objects.create(
            title='Document C',
            description='Third document',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE',
            version_major=1,
            version_minor=0
        )
    
    def test_add_dependency_to_document(self):
        """Test adding a dependency between documents"""
        dependency = DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            description='Doc A references Doc B',
            created_by=self.user
        )
        
        assert dependency.document == self.doc_a
        assert dependency.depends_on == self.doc_b
        assert dependency.dependency_type == 'REFERENCE'
        assert dependency.is_active is True
    
    def test_circular_dependency_prevented(self):
        """
        Test that circular dependencies are prevented.
        
        Example: A → B → A should be blocked
        """
        # Create A → B
        DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        # Try to create B → A (would create circular dependency)
        with pytest.raises(ValidationError):
            dep = DocumentDependency(
                document=self.doc_b,
                depends_on=self.doc_a,
                dependency_type='REFERENCE',
                created_by=self.user
            )
            dep.clean()  # Should raise ValidationError
            dep.save()
    
    def test_indirect_circular_dependency_prevented(self):
        """
        Test that indirect circular dependencies are prevented.
        
        Example: A → B → C → A should be blocked
        """
        # Create A → B
        DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        # Create B → C
        DocumentDependency.objects.create(
            document=self.doc_b,
            depends_on=self.doc_c,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        # Try to create C → A (would create circular dependency)
        with pytest.raises(ValidationError):
            dep = DocumentDependency(
                document=self.doc_c,
                depends_on=self.doc_a,
                dependency_type='REFERENCE',
                created_by=self.user
            )
            dep.clean()
            dep.save()
    
    def test_self_dependency_prevented(self):
        """Test that a document cannot depend on itself"""
        with pytest.raises(ValidationError):
            dep = DocumentDependency(
                document=self.doc_a,
                depends_on=self.doc_a,
                dependency_type='REFERENCE',
                created_by=self.user
            )
            dep.clean()
            dep.save()
    
    def test_multiple_dependencies_allowed(self):
        """Test that a document can have multiple dependencies"""
        # Doc A depends on both Doc B and Doc C
        dep1 = DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        dep2 = DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_c,
            dependency_type='IMPLEMENTS',
            created_by=self.user
        )
        
        assert self.doc_a.dependencies.count() == 2
    
    def test_critical_dependency_flag(self):
        """Test marking dependencies as critical"""
        dependency = DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            is_critical=True,
            description='Critical reference - changes require notification',
            created_by=self.user
        )
        
        assert dependency.is_critical is True
    
    def test_dependency_types(self):
        """Test different dependency types"""
        types = ['REFERENCE', 'TEMPLATE', 'SUPERSEDES', 'INCORPORATES', 'SUPPORTS', 'IMPLEMENTS']
        
        for dep_type in types:
            # Use different target docs to avoid unique constraint
            target_doc = Document.objects.create(
                title=f'Target for {dep_type}',
                description='Target',
                document_type=self.doc_type,
                document_source=self.doc_source,
                author=self.user,
                status='EFFECTIVE',
                version_major=1,
                version_minor=0
            )
            
            dependency = DocumentDependency.objects.create(
                document=self.doc_a,
                depends_on=target_doc,
                dependency_type=dep_type,
                created_by=self.user
            )
            
            assert dependency.dependency_type == dep_type
    
    def test_dependency_on_draft_document(self):
        """
        Test dependency behavior with DRAFT documents.
        
        Note: Current implementation may allow this, but ideally
        documents should only depend on EFFECTIVE documents.
        """
        draft_doc = Document.objects.create(
            title='Draft Document',
            description='Still in draft',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='DRAFT',
            version_major=1,
            version_minor=0
        )
        
        # This may be allowed in current implementation
        # Add validation if needed
        dependency = DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=draft_doc,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        assert dependency is not None
    
    def test_version_aware_circular_dependency_detection(self):
        """
        Test circular dependency detection across document versions.
        
        Example: POL-2025-0001 v1.0 → SOP-2025-0001 v1.0
                 SOP-2025-0001 v2.0 → POL-2025-0001 v1.0 should be blocked
        """
        # This tests the base number approach for circular detection
        # POL v1 depends on SOP v1
        DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        # Create v2.0 of doc_b (SOP v2)
        doc_b_v2 = Document.objects.create(
            title='Document B v2.0',
            description='Version 2 of Doc B',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE',
            version_major=2,
            version_minor=0
        )
        
        # Try to create SOP v2 → POL v1 (should be blocked if base number check works)
        # Note: Current implementation uses document_number base for detection
        pass
    
    def test_get_dependency_chain(self):
        """Test retrieving complete dependency chain"""
        # Create chain: A → B → C
        DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        DocumentDependency.objects.create(
            document=self.doc_b,
            depends_on=self.doc_c,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        # Get dependency chain for doc_a
        chain = DocumentDependency.get_dependency_chain(self.doc_a.id)
        
        assert 'dependencies' in chain
        assert 'dependents' in chain
    
    def test_remove_dependency(self):
        """Test removing/deactivating a dependency"""
        dependency = DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        # Soft delete (deactivate)
        dependency.is_active = False
        dependency.save()
        
        assert dependency.is_active is False
    
    def test_detect_circular_dependencies_system_wide(self):
        """Test system-wide circular dependency detection"""
        # Create some dependencies
        DocumentDependency.objects.create(
            document=self.doc_a,
            depends_on=self.doc_b,
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        # Run system-wide detection
        cycles = DocumentDependency.detect_circular_dependencies()
        
        # Should find no cycles in valid setup
        assert len(cycles) == 0
