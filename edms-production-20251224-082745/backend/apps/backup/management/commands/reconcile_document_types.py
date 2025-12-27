from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
import json
import os

class Command(BaseCommand):
    help = "Reconcile DocumentType bindings for Documents using a backup JSON (database_backup.json) as source of truth."

    def add_arguments(self, parser):
        parser.add_argument('--backup-json', type=str, required=True, help='Path to database_backup.json')

    def handle(self, *args, **options):
        backup_json = options['backup_json']
        if not os.path.exists(backup_json):
            self.stderr.write(self.style.ERROR(f"Backup JSON not found: {backup_json}"))
            return 1
        from apps.documents.models import Document, DocumentType
        from django.contrib.auth import get_user_model
        User = get_user_model()

        with open(backup_json, 'r') as f:
            data = json.load(f)

        # Build expected mapping: document_number -> document_type_code
        expected = {}
        for rec in data:
            if rec.get('model') == 'documents.document':
                fields = rec.get('fields', {})
                num = fields.get('document_number')
                dtype_code = None
                dtf = fields.get('document_type', [None])
                if isinstance(dtf, list):
                    dtype_code = dtf[0]
                if num and dtype_code:
                    expected[num] = dtype_code

        fixed = 0
        missing_types = set()
        with transaction.atomic():
            for doc in Document.objects.all():
                exp_code = expected.get(doc.document_number)
                if not exp_code:
                    continue
                if doc.document_type and doc.document_type.code == exp_code:
                    continue
                # find or create type by code (case-insensitive fallback)
                target = DocumentType.objects.filter(code=exp_code).first() or \
                         DocumentType.objects.filter(code__iexact=exp_code).first()
                if not target:
                    missing_types.add(exp_code)
                    target = DocumentType.objects.create(code=exp_code, name=exp_code)
                doc.document_type = target
                doc.save(update_fields=['document_type'])
                fixed += 1

        self.stdout.write(self.style.SUCCESS(f"Reconciled document types for {fixed} documents"))
        if missing_types:
            self.stdout.write(self.style.WARNING(f"Created missing types: {', '.join(sorted(missing_types))}"))
        return 0
