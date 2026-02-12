"""
Patch file to add sensitivity label fields to Document model.
Add these fields to the Document model in models.py after line 236 (after document_source).
"""

# ADD TO Document MODEL (after line 236 - document_source field):

# Sensitivity Label System (5-tier classification)
from .sensitivity_labels import SENSITIVITY_CHOICES

sensitivity_label = models.CharField(
    max_length=20,
    choices=SENSITIVITY_CHOICES,
    default='INTERNAL',
    db_index=True,
    help_text='Sensitivity classification (set by approver)'
)

sensitivity_set_by = models.ForeignKey(
    User,
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name='sensitivity_labeled_documents',
    help_text='User who set the sensitivity label (typically approver)'
)

sensitivity_set_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text='When sensitivity label was set'
)

sensitivity_inherited_from = models.ForeignKey(
    'self',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='sensitivity_inherited_by',
    help_text='Parent document this sensitivity was inherited from'
)

sensitivity_change_reason = models.TextField(
    blank=True,
    help_text='Reason for sensitivity label change (required if changed from parent)'
)


# ADD THESE METHODS TO Document MODEL:

def get_sensitivity_display_data(self):
    """Get rich display data for sensitivity label."""
    from .sensitivity_labels import SENSITIVITY_METADATA
    return SENSITIVITY_METADATA.get(self.sensitivity_label, {})

def can_user_access(self, user):
    """Check if user can access this document based on sensitivity."""
    from .access_control import can_user_view_document
    result = can_user_view_document(user, self)
    return result['allowed']

def can_user_download(self, user):
    """Check if user can download this document based on sensitivity."""
    from .access_control import can_user_download_document
    result = can_user_download_document(user, self)
    return result['allowed']

def validate_sensitivity_change(self, new_label, user, reason=''):
    """Validate if sensitivity can be changed to new label."""
    from .access_control import SensitivityAccessControl
    return SensitivityAccessControl.validate_sensitivity_change(
        self.sensitivity_label,
        new_label,
        user,
        reason
    )


# ADD TO Document.Meta.indexes (around line 370):
models.Index(fields=['sensitivity_label'], name='documents_sens_label_idx'),
models.Index(fields=['sensitivity_label', 'status'], name='documents_sens_status_idx'),
