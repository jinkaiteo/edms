"""
Restore validation utilities for backup system
Critical functions to prevent silent data loss during restore
"""

import logging
import json
from typing import Dict, Any, List
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class RestoreValidator:
    """Validates restore operations to prevent data loss"""
    
    def __init__(self):
        self._user_model = None
    
    @property
    def User(self):
        """Lazy-load User model to avoid apps loading issues"""
        if self._user_model is None:
            self._user_model = get_user_model()
        return self._user_model
    
    def count_objects_in_backup(self, backup_data: List[Dict]) -> Dict[str, int]:
        """Count objects by model type in backup data"""
        if not isinstance(backup_data, list):
            return {}
        
        counts = {}
        for item in backup_data:
            if isinstance(item, dict) and 'model' in item:
                model = item['model']
                counts[model] = counts.get(model, 0) + 1
        
        return counts
    
    def count_database_objects(self) -> Dict[str, int]:
        """Count current objects in database"""
        counts = {}
        
        try:
            # Import models dynamically to avoid circular imports
            from apps.documents.models import Document
            from apps.workflows.models_simple import DocumentWorkflow
            from apps.placeholders.models import PlaceholderDefinition
            from apps.backup.models import BackupConfiguration
            
            # Count critical models
            counts['auth.user'] = self.User.objects.count()
            counts['users.user'] = self.User.objects.count()  # May be same as auth.user
            counts['documents.document'] = Document.objects.count()
            counts['workflows.documentworkflow'] = DocumentWorkflow.objects.count()
            counts['placeholders.placeholderdefinition'] = PlaceholderDefinition.objects.count()
            counts['backup.backupconfiguration'] = BackupConfiguration.objects.count()
            
        except Exception as e:
            logger.warning(f"Failed to count some objects: {e}")
        
        return counts
    
    def validate_restore_completeness(self, expected_counts: Dict[str, int], 
                                    before_counts: Dict[str, int], 
                                    after_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Validate that restore operation completed successfully
        
        This is the CRITICAL function that catches foreign key issues
        """
        validation_result = {
            'success': True,
            'errors': [],
            'warnings': [],
            'statistics': {
                'expected_total': sum(expected_counts.values()),
                'actual_restored': 0,
                'models_checked': len(expected_counts)
            }
        }
        
        critical_models = [
            'auth.user', 'users.user',
            'documents.document', 
            'workflows.documentworkflow',
            'placeholders.placeholderdefinition'
        ]
        
        for model, expected_count in expected_counts.items():
            before_count = before_counts.get(model, 0)
            after_count = after_counts.get(model, 0)
            actual_restored = after_count - before_count
            
            # Check if restore was complete
            if actual_restored != expected_count:
                error_msg = (
                    f"{model}: Expected {expected_count}, "
                    f"but only {actual_restored} objects were restored "
                    f"(before: {before_count}, after: {after_count})"
                )
                
                if model in critical_models:
                    validation_result['errors'].append(error_msg)
                    validation_result['success'] = False
                    logger.error(f"CRITICAL: {error_msg}")
                else:
                    validation_result['warnings'].append(error_msg)
                    logger.warning(f"WARNING: {error_msg}")
            else:
                validation_result['statistics']['actual_restored'] += actual_restored
                logger.info(f"✅ {model}: {actual_restored} objects restored successfully")
        
        # Special validation for critical models
        if validation_result['errors']:
            validation_result['critical_failure_detected'] = True
            validation_result['likely_cause'] = (
                "Foreign key reference failures. Objects were skipped during restore "
                "because they reference non-existent related objects (e.g., documents "
                "referencing users by database IDs that changed after system reinit)."
            )
            validation_result['recommendation'] = (
                "This indicates the backup contains database ID references instead of "
                "natural keys. Natural key implementation is needed to fix this issue."
            )
        
        return validation_result
    
    def detect_foreign_key_issues(self, backup_data: List[Dict]) -> Dict[str, Any]:
        """Detect potential foreign key issues in backup data"""
        issues = {
            'has_database_id_references': False,
            'has_natural_key_references': False,
            'foreign_key_fields_found': [],
            'recommendations': []
        }
        
        # Look for foreign key reference patterns
        foreign_key_patterns = ['author', 'reviewer', 'approver', 'created_by', 'user', 'document']
        
        for item in backup_data[:100]:  # Sample first 100 items
            if isinstance(item, dict) and 'fields' in item:
                fields = item['fields']
                for field_name, field_value in fields.items():
                    if any(pattern in field_name.lower() for pattern in foreign_key_patterns):
                        if isinstance(field_value, int):
                            issues['has_database_id_references'] = True
                        elif isinstance(field_value, str):
                            issues['has_natural_key_references'] = True
                        elif isinstance(field_value, list) and field_value:
                            if isinstance(field_value[0], str):
                                issues['has_natural_key_references'] = True
                            else:
                                issues['has_database_id_references'] = True
                        
                        issues['foreign_key_fields_found'].append({
                            'model': item.get('model'),
                            'field': field_name,
                            'value_type': type(field_value).__name__,
                            'value_sample': str(field_value)[:50]
                        })
        
        # Generate recommendations
        if issues['has_database_id_references'] and not issues['has_natural_key_references']:
            issues['recommendations'].append(
                "Backup contains database ID references which may cause restore failures "
                "after system reinit. Consider regenerating backup with natural keys enabled."
            )
        elif issues['has_natural_key_references']:
            issues['recommendations'].append(
                "Backup contains natural key references which should restore correctly "
                "even after system reinit."
            )
        
        return issues

# Global validator instance
restore_validator = RestoreValidator()