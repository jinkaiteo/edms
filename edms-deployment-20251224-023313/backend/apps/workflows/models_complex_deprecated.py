"""
DEPRECATED: Complex Workflow Models 

These models were part of the original River-based workflow system.
They are preserved here for reference but should not be used.

Use the simple workflow models in models_simple.py instead.
"""

# This file contains the deprecated complex workflow models
# They have been moved here to keep them out of the main models.py
# but preserve them for migration purposes

# Models moved:
# - WorkflowType
# - WorkflowInstance  
# - WorkflowTransition
# - WorkflowTask
# - WorkflowRule
# - WorkflowNotification
# - WorkflowTemplate

# These models tried to implement a River-based workflow system
# but River was never properly installed/configured.

# The Simple Approach (DocumentWorkflow, DocumentState, DocumentTransition)
# provides all the workflow functionality needed for EDMS compliance.