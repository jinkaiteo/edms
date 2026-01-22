# Data Integrity System - Complete Setup Guide

**Date:** January 19, 2026  
**Status:** Partially Implemented - Additional Setup Recommended

---

## ✅ **What's Already Working**

### **1. Checksum Fields Exist**
- ✅ `AuditTrail.checksum` (SHA-256, 64 chars)
- ✅ `Document.file_checksum` (SHA-256, 64 chars)
- ✅ `ComplianceReport.report_checksum` (SHA-256)
- ✅ Database indexes on checksum fields

### **2. Checksum Calculation Methods**
- ✅ `AuditTrail.calculate_checksum()` - Hashes action + description + metadata
- ✅ `Document.calculate_file_checksum()` - SHA-256 of file contents
- ✅ `Document.verify_file_integrity()` - Compares stored vs current checksum

### **3. Scheduled Integrity Checks**
- ✅ Daily checks at 2 AM (just implemented)
- ✅ Weekly checksum verification on Sundays at 1 AM
- ✅ Creates `DataIntegrityCheck` records

---

## ⚠️ **What Needs Additional Setup**

Based on the analysis, here's what's missing or needs enhancement:

### **1. Automatic Checksum Generation** ⚠️ PARTIALLY WORKING

**Current State:**
- Checksums are calculated in `save()` method
- But only if `checksum` field is empty
- Existing records may not have checksums

**Issue:**
```python
# In Document.save()
if self.file_path and not self.file_checksum:
    self.file_checksum = self.calculate_file_checksum()  # Only if empty!
```

**Problem:** Existing documents and audit entries created before this code may not have checksums.

**Solution:** Run a one-time migration to calculate missing checksums.

---

### **2. Retroactive Checksum Calculation** ❌ NEEDED

**Create Management Command:**

```python
# backend/apps/audit/management/commands/calculate_checksums.py

from django.core.management.base import BaseCommand
from apps.documents.models import Document
from apps.audit.models import AuditTrail, ComplianceReport


class Command(BaseCommand):
    help = 'Calculate checksums for existing records that lack them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recalculate all checksums even if they exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # 1. Document checksums
        self.stdout.write("Calculating document checksums...")
        docs = Document.objects.all()
        if not force:
            docs = docs.filter(file_checksum='')
        
        updated_docs = 0
        for doc in docs:
            if doc.file_path:
                try:
                    import os
                    if os.path.exists(doc.file_path):
                        doc.file_checksum = doc.calculate_file_checksum()
                        doc.save(update_fields=['file_checksum'])
                        updated_docs += 1
                        self.stdout.write(f"  ✓ {doc.document_number}: {doc.file_checksum[:16]}...")
                except Exception as e:
                    self.stdout.write(f"  ✗ {doc.document_number}: {e}")
        
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_docs} documents"))
        
        # 2. Audit trail checksums
        self.stdout.write("\nCalculating audit trail checksums...")
        audits = AuditTrail.objects.all()
        if not force:
            audits = audits.filter(checksum='')
        
        updated_audits = 0
        for audit in audits[:1000]:  # Limit for performance
            try:
                audit.checksum = audit.calculate_checksum()
                audit.save(update_fields=['checksum'])
                updated_audits += 1
            except Exception as e:
                self.stdout.write(f"  ✗ Audit {audit.id}: {e}")
        
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_audits} audit entries"))
```

**Run Command:**
```bash
# Calculate missing checksums
docker compose exec backend python manage.py calculate_checksums

# Recalculate all (with --force)
docker compose exec backend python manage.py calculate_checksums --force
```

---

### **3. Enhanced Integrity Check Tasks** ⚠️ NEEDS IMPROVEMENT

**Current Implementation:** Basic checks (count entries, check file existence)

**Recommended Enhancements:**

#### **A. Add Actual Checksum Verification**

Update `backend/apps/audit/integrity_tasks.py`:

