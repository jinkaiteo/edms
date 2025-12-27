"""
End-to-end integration tests for complete backup and restoration flow.

Tests the full lifecycle:
1. Create test data (documents, workflows, transitions)
2. Generate backup package
3. Clear database (system_reinit)
4. Restore from backup
5. Verify all data restored correctly
"""

import os
import json
import tempfile
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from io import StringIO

from apps.documents.models import Document, DocumentType, DocumentSource
from apps.workflows.models_simple import DocumentWorkflow, DocumentTransition, DocumentState
from apps.backup.services import BackupService

User = get_user_model()


class CompleteRestorationFlowTests(TransactionTestCase):
    """Test complete backup → reinit → restore cycle."""
    
    fixtures = ['initial_users.json']
    
    def setUp(self):
        """Create comprehensive test data."""
        # Get/create infrastructure
        self.doc_type = DocumentType.objects.create(
            code='POLICY',
            name='Policy Document'
        )
        self.doc_source = DocumentSource.objects.create(
            code='INTERNAL',
            name='Internal'
        )
        
        # Create users
        self.author = User.objects.filter(username='author01').first()
        if not self.author:
            self.author = User.objects.create_user(
                username='author01',
                password='edms123',
                email='author01@example.com'
            )
        
        self.reviewer = User.objects.filter(username='reviewer01').first()
        if not self.reviewer:
            self.reviewer = User.objects.create_user(
                username='reviewer01',
                password='edms123',
                email='reviewer01@example.com'
            )
        
        # Get workflow states
        self.draft_state = DocumentState.objects.filter(code='DRAFT').first()
        self.review_state = DocumentState.objects.filter(code='PENDING_REVIEW').first()
        self.approved_state = DocumentState.objects.filter(code='APPROVED').first()
        
    def test_complete_restoration_cycle(self):
        """Test full backup → reinit → restore cycle."""
        
        # === PHASE 1: Create Test Data ===
        print("\n📝 PHASE 1: Creating test data...")
        
        # Create document
        doc = Document.objects.create(
            document_number='POL-2025-TEST-v01.00',
            title='Test Policy Document',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='DRAFT',
            version_major=1,
            version_minor=0,
            content='Test policy content'
        )
        
        # Create workflow
        workflow = DocumentWorkflow.objects.create(
            document=doc,
            workflow_type='REVIEW',
            current_state=self.draft_state,
            initiated_by=self.author,
            is_terminated=False
        )
        
        # Create transitions
        transition1 = DocumentTransition.objects.create(
            workflow=workflow,
            from_state=self.draft_state,
            to_state=self.review_state,
            transitioned_by=self.author,
            comment='Submitting for review',
            transition_data={'action': 'submit'}
        )
        
        transition2 = DocumentTransition.objects.create(
            workflow=workflow,
            from_state=self.review_state,
            to_state=self.approved_state,
            transitioned_by=self.reviewer,
            comment='Approved',
            transition_data={'action': 'approve'}
        )
        
        # Update workflow to approved state
        workflow.current_state = self.approved_state
        workflow.save()
        
        print(f"✅ Created document: {doc.document_number}")
        print(f"✅ Created workflow with {DocumentTransition.objects.filter(workflow=workflow).count()} transitions")
        
        # === PHASE 2: Create Backup ===
        print("\n💾 PHASE 2: Creating backup package...")
        
        backup_service = BackupService()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, 'test_backup.tar.gz')
            
            try:
                # Create backup
                result = backup_service.create_backup(
                    backup_type='export',
                    output_path=backup_path,
                    description='Test backup'
                )
                
                self.assertTrue(os.path.exists(backup_path))
                backup_size = os.path.getsize(backup_path)
                print(f"✅ Backup created: {backup_size} bytes")
                
                # === PHASE 3: Capture Current State ===
                original_doc_count = Document.objects.count()
                original_workflow_count = DocumentWorkflow.objects.count()
                original_transition_count = DocumentTransition.objects.count()
                original_user_count = User.objects.count()
                
                print(f"\n📊 Original state:")
                print(f"  Documents: {original_doc_count}")
                print(f"  Workflows: {original_workflow_count}")
                print(f"  Transitions: {original_transition_count}")
                print(f"  Users: {original_user_count}")
                
                # === PHASE 4: System Reinit ===
                print("\n🔄 PHASE 4: Running system_reinit...")
                
                out = StringIO()
                call_command('system_reinit', '--confirm', '--preserve-backups', stdout=out)
                
                # Verify data cleared
                self.assertEqual(Document.objects.count(), 0)
                self.assertEqual(DocumentWorkflow.objects.count(), 0)
                self.assertEqual(DocumentTransition.objects.count(), 0)
                print("✅ System reinitialized (business data cleared)")
                
                # === PHASE 5: Restore ===
                print("\n📥 PHASE 5: Restoring from backup...")
                
                out = StringIO()
                call_command('restore_from_package', backup_path, '--type', 'full', '--confirm', stdout=out)
                
                # === PHASE 6: Verify Restoration ===
                print("\n✅ PHASE 6: Verifying restoration...")
                
                # Verify document counts
                restored_doc_count = Document.objects.count()
                restored_workflow_count = DocumentWorkflow.objects.count()
                restored_transition_count = DocumentTransition.objects.count()
                restored_user_count = User.objects.count()
                
                print(f"\n📊 Restored state:")
                print(f"  Documents: {restored_doc_count}")
                print(f"  Workflows: {restored_workflow_count}")
                print(f"  Transitions: {restored_transition_count}")
                print(f"  Users: {restored_user_count}")
                
                # Assertions
                self.assertEqual(restored_doc_count, original_doc_count, "Document count mismatch")
                self.assertEqual(restored_workflow_count, original_workflow_count, "Workflow count mismatch")
                self.assertEqual(restored_transition_count, original_transition_count, "Transition count mismatch")
                
                # Verify specific document
                restored_doc = Document.objects.filter(document_number='POL-2025-TEST-v01.00').first()
                self.assertIsNotNone(restored_doc, "Test document not found after restore")
                self.assertEqual(restored_doc.title, 'Test Policy Document')
                self.assertEqual(restored_doc.status, 'DRAFT')
                
                # Verify workflow
                restored_workflow = DocumentWorkflow.objects.filter(document=restored_doc).first()
                self.assertIsNotNone(restored_workflow, "Workflow not found after restore")
                self.assertEqual(restored_workflow.workflow_type, 'REVIEW')
                self.assertEqual(restored_workflow.current_state.code, 'APPROVED')
                
                # Verify transitions
                restored_transitions = DocumentTransition.objects.filter(workflow=restored_workflow).order_by('id')
                self.assertEqual(restored_transitions.count(), 2, "Transition count mismatch")
                
                # Verify transition details
                t1 = restored_transitions[0]
                self.assertEqual(t1.from_state.code, 'DRAFT')
                self.assertEqual(t1.to_state.code, 'PENDING_REVIEW')
                self.assertEqual(t1.comment, 'Submitting for review')
                
                t2 = restored_transitions[1]
                self.assertEqual(t2.from_state.code, 'PENDING_REVIEW')
                self.assertEqual(t2.to_state.code, 'APPROVED')
                self.assertEqual(t2.comment, 'Approved')
                
                print("\n🎉 ALL VERIFICATIONS PASSED!")
                
            except Exception as e:
                print(f"\n❌ Test failed: {e}")
                raise


