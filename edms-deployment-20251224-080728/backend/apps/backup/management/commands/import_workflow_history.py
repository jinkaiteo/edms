from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import json
import os
from datetime import datetime
from django.utils import timezone

class Command(BaseCommand):
    help = "Import workflow history (DocumentWorkflow and DocumentTransition) from a backup JSON into the current DB."

    def add_arguments(self, parser):
        parser.add_argument('--backup-json', type=str, required=True, help='Path to database_backup.json')
        parser.add_argument('--limit', type=int, default=0, help='Optional limit of documents to import (0 = all)')
        parser.add_argument('--verbose', action='store_true', help='Verbose per-item logging')

    def handle(self, *args, **options):
        backup_json = options['backup_json']
        limit = options['limit']
        verbose = options['verbose']

        if not os.path.exists(backup_json):
            raise CommandError(f"Backup JSON not found: {backup_json}")

        from apps.documents.models import Document
        from apps.workflows.models_simple import (
            DocumentWorkflow,
            DocumentTransition,
            DocumentState,
        )
        from apps.workflows.models import WorkflowType

        # Load backup
        with open(backup_json, 'r') as f:
            data = json.load(f)

        # Partition records
        wf_defs = [r for r in data if r.get('model') == 'workflows.workflowtype']
        state_defs = [r for r in data if r.get('model') == 'workflows.documentstate']
        wf_recs = [r for r in data if r.get('model') == 'workflows.documentworkflow']
        tr_recs = [r for r in data if r.get('model') == 'workflows.documenttransition']

        # Upsert metadata first
        try:
            with transaction.atomic():
                for rec in wf_defs:
                    flds = rec.get('fields', {})
                    code = flds.get('code')
                    if not code:
                        continue
                    obj, created = WorkflowType.objects.get_or_create(
                        code=code,
                        defaults={
                            'name': flds.get('name') or code,
                            'description': flds.get('description','')
                        }
                    )
                    if not created:
                        updated = False
                        if flds.get('name') and obj.name != flds.get('name'):
                            obj.name = flds.get('name'); updated = True
                        if obj.description != flds.get('description',''):
                            obj.description = flds.get('description',''); updated = True
                        if updated:
                            obj.save(update_fields=['name','description'])
                for rec in state_defs:
                    flds = rec.get('fields', {})
                    code = flds.get('code')
                    if not code:
                        continue
                    obj, created = DocumentState.objects.get_or_create(
                        code=code,
                        defaults={
                            'name': flds.get('name') or code,
                            'description': flds.get('description',''),
                            'order': flds.get('order') or 0
                        }
                    )
                    if not created:
                        updated = False
                        if flds.get('name') and obj.name != flds.get('name'):
                            obj.name = flds.get('name'); updated = True
                        if obj.description != flds.get('description',''):
                            obj.description = flds.get('description',''); updated = True
                        if flds.get('order') is not None and obj.order != flds.get('order'):
                            obj.order = flds.get('order'); updated = True
                        if updated:
                            obj.save(update_fields=['name','description','order'])
        except Exception as e:
            raise CommandError(f"Failed to upsert workflow metadata: {e}")

        # Build doc list to import
        doc_numbers = []
        doc_numbers.extend([(r.get('fields',{}).get('document') or [None])[0] for r in wf_recs])
        doc_numbers.extend([(r.get('fields',{}).get('workflow') or [None])[0] for r in tr_recs])
        doc_numbers = [d for d in doc_numbers if d]
        doc_numbers = list(dict.fromkeys(doc_numbers))  # preserve order, dedupe
        if limit and len(doc_numbers) > limit:
            doc_numbers = doc_numbers[:limit]

        created_wf = 0
        created_tr = 0
        skipped = 0
        for num in doc_numbers:
            # Create/attach workflow
            try:
                doc = Document.objects.get(document_number=num)
            except Document.DoesNotExist:
                skipped += 1
                if verbose:
                    self.stdout.write(self.style.WARNING(f"Skipping {num}: document not found"))
                continue

            # Find the workflow record for this doc in backup (optional metadata)
            wf_data = None
            for rec in wf_recs:
                flds = rec.get('fields', {})
                if (flds.get('document') or [None])[0] == num:
                    wf_data = flds
                    break

            wtype = None
            cstate = None
            if wf_data:
                wtype_code = (wf_data.get('workflow_type') or [None])[0]
                state_code = (wf_data.get('current_state') or [None])[0]
                if wtype_code:
                    # WorkflowType doesn't have 'code' field - use 'name' or 'workflow_type' field
                    wtype = WorkflowType.objects.filter(name=wtype_code).first() or \
                            WorkflowType.objects.filter(workflow_type=wtype_code).first()
                if state_code:
                    cstate = DocumentState.objects.filter(code=state_code).first()

            wf = DocumentWorkflow.objects.filter(document=doc).first()
            if not wf:
                wf = DocumentWorkflow.objects.create(
                    document=doc,
                    workflow_type=wtype,
                    current_state=cstate,
                    initiated_by=None,
                    current_assignee=None,
                    selected_reviewer=None,
                    selected_approver=None,
                    is_terminated=bool(wf_data.get('is_terminated')) if wf_data else False,
                    due_date=wf_data.get('due_date') if wf_data else None,
                    effective_date=wf_data.get('effective_date') if wf_data else None,
                    obsoleting_date=wf_data.get('obsoleting_date') if wf_data else None,
                    workflow_data=wf_data.get('workflow_data') if wf_data else {},
                    up_version_reason=wf_data.get('up_version_reason') if wf_data else '',
                    obsoleting_reason=wf_data.get('obsoleting_reason') if wf_data else '',
                    termination_reason=wf_data.get('termination_reason') if wf_data else ''
                )
                created_wf += 1
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"Created workflow for {num}"))

            # Import transitions for this doc
            trs = [r for r in tr_recs if (r.get('fields',{}).get('workflow') or [None])[0] == num]
            trs_sorted = sorted(trs, key=lambda r: (r.get('fields',{}).get('transitioned_at') or '', r.get('fields',{}).get('to_state') or ''))
            for rec in trs_sorted:
                f = rec.get('fields', {})
                from_code = (f.get('from_state') or [None])[0]
                to_code = (f.get('to_state') or [None])[0]
                # Ensure states exist
                from_state = DocumentState.objects.filter(code=from_code).first()
                if not from_state and from_code:
                    from_state = DocumentState.objects.create(code=from_code, name=from_code, order=0)
                to_state = DocumentState.objects.filter(code=to_code).first()
                if not to_state and to_code:
                    to_state = DocumentState.objects.create(code=to_code, name=to_code, order=0)

                by_name = (f.get('transitioned_by') or [None])[0]
                from django.contrib.auth import get_user_model
                User = get_user_model()
                by_user = User.objects.filter(username=by_name).first() if by_name else None

                # Parse timestamp
                transitioned_at_dt = None
                ts = f.get('transitioned_at') or None
                if ts:
                    try:
                        if isinstance(ts, str) and ts.endswith('Z'):
                            ts = ts.replace('Z', '+00:00')
                        transitioned_at_dt = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
                        if transitioned_at_dt and transitioned_at_dt.tzinfo is None:
                            transitioned_at_dt = timezone.make_aware(transitioned_at_dt, timezone=timezone.utc)
                    except Exception:
                        transitioned_at_dt = None

                # Duplicate suppression (timestamp optional)
                dup_qs = DocumentTransition.objects.filter(
                    workflow=wf,
                    from_state=from_state,
                    to_state=to_state,
                    transitioned_by=by_user,
                )
                if transitioned_at_dt is not None:
                    dup_qs = dup_qs.filter(transitioned_at=transitioned_at_dt)
                if dup_qs.exists():
                    if verbose:
                        self.stdout.write(self.style.WARNING(f"Duplicate suppressed: {num} {from_code}->{to_code} by={by_name} at={f.get('transitioned_at')}"))
                    continue

                DocumentTransition.objects.create(
                    workflow=wf,
                    from_state=from_state,
                    to_state=to_state,
                    transitioned_by=by_user,
                    transitioned_at=transitioned_at_dt,
                    comment=f.get('comment') or '',
                    transition_data=f.get('transition_data') or {},
                )
                created_tr += 1
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"Created transition: {num} {from_code}->{to_code} at {f.get('transitioned_at')}"))

            # Set current_state to last transition's to_state
            last_tr = DocumentTransition.objects.filter(workflow=wf).order_by('transitioned_at','id').last()
            if last_tr and last_tr.to_state and (not wf.current_state_id or wf.current_state_id != last_tr.to_state_id):
                wf.current_state = last_tr.to_state
                wf.save(update_fields=['current_state','updated_at'])
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"Updated current_state for {num} -> {last_tr.to_state.code}"))

        self.stdout.write(self.style.SUCCESS(f"Import complete: workflows created={created_wf}, transitions created={created_tr}, skipped={skipped}"))
        return 0