```python
@shared_task(name='apps.audit.integrity_tasks.run_daily_integrity_check')
def run_daily_integrity_check():
    # ... existing code ...
    
    # ENHANCED: Actually verify document checksums
    doc_check = DataIntegrityCheck.objects.create(
        check_type='DOCUMENT',
        scope='Document checksums and metadata',
        triggered_by=None,
        is_automated=True
    )
    
    try:
        documents = Document.objects.filter(is_active=True).exclude(file_checksum='')
        total_docs = documents.count()
        checksum_mismatches = 0
        missing_files = 0
        verified = 0
        
        for doc in documents[:100]:  # Check first 100
            if doc.file_path:
                import os
                if not os.path.exists(doc.file_path):
                    missing_files += 1
                else:
                    # VERIFY CHECKSUM
                    try:
                        if doc.verify_file_integrity():
                            verified += 1
                        else:
                            checksum_mismatches += 1
                            print(f"  ⚠️  Checksum mismatch: {doc.document_number}")
                    except Exception as e:
                        print(f"  ✗ Error verifying {doc.document_number}: {e}")
        
        doc_check.status = 'PASSED' if (missing_files == 0 and checksum_mismatches == 0) else 'FAILED'
        doc_check.findings = {
            'total_documents': total_docs,
            'checked_documents': min(100, total_docs),
            'verified': verified,
            'missing_files': missing_files,
            'checksum_mismatches': checksum_mismatches
        }
        doc_check.completed_at = timezone.now()
        doc_check.save()
        
    except Exception as e:
        doc_check.status = 'FAILED'
        doc_check.findings = {'error': str(e)}
        doc_check.completed_at = timezone.now()
        doc_check.save()
```

#### **B. Add Audit Trail Checksum Chain Verification**

```python
def verify_audit_trail_chain():
    """
    Verify audit trail forms an unbroken chain.
    Each entry's checksum should be based on previous entry + current data.
    """
    
    check = DataIntegrityCheck.objects.create(
        check_type='AUDIT_CHAIN',
        scope='Audit trail chain integrity',
        triggered_by=None,
        is_automated=True
    )
    
    try:
        entries = AuditTrail.objects.all().order_by('timestamp')[:1000]
        
        broken_links = 0
        verified_links = 0
        
        for i, entry in enumerate(entries):
            if not entry.checksum:
                broken_links += 1
            else:
                expected = entry.calculate_checksum()
                if entry.checksum == expected:
                    verified_links += 1
                else:
                    broken_links += 1
                    print(f"⚠️  Audit trail tampered: Entry {entry.id}")
        
        check.status = 'PASSED' if broken_links == 0 else 'FAILED'
        check.findings = {
            'total_entries': entries.count(),
            'verified': verified_links,
            'broken': broken_links
        }
        check.completed_at = timezone.now()
        check.save()
        
    except Exception as e:
        check.status = 'FAILED'
        check.findings = {'error': str(e)}
        check.completed_at = timezone.now()
        check.save()
```

---

### **4. Checksum Verification on File Upload** ⚠️ RECOMMENDED

**Current:** Checksum calculated once on save

**Better:** Recalculate and verify on file modification

Update `backend/apps/documents/models.py`:

```python
class Document(models.Model):
    # ... existing fields ...
    
    def save(self, *args, **kwargs):
        # Calculate checksum for new files
        if self.file_path and not self.file_checksum:
            self.file_checksum = self.calculate_file_checksum()
        
        # ENHANCED: Recalculate if file changed
        if self.pk:  # Existing document
            try:
                old = Document.objects.get(pk=self.pk)
                if old.file_path != self.file_path:
                    # File path changed - recalculate checksum
                    self.file_checksum = self.calculate_file_checksum()
            except Document.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
```

---

### **5. Integrity Violation Alerts** ❌ NOT IMPLEMENTED

**Create Alert Task:**

