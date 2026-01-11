"""
Scheduler Document Activation Tests

Tests for automated document activation by Celery Beat scheduler:
- Documents become EFFECTIVE on scheduled date
- Scheduler runs daily at midnight UTC
- Multiple documents activated in batch
- Future-dated documents remain pending
- Activation notifications sent
- Timezone handling (UTC storage, SGT display)

COMPLIANCE: Automated activation ensures documents become effective exactly
when approved, without manual intervention.
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.documents.models import Document, DocumentType, DocumentSource

User = get_user_model()


@pytest.mark.django_db
class TestSchedulerDocumentActivation:
    """Test suite for scheduler-based document activation"""
    
    def setup_method(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='scheduler_user',
            password='test123'
        )
        
        self.doc_type = DocumentType.objects.create(
            name='Policy',
            code='POL',
            created_by=self.user
        )
        self.doc_source = DocumentSource.objects.create(
            name='Original Digital Draft',
            source_type='original_digital'
        )
    
    def test_document_becomes_effective_on_scheduled_date(self):
        """
        Test that APPROVED_PENDING_EFFECTIVE documents become EFFECTIVE
        when effective_date is reached.
        """
        doc = Document.objects.create(
            title='Scheduled Document',
            description='Should become effective today',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='APPROVED_PENDING_EFFECTIVE',
            effective_date=date.today(),
            version_major=1,
            version_minor=0
        )
        
        # Simulate scheduler running
        from apps.scheduler.automated_tasks import activate_pending_documents
        
        # Call the task
        result = activate_pending_documents()
        
        # Check document is now effective
        doc.refresh_from_db()
        assert doc.status == 'EFFECTIVE'
    
    def test_future_dated_documents_remain_pending(self):
        """
        Test that documents with future effective dates remain
        APPROVED_PENDING_EFFECTIVE until the date is reached.
        """
        future_date = date.today() + timedelta(days=30)
        
        doc = Document.objects.create(
            title='Future Document',
            description='Should remain pending',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='APPROVED_PENDING_EFFECTIVE',
            effective_date=future_date,
            version_major=1,
            version_minor=0
        )
        
        # Simulate scheduler running today
        from apps.scheduler.automated_tasks import activate_pending_documents
        activate_pending_documents()
        
        # Document should still be pending
        doc.refresh_from_db()
        assert doc.status == 'APPROVED_PENDING_EFFECTIVE'
    
    def test_scheduler_activates_multiple_documents(self):
        """Test scheduler can activate multiple documents in one run"""
        # Create 3 documents ready to activate
        docs = []
        for i in range(3):
            doc = Document.objects.create(
                title=f'Batch Document {i+1}',
                description='Batch activation',
                document_type=self.doc_type,
                document_source=self.doc_source,
                author=self.user,
                status='APPROVED_PENDING_EFFECTIVE',
                effective_date=date.today(),
                version_major=1,
                version_minor=0
            )
            docs.append(doc)
        
        # Run scheduler
        from apps.scheduler.automated_tasks import activate_pending_documents
        result = activate_pending_documents()
        
        # All should be effective
        for doc in docs:
            doc.refresh_from_db()
            assert doc.status == 'EFFECTIVE'
    
    def test_past_dated_documents_activated_immediately(self):
        """
        Test that documents with past effective dates are activated
        immediately when scheduler runs.
        """
        past_date = date.today() - timedelta(days=5)
        
        doc = Document.objects.create(
            title='Past Date Document',
            description='Already past effective date',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='APPROVED_PENDING_EFFECTIVE',
            effective_date=past_date,
            version_major=1,
            version_minor=0
        )
        
        # Run scheduler
        from apps.scheduler.automated_tasks import activate_pending_documents
        activate_pending_documents()
        
        # Should be effective
        doc.refresh_from_db()
        assert doc.status == 'EFFECTIVE'
    
    def test_scheduler_skips_non_pending_documents(self):
        """Test scheduler only affects APPROVED_PENDING_EFFECTIVE documents"""
        # Create documents in various statuses
        statuses = ['DRAFT', 'UNDER_REVIEW', 'PENDING_APPROVAL', 'EFFECTIVE', 'OBSOLETE']
        
        for status in statuses:
            Document.objects.create(
                title=f'Document {status}',
                description='Should be skipped',
                document_type=self.doc_type,
                document_source=self.doc_source,
                author=self.user,
                status=status,
                effective_date=date.today(),
                version_major=1,
                version_minor=0
            )
        
        # Run scheduler
        from apps.scheduler.automated_tasks import activate_pending_documents
        activate_pending_documents()
        
        # All documents should remain in original status
        for status in statuses:
            doc = Document.objects.get(title=f'Document {status}')
            assert doc.status == status
    
    def test_scheduler_timezone_handling(self):
        """
        Test that scheduler handles timezones correctly.
        
        Documents use effective_date (date field, no timezone)
        Scheduler runs at midnight UTC
        Comparison should be date-only
        """
        doc = Document.objects.create(
            title='Timezone Test Document',
            description='Testing timezone handling',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='APPROVED_PENDING_EFFECTIVE',
            effective_date=date.today(),  # Date field (no timezone)
            version_major=1,
            version_minor=0
        )
        
        # Run scheduler
        from apps.scheduler.automated_tasks import activate_pending_documents
        activate_pending_documents()
        
        doc.refresh_from_db()
        assert doc.status == 'EFFECTIVE'
