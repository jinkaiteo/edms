import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.documents.models import Document
from apps.workflows.models import DocumentWorkflow, DocumentTransition


class Command(BaseCommand):
    help = "Export workflow history for all documents to a JSON file using natural keys"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            dest="output",
            help="Path to write the JSON file (default: /app/storage/workflow_history_<timestamp>.json)",
        )
        parser.add_argument(
            "--indent",
            dest="indent",
            type=int,
            default=2,
            help="Pretty-print JSON with the given indentation (default: 2)",
        )

    def handle(self, *args, **options):
        ts = timezone.now().strftime("%Y%m%d_%H%M%S")
        output_path = options.get("output") or f"/app/storage/workflow_history_{ts}.json"
        indent = options.get("indent", 2)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        self.stdout.write(self.style.NOTICE("🔎 Collecting workflow history for all documents..."))

        records = []
        count_docs = 0
        count_wf = 0
        count_tr = 0

        # Iterate documents to guarantee stable ordering by document_number
        for doc in Document.objects.order_by("document_number").all():
            count_docs += 1
            # Export DocumentWorkflow (if present) using natural keys
            wf = DocumentWorkflow.objects.filter(document=doc).first()
            if wf:
                count_wf += 1
                records.append({
                    "model": "workflows.documentworkflow",
                    "pk": None,  # use natural keys only
                    "fields": {
                        "document": [doc.document_number],
                        "current_state": [wf.current_state.code] if getattr(wf, "current_state", None) else [None],
                        "workflow_type": [getattr(getattr(wf, "workflow_type", None), "code", None)],
                        "is_terminated": getattr(wf, "is_terminated", False),
                    }
                })

                # Export transitions ordered by transitioned_at then id for stability
                transitions = DocumentTransition.objects.filter(workflow=wf).order_by("transitioned_at", "id")
                for t in transitions:
                    count_tr += 1
                    records.append({
                        "model": "workflows.documenttransition",
                        "pk": None,  # use natural keys only
                        "fields": {
                            "workflow": [doc.document_number],
                            "from_state": [t.from_state.code] if getattr(t, "from_state", None) else [None],
                            "to_state": [t.to_state.code] if getattr(t, "to_state", None) else [None],
                            "transitioned_at": t.transitioned_at.isoformat() if getattr(t, "transitioned_at", None) else None,
                            "transitioned_by": [getattr(getattr(t, "transitioned_by", None), "username", None)],
                        }
                    })

        summary = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "document_count": count_docs,
            "workflows_found": count_wf,
            "transitions_exported": count_tr,
            "file": output_path,
        }

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=indent, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS("✅ Workflow history export completed."))
        self.stdout.write(self.style.SUCCESS(json.dumps(summary, indent=2)))
        self.stdout.write(self.style.NOTICE(f"➡️  Output: {output_path}"))