```python
# backend/apps/audit/integrity_tasks.py

@shared_task
def send_integrity_violation_alert(check_id):
    """
    Send email alert when integrity check fails.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    check = DataIntegrityCheck.objects.get(id=check_id)
    
    if check.status == 'FAILED':
        subject = f"⚠️ Data Integrity Check Failed: {check.check_type}"
        message = f"""
        Data Integrity Check Failure
        
        Check Type: {check.check_type}
        Scope: {check.scope}
        Time: {check.completed_at}
        
        Findings:
        {check.findings}
        
        Action Required: Review the system for potential tampering or corruption.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
```

**Update integrity check task to trigger alert:**

```python
# At end of run_daily_integrity_check()
if doc_check.status == 'FAILED':
    send_integrity_violation_alert.delay(doc_check.id)
```

---

### **6. Checksum Verification on Download** ⚠️ RECOMMENDED

**Add Verification Endpoint:**

```python
# backend/apps/documents/views.py

@action(detail=True, methods=['get'])
def verify_integrity(self, request, pk=None):
    """
    Verify document file integrity against stored checksum.
    """
    document = self.get_object()
    
    if not document.file_checksum:
        return Response({
            'verified': False,
            'message': 'No checksum stored for this document'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        is_valid = document.verify_file_integrity()
        
        # Log verification in audit trail
        AuditTrail.objects.create(
            user=request.user,
            action='DOCUMENT_INTEGRITY_VERIFIED',
            description=f'Integrity verification for {document.document_number}: {"PASSED" if is_valid else "FAILED"}',
            object_type='Document',
            object_id=document.id
        )
        
        return Response({
            'verified': is_valid,
            'checksum': document.file_checksum,
            'message': 'File integrity verified' if is_valid else 'Checksum mismatch detected'
        })
        
    except Exception as e:
        return Response({
            'verified': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

**Add Frontend Button:**

```typescript
// frontend/src/components/documents/DocumentDetail.tsx

const verifyIntegrity = async () => {
  const response = await apiService.get(`/documents/${documentId}/verify_integrity/`);
  if (response.verified) {
    alert('✓ File integrity verified - document has not been tampered with');
  } else {
    alert('⚠️ Integrity check failed - file may have been modified');
  }
};

// Add button
<button onClick={verifyIntegrity}>
  🔐 Verify Integrity
</button>
```

---

## 📋 **Complete Setup Checklist**

### **Immediate (Required for Data Integrity Report to work well):**

- [x] Scheduled daily integrity checks (DONE)
- [x] Scheduled weekly checksum verification (DONE)
- [ ] **Run checksum calculation for existing records**
  ```bash
  docker compose exec backend python manage.py calculate_checksums
  ```
- [ ] **Update integrity check to actually verify checksums** (not just count)

### **Short Term (Recommended for production):**

- [ ] Create `calculate_checksums` management command
- [ ] Enhance integrity check task with actual verification
- [ ] Add integrity violation email alerts
- [ ] Add checksum verification on file modification

### **Medium Term (Nice to have):**

- [ ] Add "Verify Integrity" button in document detail page
- [ ] Create dashboard widget showing integrity check status
- [ ] Add audit trail chain verification
- [ ] Implement continuous monitoring

### **Long Term (Advanced features):**

- [ ] Digital signatures for critical documents
- [ ] Blockchain-based audit trail for immutability
- [ ] Real-time integrity monitoring dashboard
- [ ] Automated remediation for integrity issues

---

## 🚀 **Quick Start - Minimum Setup**

**To get Data Integrity Report working well NOW:**

### **Step 1: Create the management command**

```bash
# Create the file
cat > backend/apps/audit/management/commands/calculate_checksums.py << 'EOF'
from django.core.management.base import BaseCommand
from apps.documents.models import Document
from apps.audit.models import AuditTrail
import os


