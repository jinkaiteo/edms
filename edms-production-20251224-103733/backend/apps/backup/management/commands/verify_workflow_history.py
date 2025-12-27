from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from typing import Dict, List
import json
import os

class Command(BaseCommand):
    help = "Verify that restored workflow history in DB matches the workflow history in a backup JSON (database_backup.json)."

    def add_arguments(self, parser):
        parser.add_argument('--backup-json', type=str, required=True, help='Path to database_backup.json to compare against')
        parser.add_argument('--limit', type=int, default=0, help='Optional limit of documents to check (0 = all)')
        parser.add_argument('--verbose', action='store_true', help='Print per-document details of differences')

    def handle(self, *args, **options):
        backup_json = options['backup_json']
        limit = options['limit']
        verbose = options['verbose']

        if not os.path.exists(backup_json):
            # Try common default path relative to project root
            default_path = os.path.abspath(os.path.join(os.getcwd(), 'test_doc', 'database', 'database_backup.json'))
            if os.path.exists(default_path):
                backup_json = default_path
                self.stdout.write(self.style.WARNING(f"Backup JSON not found at provided path. Using default: {backup_json}"))
            else:
                from django.core.management.base import CommandError
                raise CommandError(f"Backup JSON not found: {backup_json}")

        from apps.workflows.models_simple import DocumentWorkflow, DocumentTransition, DocumentState
        from apps.documents.models import Document

        # Load backup data
        with open(backup_json, 'r') as f:
            data = json.load(f)

        # Extract backup workflows and transitions keyed by document_number
        backup_wf: Dict[str, dict] = {}
        backup_tr: Dict[str, List[dict]] = {}
        for rec in data:
            model = rec.get('model')
            fields = rec.get('fields', {})
            if model == 'workflows.documentworkflow':
                doc_num = (fields.get('document', [None])[0] or '').strip() or None
                if doc_num:
                    backup_wf[doc_num] = {
                        'current_state': (fields.get('current_state', [None])[0] or None),
                        'workflow_type': (fields.get('workflow_type', [None])[0] or None),
                        'is_terminated': fields.get('is_terminated', False)
                    }
            elif model == 'workflows.documenttransition':
                doc_num = (fields.get('workflow', [None])[0] or '').strip() or None
                if doc_num:
                    backup_tr.setdefault(doc_num, []).append({
                        'from_state': (fields.get('from_state', [None])[0] or None),
                        'to_state': (fields.get('to_state', [None])[0] or None),
                        'transitioned_at': fields.get('transitioned_at') or None,
                        'transitioned_by': (fields.get('transitioned_by', [None])[0] or None)
                    })

        # Build list of documents to check
        doc_numbers = list(backup_wf.keys() | backup_tr.keys())
        if limit and len(doc_numbers) > limit:
            doc_numbers = doc_numbers[:limit]

        checked = 0
        missing_in_db = []
        mismatch_counts = []
        mismatch_sequences = []
        ok = 0

        for num in doc_numbers:
            checked += 1
            try:
                doc = Document.objects.get(document_number=num)
            except Document.DoesNotExist:
                missing_in_db.append(num)
                continue
            db_wf = DocumentWorkflow.objects.filter(document=doc).first()
            db_tr_qs = DocumentTransition.objects.filter(workflow=db_wf).order_by('transitioned_at', 'id') if db_wf else []
            db_tr = [
                {
                    'from_state': t.from_state.code if t.from_state else None,
                    'to_state': t.to_state.code if t.to_state else None,
                    'transitioned_at': t.transitioned_at.isoformat() if t.transitioned_at else None,
                    'transitioned_by': t.transitioned_by.username if t.transitioned_by else None,
                }
                for t in db_tr_qs
            ]

            b_tr = sorted(backup_tr.get(num, []), key=lambda x: (x.get('transitioned_at') or '', x.get('to_state') or ''))
            # Compare counts
            if len(db_tr) != len(b_tr):
                mismatch_counts.append({'document_number': num, 'backup': len(b_tr), 'db': len(db_tr)})
                if verbose:
                    self.stdout.write(self.style.WARNING(f"Count mismatch for {num}: backup={len(b_tr)} db={len(db_tr)}"))
                    self.stdout.write(f"  backup={b_tr}")
                    self.stdout.write(f"  db={db_tr}")
                continue
            # Compare sequences (from_state,to_state,transitioned_by; timestamps may vary in precision/timezone)
            seq_equal = True
            for i in range(len(b_tr)):
                b = b_tr[i]
                d = db_tr[i]
                if (b.get('from_state') != d.get('from_state') or
                    b.get('to_state') != d.get('to_state') or
                    (b.get('transitioned_by') or None) != (d.get('transitioned_by') or None)):
                    seq_equal = False
                    break
            if not seq_equal:
                mismatch_sequences.append({'document_number': num, 'backup': b_tr, 'db': db_tr})
                if verbose:
                    self.stdout.write(self.style.WARNING(f"Sequence mismatch for {num}"))
                    self.stdout.write(f"  backup={b_tr}")
                    self.stdout.write(f"  db={db_tr}")
            else:
                ok += 1

        summary = {
            'checked_documents': checked,
            'ok': ok,
            'missing_in_db': missing_in_db,
            'mismatch_counts': mismatch_counts,
            'mismatch_sequences': mismatch_sequences,
        }
        self.stdout.write(json.dumps(summary, indent=2))
        return 0
