from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.utils import timezone
import os
import json

class Command(BaseCommand):
    help = (
        "Summarize post-restore health: file presence, checksum validity, "
        "workflow counts, and document type consistency. Optionally compare with a backup JSON."
    )

    def add_arguments(self, parser):
        parser.add_argument('--backup-json', type=str, help='Optional path to database_backup.json for expectations')
        parser.add_argument('--limit-checksums', type=int, default=200, help='Limit checksum recomputation for performance (0 = no limit)')

    def handle(self, *args, **options):
        backup_json = options.get('backup_json')
        limit_checksums = options.get('limit_checksums') or 0

        from apps.documents.models import Document
        try:
            from apps.workflows.models import DocumentWorkflow, DocumentTransition
            workflows_available = True
        except Exception:
            workflows_available = False
            DocumentWorkflow = None
            DocumentTransition = None

        expected_map = {}
        if backup_json and os.path.exists(backup_json):
            with open(backup_json, 'r') as f:
                try:
                    data = json.load(f)
                    for rec in data:
                        if rec.get('model') == 'documents.document':
                            flds = rec.get('fields', {})
                            num = flds.get('document_number')
                            dt = flds.get('document_type', [None])
                            dt_code = dt[0] if isinstance(dt, list) else None
                            if num and dt_code:
                                expected_map[num] = dt_code
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Failed to parse backup json: {e}"))

        total_docs = Document.objects.count()
        missing_files = 0
        checksum_mismatches = 0
        checked_checksums = 0
        type_none = 0
        type_mismatch_vs_backup = 0
        media_root = getattr(settings, 'MEDIA_ROOT', '/app/storage')

        # File presence + checksum verification (limited)
        docs = Document.objects.all().only('id','document_number','file_name','file_path','file_checksum','document_type')
        for doc in docs.iterator():
            fpath = doc.full_file_path
            if not fpath or not os.path.exists(fpath):
                missing_files += 1
            else:
                if limit_checksums == 0 or checked_checksums < limit_checksums:
                    try:
                        actual = doc.calculate_file_checksum()
                        checked_checksums += 1
                        if doc.file_checksum and actual and doc.file_checksum != actual:
                            checksum_mismatches += 1
                    except Exception:
                        pass
            if not getattr(doc, 'document_type', None):
                type_none += 1
            elif expected_map:
                exp = expected_map.get(doc.document_number)
                if exp and getattr(doc.document_type, 'code', None) and doc.document_type.code != exp:
                    type_mismatch_vs_backup += 1

        # Workflow counts
        wf_counts = {}
        if workflows_available:
            wf_counts['DocumentWorkflow'] = DocumentWorkflow.objects.count()
            wf_counts['DocumentTransition'] = DocumentTransition.objects.count()

        summary = {
            'timestamp': timezone.now().isoformat(),
            'media_root': media_root,
            'documents': {
                'total': total_docs,
                'missing_files': missing_files,
                'checksum_checked': checked_checksums,
                'checksum_mismatches': checksum_mismatches,
                'type_none': type_none,
                'type_mismatch_vs_backup': type_mismatch_vs_backup,
            },
            'workflows': wf_counts,
        }

        self.stdout.write(json.dumps(summary, indent=2))
        return 0
