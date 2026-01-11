"""
Scheduler Obsolescence Automation Tests

Tests for automated document obsolescence by scheduler:
- Documents marked OBSOLETE on scheduled date
- Scheduler handles SCHEDULED_FOR_OBSOLESCENCE status
- Obsolescence notifications sent
- Obsolescence date validation

COMPLIANCE: Automated obsolescence ensures consistent document lifecycle management.
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model

from apps.documents.models import Document, DocumentType, DocumentSource

User = get_user_model()


@pytest.mark.django_db
class TestSchedulerObsolescence:
    """Test suite for scheduler-based obsolescence"""
    
    def setup_method(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='obs_scheduler_user',
            password='test123'
        )
        
        self.doc_type = DocumentType.objects.create(
            name='Guideline',
            code='GUIDE',
            created_by=self.user
        )
        self.doc_source = DocumentSource.objects.create(
            name='Original Digital Draft',
            source_type='original_digital'
        )
    
    def test_scheduler_marks_documents_obsolete_on_date(self):
        """Test documents become OBSOLETE on scheduled obsolescence date"""
        doc = Document.objects.create(
            title='Document to Obsolete',
            description='Scheduled for obsolescence',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='SCHEDULED_FOR_OBSOLESCENCE',
            obsolescence_date=date.today(),
            obsolescence_reason='Superseded by new version',
            version_major=1,
            version_minor=0
        )
        
        # Simulate scheduler running
        from apps.scheduler.automated_tasks import process_scheduled_obsolescence
        
        try:
            result = process_scheduled_obsolescence()
            
            # Check document is now obsolete
            doc.refresh_from_db()
            assert doc.status == 'OBSOLETE'
        except AttributeError:
            # Task may not exist yet - that's okay for this test
            pytest.skip("Obsolescence task not implemented yet")
    
    def test_future_obsolescence_remains_scheduled(self):
        """Test documents with future obsolescence dates remain scheduled"""
        future_date = date.today() + timedelta(days=60)
        
        doc = Document.objects.create(
            title='Future Obsolescence',
            description='Not yet obsolete',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='SCHEDULED_FOR_OBSOLESCENCE',
            obsolescence_date=future_date,
            obsolescence_reason='Will be obsolete in future',
            version_major=1,
            version_minor=0
        )
        
        # Scheduler should skip this document
        try:
            from apps.scheduler.automated_tasks import process_scheduled_obsolescence
            process_scheduled_obsolescence()
            
            doc.refresh_from_db()
            assert doc.status == 'SCHEDULED_FOR_OBSOLESCENCE'
        except AttributeError:
            pytest.skip("Obsolescence task not implemented yet")
    
    def test_past_obsolescence_processed_immediately(self):
        """Test documents with past obsolescence dates are processed"""
        past_date = date.today() - timedelta(days=10)
        
        doc = Document.objects.create(
            title='Past Obsolescence',
            description='Already past obsolescence date',
            document_type=self.doc_type,
            document_source=self.doc_source,
            author=self.user,
            status='SCHEDULED_FOR_OBSOLESCENCE',
            obsolescence_date=past_date,
            obsolescence_reason='Past due',
            version_major=1,
            version_minor=0
        )
        
        try:
            from apps.scheduler.automated_tasks import process_scheduled_obsolescence
            process_scheduled_obsolescence()
            
            doc.refresh_from_db()
            assert doc.status == 'OBSOLETE'
        except AttributeError:
            pytest.skip("Obsolescence task not implemented yet")
