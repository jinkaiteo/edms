"""
Comprehensive test suite for workflow history restoration.

Tests cover:
1. Natural key resolution for all workflow-related models
2. Foreign key resolution for workflow dependencies
3. Complete workflow restoration flow
4. Edge cases and error handling
"""

import json
import tempfile
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.backup.restore_processor import EnhancedRestoreProcessor
from apps.documents.models import Document, DocumentType, DocumentSource
from apps.workflows.models import WorkflowType
from apps.workflows.models_simple import (
    DocumentWorkflow, 
    DocumentTransition, 
    DocumentState
)
from apps.users.models import Role

User = get_user_model()


class NaturalKeyResolutionTests(TestCase):
    """Test natural key resolution for workflow-related models."""
    
    fixtures = ['initial_users.json']
    
    def setUp(self):
        """Set up test data."""
        self.processor = EnhancedRestoreProcessor()
        
        # Create test document
        self.doc_type = DocumentType.objects.create(
            code='TEST',
            name='Test Document'
        )
        self.doc_source = DocumentSource.objects.create(
            code='TEST',
            name='Test Source'
        )
        self.user = User.objects.first()
        
        self.document = Document.objects.create(
            document_number='TEST-2025-0001-v01.00',
            title='Test Document',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='DRAFT'
        )
        
        # Create workflow state
        self.state = DocumentState.objects.filter(code='DRAFT').first()
        
    def test_resolve_document_natural_key(self):
        """Test Document natural key resolution by document_number."""
        natural_key = ['TEST-2025-0001-v01.00']
        resolved = self.processor._resolve_document_natural_key(natural_key)
        
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.document_number, 'TEST-2025-0001-v01.00')
        self.assertEqual(resolved.id, self.document.id)
    
    def test_resolve_document_natural_key_nonexistent(self):
        """Test Document natural key resolution for nonexistent document."""
        natural_key = ['NONEXISTENT-2025-0001-v01.00']
        resolved = self.processor._resolve_document_natural_key(natural_key)
        
        self.assertIsNone(resolved)
    
    def test_resolve_documentstate_natural_key(self):
        """Test DocumentState natural key resolution by code."""
        natural_key = ['DRAFT']
        resolved = self.processor._resolve_document_state_natural_key(natural_key)
        
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.code, 'DRAFT')
    
    def test_resolve_user_natural_key(self):
        """Test User natural key resolution by username."""
        natural_key = [self.user.username]
        resolved = self.processor._resolve_user_natural_key(natural_key)
        
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.username, self.user.username)
    
    def test_resolve_documentworkflow_natural_key(self):
        """Test DocumentWorkflow natural key resolution."""
        # Create a workflow first
        workflow = DocumentWorkflow.objects.create(
            document=self.document,
            workflow_type='REVIEW',
            current_state=self.state,
            initiated_by=self.user
        )
        
        natural_key = ['TEST-2025-0001-v01.00', 'REVIEW']
        resolved = self.processor._resolve_documentworkflow_natural_key(natural_key)
        
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.id, workflow.id)
        self.assertEqual(resolved.document.document_number, 'TEST-2025-0001-v01.00')