class MultipleDocumentWorkflowTests(TransactionTestCase):
    """Test restoration with multiple documents and complex workflow states."""
    
    fixtures = ['initial_users.json']
    
    def setUp(self):
        """Set up test infrastructure."""
        self.doc_type = DocumentType.objects.create(code='SOP', name='SOP')
        self.doc_source = DocumentSource.objects.create(code='INT', name='Internal')
        self.author = User.objects.first()
        self.draft_state = DocumentState.objects.filter(code='DRAFT').first()
        self.effective_state = DocumentState.objects.filter(code='EFFECTIVE').first()
    
    def test_restore_multiple_workflows(self):
        """Test restoration of multiple documents with different workflow states."""
        
        # Create multiple documents with different workflow states
        documents = []
        workflows = []
        
        for i in range(3):
            doc = Document.objects.create(
                document_number=f'SOP-2025-000{i+1}-v01.00',
                title=f'SOP Document {i+1}',
                document_type=self.doc_type,
                document_source=self.doc_source,
                author=self.author,
                status='DRAFT'
            )
            documents.append(doc)
            
            # Create workflow with different states
            state = self.draft_state if i % 2 == 0 else self.effective_state
            workflow = DocumentWorkflow.objects.create(
                document=doc,
                workflow_type='REVIEW',
                current_state=state,
                initiated_by=self.author
            )
            workflows.append(workflow)
        
        print(f"\n✅ Created {len(documents)} documents with workflows")
        
        # Create backup
        backup_service = BackupService()
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, 'multi_doc_backup.tar.gz')
            
            backup_service.create_backup(
                backup_type='export',
                output_path=backup_path
            )
            
            # Clear data
            call_command('system_reinit', '--confirm', '--preserve-backups', stdout=StringIO())
            
            self.assertEqual(Document.objects.count(), 0)
            self.assertEqual(DocumentWorkflow.objects.count(), 0)
            
            # Restore
            call_command('restore_from_package', backup_path, '--type', 'full', '--confirm', stdout=StringIO())
            
            # Verify all documents restored
            self.assertEqual(Document.objects.count(), 3)
            self.assertEqual(DocumentWorkflow.objects.count(), 3)
            
            # Verify each workflow state
            for i, original_wf in enumerate(workflows):
                doc_num = f'SOP-2025-000{i+1}-v01.00'
                restored_doc = Document.objects.get(document_number=doc_num)
                restored_wf = DocumentWorkflow.objects.get(document=restored_doc)
                
                expected_state = self.draft_state.code if i % 2 == 0 else self.effective_state.code
                self.assertEqual(restored_wf.current_state.code, expected_state)
            
            print("✅ All workflows restored with correct states")