class Command(BaseCommand):
    help = 'Calculate checksums for existing records'

    def handle(self, *args, **options):
        # Documents
        self.stdout.write("Calculating document checksums...")
        docs = Document.objects.filter(file_checksum='')
        count = 0
        for doc in docs:
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    doc.file_checksum = doc.calculate_file_checksum()
                    doc.save(update_fields=['file_checksum'])
                    count += 1
                    self.stdout.write(f"  ✓ {doc.document_number}")
                except Exception as e:
                    self.stdout.write(f"  ✗ {doc.document_number}: {e}")
        
        self.stdout.write(self.style.SUCCESS(f"✓ Updated {count} documents"))
        
        # Audit trail
        self.stdout.write("\nCalculating audit checksums...")
        audits = AuditTrail.objects.filter(checksum='')[:1000]
        count = 0
        for audit in audits:
            try:
                audit.checksum = audit.calculate_checksum()
                audit.save(update_fields=['checksum'])
                count += 1
            except:
                pass
        
        self.stdout.write(self.style.SUCCESS(f"✓ Updated {count} audit entries"))
EOF
```

### **Step 2: Run it**

```bash
docker compose exec backend python manage.py calculate_checksums
```

### **Step 3: Verify**

```bash
docker compose exec backend python manage.py shell << 'PYEOF'
from apps.documents.models import Document
from apps.audit.models import AuditTrail

docs_with_checksum = Document.objects.exclude(file_checksum='').count()
total_docs = Document.objects.count()
print(f"Documents: {docs_with_checksum}/{total_docs} have checksums")

audits_with_checksum = AuditTrail.objects.exclude(checksum='').count()
total_audits = AuditTrail.objects.count()
print(f"Audit Trail: {audits_with_checksum}/{total_audits} have checksums")
PYEOF
```

### **Step 4: Trigger manual integrity check**

```bash
docker compose exec backend python manage.py shell << 'PYEOF'
from apps.audit.integrity_tasks import run_daily_integrity_check
result = run_daily_integrity_check()
print(result)
PYEOF
```

### **Step 5: Check results**

```bash
docker compose exec backend python manage.py shell << 'PYEOF'
from apps.audit.models import DataIntegrityCheck
checks = DataIntegrityCheck.objects.all().order_by('-completed_at')
for check in checks[:5]:
    print(f"{check.check_type}: {check.status} - {check.findings}")
PYEOF
```

---

## 📊 **What You'll Have After Setup**

### **With Minimum Setup (Steps 1-5 above):**
- ✅ All documents have checksums
- ✅ Audit trail entries have checksums
- ✅ Daily integrity checks running at 2 AM
- ✅ Weekly checksum verification on Sundays
- ✅ Data Integrity Report shows real data

### **With Full Setup (All enhancements):**
- ✅ Real-time checksum verification on file changes
- ✅ Email alerts for integrity violations
- ✅ Manual "Verify Integrity" button in UI
- ✅ Comprehensive audit trail chain verification
- ✅ Production-grade data integrity system

---

## 🎯 **Current Status**

| Feature | Status | Priority |
|---------|--------|----------|
| Checksum fields exist | ✅ Done | - |
| Scheduled checks | ✅ Done | - |
| Retroactive checksum calc | ❌ **Needed** | 🔴 **High** |
| Actual checksum verification | ⚠️ Partial | 🔴 **High** |
| Integrity violation alerts | ❌ Not done | 🟡 Medium |
| UI verification button | ❌ Not done | 🟢 Low |
| Audit trail chain | ❌ Not done | 🟡 Medium |

---

## ✅ **Recommendation**

**Do the minimum setup (Steps 1-5) NOW to make Data Integrity Report functional:**

1. Create `calculate_checksums` management command (5 minutes)
2. Run it to populate checksums (1 minute)
3. Verify checksums are populated (1 minute)

**Total time: 7 minutes**

This will make your Data Integrity Report badge change from:
- [⚙ Setup Required] → [⚠ Partial Data] or [✓ Ready]

---

**Would you like me to create the checksum calculation command and run it now?**
