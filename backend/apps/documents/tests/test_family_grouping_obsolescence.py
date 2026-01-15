"""
Tests for Document Family Grouping and Enhanced Obsolescence Validation
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.documents.models import Document, DocumentType, DocumentSource, DocumentDependency

User = get_user_model()


class DocumentFamilyGroupingTests(TestCase):
    """Test family grouping functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.doc_type = DocumentType.objects.create(
            name='Test SOP',
            code='SOP',
            created_by=self.user
        )
        
        self.doc_source = DocumentSource.objects.create(
            name='Web Upload',
            source_type='web_upload'
        )
    
    def test_get_family_versions(self):
        """Test getting all versions of a document family"""
        # Create document family
        doc_v1 = Document.objects.create(
            title='Test Document',
            document_number='SOP-2025-0001-v01.00',
            version_major=1,
            version_minor=0,
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='SUPERSEDED'
        )
        
        doc_v2 = Document.objects.create(
            title='Test Document',
            document_number='SOP-2025-0001-v02.00',
            version_major=2,
            version_minor=0,
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE',
            supersedes=doc_v1
        )
        
        # Get family versions
        family = doc_v2.get_family_versions()
        
        self.assertEqual(len(family), 2)
        self.assertEqual(family[0].version_major, 2)  # Newest first
        self.assertEqual(family[1].version_major, 1)


class ObsolescenceValidationTests(TestCase):
    """Test enhanced obsolescence validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.doc_type = DocumentType.objects.create(
            name='Test SOP',
            code='SOP',
            created_by=self.user
        )
        
        self.doc_source = DocumentSource.objects.create(
            name='Web Upload',
            source_type='web_upload'
        )
    
    def test_can_obsolete_without_dependencies(self):
        """Test obsolescence validation when no dependencies exist"""
        doc = Document.objects.create(
            title='Test Document',
            document_number='SOP-2025-0001-v01.00',
            version_major=1,
            version_minor=0,
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE'
        )
        
        validation = doc.can_obsolete_family()
        
        self.assertTrue(validation['can_obsolete'])
        self.assertEqual(len(validation['blocking_dependencies']), 0)
    
    def test_cannot_obsolete_with_dependencies(self):
        """Test obsolescence validation when dependencies exist"""
        # Create document family
        policy_v1 = Document.objects.create(
            title='Test Policy',
            document_number='POL-2025-0001-v01.00',
            version_major=1,
            version_minor=0,
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='SUPERSEDED'
        )
        
        policy_v2 = Document.objects.create(
            title='Test Policy',
            document_number='POL-2025-0001-v02.00',
            version_major=2,
            version_minor=0,
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE',
            supersedes=policy_v1
        )
        
        # Create dependent document that depends on v1 (SUPERSEDED)
        sop = Document.objects.create(
            title='Dependent SOP',
            document_number='SOP-2025-0001-v01.00',
            version_major=1,
            version_minor=0,
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE'
        )
        
        # Create dependency
        DocumentDependency.objects.create(
            document=sop,
            depends_on=policy_v1,  # Depends on SUPERSEDED version
            dependency_type='REFERENCE',
            created_by=self.user
        )
        
        # Validate - should block because v1 has active dependents
        validation = policy_v2.can_obsolete_family()
        
        self.assertFalse(validation['can_obsolete'])
        self.assertEqual(validation['affected_versions'], 1)
        self.assertEqual(len(validation['blocking_dependencies']), 1)
        self.assertEqual(validation['blocking_dependencies'][0]['version'], '01.00')
    
    def test_family_dependency_summary(self):
        """Test getting dependency summary for document family"""
        doc = Document.objects.create(
            title='Test Document',
            document_number='SOP-2025-0001-v01.00',
            version_major=1,
            version_minor=0,
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='EFFECTIVE'
        )
        
        summary = doc.get_family_dependency_summary()
        
        self.assertEqual(summary['total_versions'], 1)
        self.assertEqual(len(summary['versions']), 1)
        self.assertEqual(summary['versions'][0]['dependents_count'], 0)
        self.assertEqual(summary['versions'][0]['dependencies_count'], 0)