class WorkflowHistoryPreservationTests(TransactionTestCase):
    """Test that complete workflow history is preserved through restoration."""
    
    fixtures = ['initial_users.json']
    
    def setUp(self):
        """Set up test environment."""
        self.doc_type = DocumentType.objects.create(code='TEST', name='Test')
        self.doc_source = DocumentSource.objects.create(code='TEST', name='Test')
        self.author = User.objects.first()
        
        # Get all states for complete workflow
        self.states = {
            'DRAFT': DocumentState.objects.filter(code='DRAFT').first(),
            'REVIEW': DocumentState.objects.filter(code='PENDING_REVIEW').first(),
            'APPROVAL': DocumentState.objects.filter(code='PENDING_APPROVAL').first(),
            'APPROVED': DocumentState.objects.filter(code='APPROVED').first(),
            'EFFECTIVE': DocumentState.objects.filter(code='EFFECTIVE').first(),
        }
    
    def test_complete_workflow_history_preservation(self):
        """Test that complete workflow transition history is preserved."""
        
        # Create document
        doc = Document.objects.create(
            document_number='TEST-2025-HIST-v01.00',
            title='Workflow History Test',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.author,
            status='DRAFT'
        )
        
        # Create workflow
        workflow = DocumentWorkflow.objects.create(
            document=doc,
            workflow_type='REVIEW',
            current_state=self.states['DRAFT'],
            initiated_by=self.author
        )
        
        # Create complete workflow history
        transitions_data = [
            ('DRAFT', 'REVIEW', 'Submit for review'),
            ('REVIEW', 'APPROVAL', 'Review approved'),
            ('APPROVAL', 'APPROVED', 'Final approval'),
            ('APPROVED', 'EFFECTIVE', 'Made effective'),
        ]
        
        for from_state_code, to_state_code, comment in transitions_data:
            DocumentTransition.objects.create(
                workflow=workflow,
                from_state=self.states[from_state_code],
                to_state=self.states[to_state_code],
                transitioned_by=self.author,
                comment=comment
            )
        
        workflow.current_state = self.states['EFFECTIVE']
        workflow.save()
        
        original_transition_count = DocumentTransition.objects.filter(workflow=workflow).count()
        print(f"\n✅ Created workflow with {original_transition_count} transitions")
        
        # Backup and restore
        backup_service = BackupService()
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, 'history_backup.tar.gz')
            
            backup_service.create_backup(backup_type='export', output_path=backup_path)
            call_command('system_reinit', '--confirm', '--preserve-backups', stdout=StringIO())
            call_command('restore_from_package', backup_path, '--type', 'full', '--confirm', stdout=StringIO())
            
            # Verify complete history
            restored_doc = Document.objects.get(document_number='TEST-2025-HIST-v01.00')
            restored_workflow = DocumentWorkflow.objects.get(document=restored_doc)
            restored_transitions = DocumentTransition.objects.filter(workflow=restored_workflow).order_by('id')
            
            self.assertEqual(restored_transitions.count(), original_transition_count)
            self.assertEqual(restored_workflow.current_state.code, 'EFFECTIVE')
            
            # Verify each transition preserved
            for i, (from_code, to_code, comment) in enumerate(transitions_data):
                transition = restored_transitions[i]
                self.assertEqual(transition.from_state.code, from_code)
                self.assertEqual(transition.to_state.code, to_code)
                self.assertEqual(transition.comment, comment)
            
            print("✅ Complete workflow history preserved through restoration")