class WorkflowRestorationIntegrationTests(TransactionTestCase):
    """Integration tests for complete workflow restoration flow."""
    
    fixtures = ['initial_users.json']
    
    def setUp(self):
        """Set up test environment."""
        self.processor = EnhancedRestoreProcessor()
        
        # Create test infrastructure
        self.doc_type = DocumentType.objects.create(
            code='TEST',
            name='Test Document'
        )
        self.doc_source = DocumentSource.objects.create(
            code='TEST',
            name='Test Source'
        )
        self.user = User.objects.first()
        self.draft_state = DocumentState.objects.filter(code='DRAFT').first()
        self.review_state = DocumentState.objects.filter(code='PENDING_REVIEW').first()
        
    def test_restore_document_with_workflow(self):
        """Test restoring a document with associated workflow."""
        # Create backup data structure
        backup_data = [
            {
                "model": "documents.document",
                "pk": None,
                "fields": {
                    "document_number": "TEST-2025-0001-v01.00",
                    "title": "Test Document",
                    "document_type": ["TEST"],
                    "document_source": ["TEST"],
                    "author": [self.user.username],
                    "status": "DRAFT",
                    "version_major": 1,
                    "version_minor": 0,
                    "content": "Test content"
                }
            },
            {
                "model": "workflows.documentworkflow",
                "pk": None,
                "fields": {
                    "document": ["TEST-2025-0001-v01.00"],
                    "workflow_type": "REVIEW",
                    "current_state": ["DRAFT"],
                    "initiated_by": [self.user.username],
                    "workflow_data": {},
                    "is_terminated": False
                }
            }
        ]
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(backup_data, f)
            temp_path = f.name
        
        try:
            # Restore
            result = self.processor.process_backup_data(temp_path)
            
            # Verify document was created
            doc = Document.objects.filter(document_number='TEST-2025-0001-v01.00').first()
            self.assertIsNotNone(doc)
            self.assertEqual(doc.title, 'Test Document')
            
            # Verify workflow was created
            workflow = DocumentWorkflow.objects.filter(document=doc).first()
            self.assertIsNotNone(workflow)
            self.assertEqual(workflow.workflow_type, 'REVIEW')
            self.assertEqual(workflow.current_state.code, 'DRAFT')
            self.assertEqual(workflow.initiated_by.id, self.user.id)
            
        finally:
            import os
            os.unlink(temp_path)
    
    def test_restore_workflow_with_transitions(self):
        """Test restoring workflow with multiple transitions."""
        # Create document first
        doc = Document.objects.create(
            document_number='TEST-2025-0002-v01.00',
            title='Test Document 2',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='DRAFT'
        )
        
        # Create backup data with workflow and transitions
        backup_data = [
            {
                "model": "workflows.documentworkflow",
                "pk": None,
                "fields": {
                    "document": ["TEST-2025-0002-v01.00"],
                    "workflow_type": "REVIEW",
                    "current_state": ["PENDING_REVIEW"],
                    "initiated_by": [self.user.username],
                    "workflow_data": {},
                    "is_terminated": False
                }
            },
            {
                "model": "workflows.documenttransition",
                "pk": None,
                "fields": {
                    "workflow": ["TEST-2025-0002-v01.00", "REVIEW", 1],
                    "from_state": ["DRAFT"],
                    "to_state": ["PENDING_REVIEW"],
                    "transitioned_by": [self.user.username],
                    "comment": "Submitting for review",
                    "transition_data": {}
                }
            }
        ]
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(backup_data, f)
            temp_path = f.name
        
        try:
            # Restore
            result = self.processor.process_backup_data(temp_path)
            
            # Verify workflow
            workflow = DocumentWorkflow.objects.filter(document=doc).first()
            self.assertIsNotNone(workflow)
            self.assertEqual(workflow.current_state.code, 'PENDING_REVIEW')
            
            # Verify transition
            transitions = DocumentTransition.objects.filter(workflow=workflow)
            self.assertEqual(transitions.count(), 1)
            
            transition = transitions.first()
            self.assertEqual(transition.from_state.code, 'DRAFT')
            self.assertEqual(transition.to_state.code, 'PENDING_REVIEW')
            self.assertEqual(transition.comment, 'Submitting for review')
            
        finally:
            import os
            os.unlink(temp_path)
    
    def test_restore_with_missing_document(self):
        """Test workflow restoration gracefully fails when document doesn't exist."""
        backup_data = [
            {
                "model": "workflows.documentworkflow",
                "pk": None,
                "fields": {
                    "document": ["NONEXISTENT-2025-0001-v01.00"],
                    "workflow_type": "REVIEW",
                    "current_state": ["DRAFT"],
                    "initiated_by": [self.user.username],
                    "workflow_data": {},
                    "is_terminated": False
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(backup_data, f)
            temp_path = f.name
        
        try:
            # Restore should handle gracefully
            result = self.processor.process_backup_data(temp_path)
            
            # Workflow should not be created
            workflow_count = DocumentWorkflow.objects.count()
            self.assertEqual(workflow_count, 0)
            
        finally:
            import os
            os.unlink(temp_path)


class PostReinitWorkflowRestorationTests(TransactionTestCase):
    """Test workflow restoration after system_reinit (with infrastructure preserved)."""
    
    fixtures = ['initial_users.json']
    
    def setUp(self):
        """Set up preserved infrastructure."""
        self.processor = EnhancedRestoreProcessor()
        self.processor.post_reinit_mode = True
        
        # Infrastructure is preserved during system_reinit
        self.doc_type = DocumentType.objects.create(
            code='TEST',
            name='Test Document'
        )
        self.doc_source = DocumentSource.objects.create(
            code='TEST',
            name='Test Source'
        )
        self.draft_state = DocumentState.objects.filter(code='DRAFT').first()
        self.user = User.objects.first()
    
    def test_skip_preserved_infrastructure(self):
        """Test that preserved infrastructure is not duplicated."""
        # Try to restore infrastructure that already exists
        backup_data = [
            {
                "model": "workflows.documentstate",
                "pk": None,
                "fields": {
                    "code": "DRAFT",
                    "name": "Draft",
                    "description": "Draft state"
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(backup_data, f)
            temp_path = f.name
        
        try:
            initial_count = DocumentState.objects.count()
            
            # Restore
            result = self.processor.process_backup_data(temp_path)
            
            # Count should not increase (infrastructure preserved)
            final_count = DocumentState.objects.count()
            self.assertEqual(initial_count, final_count)
            
        finally:
            import os
            os.unlink(temp_path)
    
    def test_restore_business_data_post_reinit(self):
        """Test business data restoration in post-reinit mode."""
        backup_data = [
            {
                "model": "documents.document",
                "pk": None,
                "fields": {
                    "document_number": "TEST-2025-0003-v01.00",
                    "title": "Post-Reinit Test",
                    "document_type": ["TEST"],
                    "document_source": ["TEST"],
                    "author": [self.user.username],
                    "status": "DRAFT",
                    "version_major": 1,
                    "version_minor": 0
                }
            },
            {
                "model": "workflows.documentworkflow",
                "pk": None,
                "fields": {
                    "document": ["TEST-2025-0003-v01.00"],
                    "workflow_type": "REVIEW",
                    "current_state": ["DRAFT"],
                    "initiated_by": [self.user.username],
                    "workflow_data": {},
                    "is_terminated": False
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(backup_data, f)
            temp_path = f.name
        
        try:
            # Restore
            result = self.processor.process_backup_data(temp_path)
            
            # Verify document created
            doc = Document.objects.filter(document_number='TEST-2025-0003-v01.00').first()
            self.assertIsNotNone(doc)
            
            # Verify workflow created
            workflow = DocumentWorkflow.objects.filter(document=doc).first()
            self.assertIsNotNone(workflow)
            
        finally:
            import os
            os.unlink(temp_path)


class EdgeCaseTests(TestCase):
    """Test edge cases and error scenarios."""
    
    fixtures = ['initial_users.json']
    
    def setUp(self):
        """Set up test environment."""
        self.processor = EnhancedRestoreProcessor()
    
    def test_empty_natural_key(self):
        """Test handling of empty natural key arrays."""
        result = self.processor._resolve_document_natural_key([])
        self.assertIsNone(result)
    
    def test_invalid_natural_key_format(self):
        """Test handling of invalid natural key format."""
        result = self.processor._resolve_document_natural_key(None)
        self.assertIsNone(result)
    
    def test_workflow_with_null_fields(self):
        """Test workflow restoration with optional null fields."""
        doc_type = DocumentType.objects.create(code='TEST', name='Test')
        doc_source = DocumentSource.objects.create(code='TEST', name='Test')
        user = User.objects.first()
        state = DocumentState.objects.filter(code='DRAFT').first()
        
        doc = Document.objects.create(
            document_number='TEST-2025-0004-v01.00',
            title='Test',
            document_type=doc_type,
            document_source=doc_source,
            author=user,
            status='DRAFT'
        )
        
        backup_data = [
            {
                "model": "workflows.documentworkflow",
                "pk": None,
                "fields": {
                    "document": ["TEST-2025-0004-v01.00"],
                    "workflow_type": "REVIEW",
                    "current_state": ["DRAFT"],
                    "initiated_by": [user.username],
                    "due_date": None,  # Null optional field
                    "workflow_data": {},
                    "is_terminated": False
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(backup_data, f)
            temp_path = f.name
        
        try:
            result = self.processor.process_backup_data(temp_path)
            workflow = DocumentWorkflow.objects.filter(document=doc).first()
            self.assertIsNotNone(workflow)
            self.assertIsNone(workflow.due_date)
        finally:
            import os
            os.unlink(temp_path)
