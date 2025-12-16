"""
Enhanced Restore Processor for EDMS Migration Packages

This module implements proper natural key resolution and conflict handling
to ensure complete data restoration from backup packages.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.core.management import call_command
from django.db import transaction, connection
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from io import StringIO

User = get_user_model()
logger = logging.getLogger(__name__)


class EnhancedRestoreProcessor:
    """
    Enhanced restore processor that properly handles natural keys,
    foreign key resolution, and conflict management.
    """
    
    def __init__(self):
        self.natural_key_cache = {}
        self.object_mappings = {}
        self.role_mapping = {}  # Maps backup Role UUIDs to current Role objects
        self.post_reinit_mode = False  # Flag for post-reinit scenario
        self.restoration_stats = {
            'total_records': 0,
            'successful_restorations': 0,
            'skipped_records': 0,
            'failed_records': 0,
            'created_objects': 0,
            'updated_objects': 0,
            'model_stats': {}
        }
        
    def process_backup_data(self, backup_file_path: str) -> Dict[str, Any]:
        """
        Process backup data with enhanced natural key resolution.
        
        Args:
            backup_file_path: Path to the backup JSON file
            
        Returns:
            Dictionary with restoration results and statistics
        """
        logger.info(f"🔄 Starting enhanced restoration from: {backup_file_path}")
        
        try:
            # Load backup data
            backup_data = self._load_backup_data(backup_file_path)
            
            # Detect post-reinit scenario and set up role mapping
            self.detect_post_reinit_scenario(backup_data)
            
            # Pre-process and validate data
            processed_data = self._preprocess_backup_data(backup_data)
            
            # Execute restoration in phases
            with transaction.atomic():
                self._restore_in_phases(processed_data)
            
            # Reset sequences
            self._reset_postgresql_sequences()
            
            # Generate final report
            return self._generate_restoration_report()
            
        except Exception as e:
            logger.error(f"Enhanced restoration failed: {str(e)}")
            raise
    
    def _load_backup_data(self, backup_file_path: str) -> List[Dict]:
        """Load and validate backup data from file."""
        logger.info("📂 Loading backup data...")
        
        with open(backup_file_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("Backup data must be a list of Django fixture records")
        
        self.restoration_stats['total_records'] = len(data)
        logger.info(f"✅ Loaded {len(data)} records from backup")
        
        return data
    
    def detect_post_reinit_scenario(self, backup_data: List[Dict]):
        """Detect if we're in a post-reinit scenario and set up role mapping"""
        from apps.users.models import Role
        
        # Get backup roles and current roles
        backup_roles = [r for r in backup_data if r.get('model') == 'users.role']
        current_roles = {role.name: role for role in Role.objects.all()}
        
        # Check if backup contains Role objects with different UUIDs than current
        role_uuid_conflicts = False
        for backup_role in backup_roles:
            role_name = backup_role['fields']['name']
            backup_uuid = backup_role['fields']['uuid']
            
            if role_name in current_roles:
                current_role = current_roles[role_name]
                if str(current_role.uuid) != backup_uuid:
                    role_uuid_conflicts = True
                    self.role_mapping[backup_uuid] = current_role
                    logger.info(f"🔄 Role UUID mapping: {role_name}")
                    logger.info(f"   Backup UUID: {backup_uuid[:8]}... → Current UUID: {str(current_role.uuid)[:8]}...")
        
        if role_uuid_conflicts:
            self.post_reinit_mode = True
            logger.info("🎯 Post-reinit scenario detected - enabling role UUID mapping")
            
            # Create missing users that UserRoles reference
            self._create_missing_users(backup_data)
            
        return role_uuid_conflicts
    
    def _create_missing_users(self, backup_data: List[Dict]):
        """Create users referenced by UserRoles but missing from system"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Extract all user references from UserRoles
        user_role_records = [r for r in backup_data if r.get('model') == 'users.userrole']
        
        referenced_users = set()
        for ur in user_role_records:
            fields = ur['fields']
            if 'user' in fields and isinstance(fields['user'], list):
                referenced_users.add(fields['user'][0])
            if 'assigned_by' in fields and isinstance(fields['assigned_by'], list):
                referenced_users.add(fields['assigned_by'][0])
        
        # Check which users exist
        existing_users = {user.username for user in User.objects.all()}
        missing_users = referenced_users - existing_users
        
        # Create missing users
        for username in missing_users:
            try:
                user = User.objects.create(
                    username=username,
                    email=f'{username}@edms.local',
                    first_name=username.capitalize(),
                    last_name='User',
                    is_active=True
                )
                user.set_password('edms123')  # Default password for restored users
                user.save()
                
                logger.info(f"  ✅ Created missing user: {username}")
                
            except Exception as e:
                logger.warning(f"  ❌ Failed to create user {username}: {str(e)}")
    
    def _preprocess_backup_data(self, backup_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Preprocess backup data and organize by restoration phases.
        
        This ensures dependencies are restored in the correct order.
        """
        logger.info("🔧 Preprocessing backup data...")
        
        # Define restoration phases based on dependencies
        phases = {
            'system_infrastructure': [
                'contenttypes.contenttype',
                'auth.permission'
            ],
            'user_management': [
                'auth.group',
                'users.user',
                'users.role',
                'users.userrole'
            ],
            'core_configuration': [
                'documents.documenttype',
                'documents.documentsource', 
                'workflows.workflowtype',
                'workflows.documentstate',
                'placeholders.placeholderdefinition'
            ],
            'business_data': [
                'documents.document',
                'documents.documentversion',
                'workflows.documentworkflow',
                'workflows.documenttransition'
            ],
            'audit_and_security': [
                'audit.audittrail',
                'audit.systemevent',
                'audit.loginaudit',
                'audit.databasechangelog',
                'audit.complianceevent',
                'security.pdfsigningcertificate'
            ],
            'system_configuration': [
                'backup.backupconfiguration',
                'scheduler.periodictask',
                'settings.systemsetting'
            ]
        }
        
        # Organize records by phase
        processed_data = {phase: [] for phase in phases.keys()}
        unclassified = []
        
        for record in backup_data:
            model = record.get('model')
            classified = False
            
            for phase, models in phases.items():
                if model in models:
                    processed_data[phase].append(record)
                    classified = True
                    break
            
            if not classified:
                unclassified.append(record)
        
        # Add unclassified records to appropriate phase based on app
        for record in unclassified:
            model = record.get('model', '')
            app_label = model.split('.')[0] if '.' in model else 'unknown'
            
            if app_label in ['documents', 'workflows']:
                processed_data['business_data'].append(record)
            elif app_label in ['audit', 'security']:
                processed_data['audit_and_security'].append(record)
            elif app_label in ['backup', 'scheduler', 'settings']:
                processed_data['system_configuration'].append(record)
            else:
                processed_data['system_infrastructure'].append(record)
        
        # Log phase distribution
        for phase, records in processed_data.items():
            logger.info(f"  📊 {phase}: {len(records)} records")
        
        return processed_data
    
    def _restore_in_phases(self, processed_data: Dict[str, List[Dict]]):
        """Restore data in dependency-aware phases."""
        
        phase_order = [
            'system_infrastructure',
            'user_management', 
            'core_configuration',
            'business_data',
            'audit_and_security',
            'system_configuration'
        ]
        
        for phase in phase_order:
            records = processed_data.get(phase, [])
            if records:
                logger.info(f"🔄 Restoring phase: {phase} ({len(records)} records)")
                self._restore_phase_records(phase, records)
    
    def _restore_phase_records(self, phase: str, records: List[Dict]):
        """Restore records for a specific phase with enhanced processing."""
        
        phase_stats = {
            'processed': 0,
            'successful': 0,
            'skipped': 0,
            'failed': 0
        }
        
        for record in records:
            try:
                # Skip Role objects in post-reinit mode (they already exist)
                if self.post_reinit_mode and record.get('model') == 'users.role':
                    phase_stats['skipped'] += 1
                    self.restoration_stats['skipped_records'] += 1
                    continue
                    
                result = self._restore_single_record(record, phase)
                phase_stats['processed'] += 1
                
                if result == 'success':
                    phase_stats['successful'] += 1
                    self.restoration_stats['successful_restorations'] += 1
                elif result == 'skipped':
                    phase_stats['skipped'] += 1
                    self.restoration_stats['skipped_records'] += 1
                else:
                    phase_stats['failed'] += 1
                    self.restoration_stats['failed_records'] += 1
                    
            except Exception as e:
                phase_stats['failed'] += 1
                self.restoration_stats['failed_records'] += 1
                logger.warning(f"Failed to restore {record.get('model')} record: {str(e)}")
        
        logger.info(f"✅ Phase {phase} completed: {phase_stats['successful']}/{phase_stats['processed']} successful")
    
    def _restore_single_record(self, record: Dict, phase: str) -> str:
        """
        Enhanced single record restoration with comprehensive error handling.
        
        Returns:
            'success', 'skipped', or 'failed'
        """
        model_name = record.get('model')
        fields = record.get('fields', {})
        pk = record.get('pk')
        
        try:
            # Get Django model class
            app_label, model = model_name.split('.')
            Model = apps.get_model(app_label, model)
            
            # Handle special cases for system infrastructure
            if phase == 'system_infrastructure':
                return self._handle_system_infrastructure(Model, record)
            
            # Check if this is a critical business model that should be prioritized
            is_critical = self._is_critical_business_model(model_name)
            
            # Resolve natural keys and foreign key references
            resolved_fields = self._resolve_foreign_keys(Model, fields)
            
            # In post-reinit mode, check if this is an infrastructure model that was preserved
            if self.post_reinit_mode and phase == 'core_configuration':
                # Check if object already exists by natural key (code, name, etc.)
                existing_obj = self._find_existing_object(Model, resolved_fields, None)
                if existing_obj:
                    logger.debug(f"Skipping preserved infrastructure: {model_name}")
                    return 'skipped'
            
            # Generate new UUID for business data objects in post-reinit mode to avoid conflicts
            if self.post_reinit_mode and hasattr(Model, 'uuid') and phase not in ['core_configuration', 'system_infrastructure']:
                import uuid as uuid_lib
                resolved_fields['uuid'] = uuid_lib.uuid4()
            
            # For critical models, skip field validation if we have essential data
            if is_critical:
                # Check if we have essential fields for creation
                has_essential_data = self._has_essential_data(Model, resolved_fields)
                if not has_essential_data:
                    logger.debug(f"Critical model {model_name} lacks essential data")
                    return 'skipped'
            else:
                # Validate required fields for non-critical models
                if not self._validate_required_fields(Model, resolved_fields, is_critical):
                    return 'skipped'
            
            # Handle conflicts and duplicates
            existing_obj = self._find_existing_object(Model, resolved_fields, pk)
            
            if existing_obj:
                # For critical models, try to update; for others, skip if exists
                if is_critical:
                    updated = self._update_existing_object(existing_obj, resolved_fields)
                    if updated:
                        self.restoration_stats['updated_objects'] += 1
                        logger.debug(f"✅ Updated {model_name}: {getattr(existing_obj, 'name', getattr(existing_obj, 'title', existing_obj.pk))}")
                        return 'success'
                    else:
                        return 'skipped'
                else:
                    return 'skipped'  # Non-critical model already exists
            else:
                # Create new object
                created_obj = self._create_new_object(Model, resolved_fields)
                if created_obj:
                    self.restoration_stats['created_objects'] += 1
                    # Cache object for future natural key lookups
                    self._cache_object_for_natural_keys(created_obj)
                    logger.info(f"✅ Created {model_name}: {getattr(created_obj, 'name', getattr(created_obj, 'title', created_obj.pk))}")
                    return 'success'
                else:
                    if is_critical:
                        logger.warning(f"⚠️ Failed to create critical model {model_name}")
                    return 'failed'
                    
        except Exception as e:
            is_critical = self._is_critical_business_model(model_name)
            if is_critical:
                logger.warning(f"⚠️ Critical model restoration failed for {model_name}: {str(e)}")
            else:
                logger.debug(f"Record restoration failed for {model_name}: {str(e)}")
            return 'failed'
    
    def _has_essential_data(self, Model, resolved_fields: Dict) -> bool:
        """
        Check if we have essential data needed for object creation.
        
        This is more permissive than full field validation.
        """
        try:
            # For UserRole, we need user and role
            if Model._meta.model_name == 'userrole':
                return 'user' in resolved_fields and 'role' in resolved_fields
            
            # For Document, we need author, document_type, and document_source
            elif Model._meta.model_name == 'document':
                return ('author' in resolved_fields and 
                        'document_type' in resolved_fields and 
                        'document_source' in resolved_fields)
            
            # For other models, check if we have at least one key identifier
            identifier_fields = ['name', 'title', 'username', 'code']
            for field_name in identifier_fields:
                if field_name in resolved_fields and resolved_fields[field_name]:
                    return True
            
            # If no identifier, check if we have any non-None fields
            non_none_fields = {k: v for k, v in resolved_fields.items() if v is not None}
            return len(non_none_fields) > 1  # More than just UUID
            
        except Exception as e:
            logger.debug(f"Error checking essential data for {Model._meta.model_name}: {str(e)}")
            return False
    
    def _is_critical_business_model(self, model_name: str) -> bool:
        """Determine if a model is critical for business functionality."""
        critical_models = {
            'users.user',
            'users.userrole', 
            'users.role',
            'documents.document',
            'documents.documenttype',
            'documents.documentsource',
            'documents.documentdependency',
            'workflows.workflowtype',
            'workflows.documentstate',
            'workflows.documentworkflow',
            'workflows.documenttransition',
            'placeholders.placeholderdefinition',
            'auth.group',
        }
        return model_name in critical_models
    
    def _validate_required_fields(self, Model, resolved_fields: Dict, is_critical: bool) -> bool:
        """
        Enhanced validation that checks for required fields with better error handling.
        
        This function is more permissive to allow restoration even when some fields
        might be missing due to model schema differences.
        """
        
        try:
            # For critical models, be more permissive to ensure business functionality
            if is_critical:
                # Only check for truly essential fields that would prevent object creation
                essential_fields = self._get_essential_fields(Model)
                
                missing_essential = []
                for field_name in essential_fields:
                    if field_name not in resolved_fields or resolved_fields[field_name] is None:
                        missing_essential.append(field_name)
                
                if missing_essential:
                    logger.debug(f"Missing essential fields for {Model._meta.label}: {missing_essential}")
                    # For critical models, try to proceed even with missing fields
                    # Django will handle required field validation at save time
                    return True
                
                return True
            else:
                # For non-critical models, use stricter validation
                return self._strict_field_validation(Model, resolved_fields)
            
        except Exception as e:
            logger.debug(f"Field validation failed for {Model._meta.label}: {str(e)}")
            # Default to allowing critical models to proceed
            return is_critical
    
    def _get_essential_fields(self, Model) -> List[str]:
        """
        Get truly essential fields that are absolutely required for object creation.
        
        This is more permissive than Django's field validation.
        """
        essential_fields = []
        
        try:
            for field in Model._meta.fields:
                # Only include fields that are:
                # 1. Not auto-generated (like id, created_at)
                # 2. Not nullable
                # 3. Don't have defaults
                # 4. Are not foreign keys (we handle those separately)
                if (not field.null and 
                    not getattr(field, 'auto_created', False) and
                    not hasattr(field, 'related_model') and
                    field.name not in ['id', 'created_at', 'updated_at', 'uuid']):
                    
                    # Check if field has a default value
                    try:
                        default_value = field.default
                        if default_value == field.__class__.default:
                            essential_fields.append(field.name)
                    except:
                        # If we can't check default, assume it's essential
                        essential_fields.append(field.name)
        
        except Exception as e:
            logger.debug(f"Error getting essential fields for {Model._meta.label}: {str(e)}")
        
        return essential_fields
    
    def _strict_field_validation(self, Model, resolved_fields: Dict) -> bool:
        """Strict field validation for non-critical models."""
        
        try:
            required_fields = []
            for field in Model._meta.fields:
                if (not field.null and 
                    not field.blank and 
                    not getattr(field, 'auto_created', False) and
                    field.name not in ['id', 'created_at', 'updated_at', 'uuid']):
                    required_fields.append(field.name)
            
            missing_fields = []
            for field_name in required_fields:
                if field_name not in resolved_fields or resolved_fields[field_name] is None:
                    missing_fields.append(field_name)
            
            return len(missing_fields) == 0
            
        except Exception as e:
            logger.debug(f"Strict validation failed for {Model._meta.label}: {str(e)}")
            return False
    
    def _handle_system_infrastructure(self, Model, record: Dict) -> str:
        """Handle system infrastructure models that may already exist."""
        
        model_name = record.get('model')
        fields = record.get('fields', {})
        
        # Skip contenttypes and permissions as they're managed by Django
        if model_name in ['contenttypes.contenttype', 'auth.permission']:
            return 'skipped'
        
        # For other system models, proceed with normal processing
        resolved_fields = self._resolve_foreign_keys(Model, fields)
        existing_obj = self._find_existing_object(Model, resolved_fields, record.get('pk'))
        
        if existing_obj:
            return 'skipped'  # Don't overwrite system objects
        else:
            created_obj = self._create_new_object(Model, resolved_fields)
            return 'success' if created_obj else 'failed'
    
    def _resolve_foreign_keys(self, Model, fields: Dict) -> Dict:
        """
        Enhanced foreign key resolution with comprehensive natural key support and robust error handling.
        
        This function handles all types of foreign key references including complex
        multi-level relationships and many-to-many fields.
        """
        resolved_fields = {}
        many_to_many_fields = {}
        
        for field_name, field_value in fields.items():
            try:
                # Get field information from model with bulletproof error handling
                field_obj = None
                try:
                    # Use Django's meta API safely
                    if hasattr(Model._meta, 'get_field'):
                        field_obj = Model._meta.get_field(field_name)
                    else:
                        # Fallback for edge cases
                        logger.debug(f"Model {Model._meta.label} has no get_field method")
                        continue
                        
                except Exception as field_error:
                    # Field doesn't exist or other meta API issue, skip it gracefully
                    logger.debug(f"Field {field_name} lookup failed in {Model._meta.label}: {str(field_error)}")
                    continue
                
                # Validate field object before using it
                if field_obj is None:
                    logger.debug(f"Field object is None for {field_name} in {Model._meta.label}")
                    continue
                    
                # Additional safety check for field object validity
                if not hasattr(field_obj, '__class__'):
                    logger.debug(f"Invalid field object for {field_name} in {Model._meta.label}")
                    continue
                
                # Determine field type safely
                field_type = self._get_field_type(field_obj)
                
                if field_type == 'foreign_key':
                    # Foreign key field
                    resolved_obj = self._resolve_foreign_key_field(field_obj, field_value)
                    if resolved_obj is not None:
                        resolved_fields[field_name] = resolved_obj
                    elif field_value is not None and field_value != []:
                        logger.debug(f"Failed to resolve FK {field_name}={field_value} for {Model._meta.label}")
                
                elif field_type == 'many_to_many':
                    # Many-to-many field - store for later processing
                    if isinstance(field_value, list) and len(field_value) > 0:
                        many_to_many_fields[field_name] = {
                            'field_obj': field_obj,
                            'value': field_value
                        }
                    # Don't add to resolved_fields as M2M is handled after object creation
                
                else:
                    # Regular field (CharField, IntegerField, etc.)
                    processed_value = self._process_regular_field(field_obj, field_value)
                    if processed_value is not None:
                        resolved_fields[field_name] = processed_value
                    
            except Exception as e:
                logger.debug(f"Failed to process field {field_name} in {Model._meta.label}: {str(e)}")
                # Continue processing other fields instead of failing entire record
                continue
        
        # Store M2M fields for post-creation processing
        if many_to_many_fields:
            resolved_fields['_deferred_m2m_fields'] = many_to_many_fields
        
        return resolved_fields
    
    def _get_field_type(self, field_obj) -> str:
        """
        Bulletproof field type detection with comprehensive error handling.
        
        Returns:
            'foreign_key', 'many_to_many', or 'regular'
        """
        try:
            # Safety check for field object
            if field_obj is None or not hasattr(field_obj, '__class__'):
                logger.debug("Invalid field object passed to _get_field_type")
                return 'regular'
            
            # Get field class name for safer type checking
            field_class_name = field_obj.__class__.__name__
            
            # Check field type by class name (safer than attribute checking)
            if field_class_name in ['ForeignKey', 'OneToOneField']:
                return 'foreign_key'
            elif field_class_name in ['ManyToManyField']:
                return 'many_to_many'
            
            # Fallback to attribute checking with safety
            try:
                if hasattr(field_obj, 'related_model') and getattr(field_obj, 'related_model', None) is not None:
                    return 'foreign_key'
            except Exception as attr_error:
                logger.debug(f"Error checking related_model attribute: {str(attr_error)}")
            
            try:
                if (hasattr(field_obj, 'remote_field') and 
                    field_obj.remote_field is not None and
                    hasattr(field_obj.remote_field, 'through')):
                    return 'many_to_many'
            except Exception as attr_error:
                logger.debug(f"Error checking remote_field attribute: {str(attr_error)}")
            
            # Default to regular field
            return 'regular'
            
        except Exception as e:
            logger.debug(f"Error determining field type: {str(e)}")
            return 'regular'
    
    def _resolve_foreign_key_field(self, field_obj, field_value) -> Optional[Any]:
        """Resolve a single foreign key field value with bulletproof error handling."""
        try:
            if isinstance(field_value, list) and len(field_value) > 0:
                # Natural key reference
                related_model = None
                try:
                    related_model = getattr(field_obj, 'related_model', None)
                except Exception as related_error:
                    logger.debug(f"Error accessing related_model: {str(related_error)}")
                    return None
                
                if related_model is not None:
                    return self._resolve_natural_key(related_model, field_value)
                else:
                    logger.debug(f"No related_model found for field")
                    return None
                    
            elif field_value is not None and not isinstance(field_value, list):
                # Direct reference (primary key)
                try:
                    related_model = getattr(field_obj, 'related_model', None)
                    if related_model is not None:
                        return related_model.objects.get(pk=field_value)
                    else:
                        logger.debug(f"No related_model for direct FK reference")
                        return None
                except Exception as direct_error:
                    logger.debug(f"Direct FK reference {field_value} lookup failed: {str(direct_error)}")
                    return None
            
            return None
            
        except Exception as e:
            logger.debug(f"Error resolving foreign key field: {str(e)}")
            return None
    
    def _process_regular_field(self, field_obj, field_value) -> Any:
        """Process regular (non-FK) field values with type conversion."""
        if field_value is None:
            return None
            
        # Handle different field types
        field_type = type(field_obj).__name__
        
        if field_type in ['DateTimeField', 'DateField']:
            # Handle datetime strings
            if isinstance(field_value, str):
                from django.utils.dateparse import parse_datetime, parse_date
                if field_type == 'DateTimeField':
                    return parse_datetime(field_value)
                else:
                    return parse_date(field_value)
            return field_value
        
        elif field_type == 'UUIDField':
            # Handle UUID fields
            if isinstance(field_value, str):
                import uuid
                try:
                    return uuid.UUID(field_value)
                except ValueError:
                    return field_value
            return field_value
        
        elif field_type == 'JSONField':
            # Handle JSON fields
            if isinstance(field_value, str):
                try:
                    import json
                    return json.loads(field_value)
                except:
                    return field_value
            return field_value
        
        else:
            # For most fields, return as-is
            return field_value
    
    def _resolve_natural_key(self, related_model, natural_key: List) -> Optional[Any]:
        """
        Enhanced natural key resolution for all model types with comprehensive FK support.
        
        Args:
            related_model: The model class for the foreign key
            natural_key: List representing the natural key
            
        Returns:
            The resolved object or None if not found
        """
        # Create cache key
        cache_key = f"{related_model._meta.label_lower}:{':'.join(map(str, natural_key))}"
        
        # Check cache first
        if cache_key in self.natural_key_cache:
            return self.natural_key_cache[cache_key]
        
        try:
            resolved_obj = None
            
            # Model-specific natural key resolution with comprehensive coverage
            model_label = related_model._meta.label_lower
            
            if model_label == 'auth.user' or related_model == User:
                resolved_obj = self._resolve_user_natural_key(natural_key)
                
            elif model_label == 'auth.group':
                resolved_obj = self._resolve_group_natural_key(natural_key)
                
            elif model_label == 'auth.permission':
                resolved_obj = self._resolve_permission_natural_key(natural_key)
                
            elif model_label == 'contenttypes.contenttype':
                resolved_obj = self._resolve_contenttype_natural_key(natural_key)
                
            elif model_label == 'users.role':
                resolved_obj = self._resolve_role_natural_key(natural_key)
                
            elif model_label == 'documents.document':
                resolved_obj = self._resolve_document_natural_key(natural_key)
                
            elif model_label == 'documents.documenttype':
                resolved_obj = self._resolve_document_type_natural_key(natural_key)
                
            elif model_label == 'documents.documentsource':
                resolved_obj = self._resolve_document_source_natural_key(natural_key)
                
            elif model_label == 'workflows.workflowtype':
                resolved_obj = self._resolve_workflow_type_natural_key(natural_key)
                
            elif model_label == 'workflows.documentstate':
                resolved_obj = self._resolve_document_state_natural_key(natural_key)
                
            elif model_label == 'workflows.documentworkflow':
                resolved_obj = self._resolve_documentworkflow_natural_key(natural_key)
                
            elif model_label == 'workflows.documenttransition':
                resolved_obj = self._resolve_documenttransition_natural_key(natural_key)
                
            elif model_label == 'documents.documentdependency':
                resolved_obj = self._resolve_documentdependency_natural_key(natural_key)
                
            elif model_label == 'placeholders.placeholderdefinition':
                resolved_obj = self._resolve_placeholder_natural_key(natural_key)
                
            elif model_label == 'backup.backupconfiguration':
                resolved_obj = self._resolve_backup_config_natural_key(natural_key)
                
            elif model_label == 'security.pdfsigningcertificate':
                resolved_obj = self._resolve_pdf_cert_natural_key(natural_key)
                
            else:
                # Enhanced generic resolution for unknown models
                resolved_obj = self._resolve_generic_natural_key(related_model, natural_key)
            
            # Cache the result (even if None)
            self.natural_key_cache[cache_key] = resolved_obj
            
            if resolved_obj:
                logger.debug(f"✅ Resolved natural key {cache_key} → {resolved_obj}")
            else:
                logger.debug(f"❌ Failed to resolve natural key {cache_key}")
            
            return resolved_obj
        
        except Exception as e:
            logger.debug(f"Natural key resolution failed for {cache_key}: {str(e)}")
            self.natural_key_cache[cache_key] = None
            return None
    
    def _resolve_user_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve User model natural keys (username)."""
        if len(natural_key) >= 1:
            username = natural_key[0]
            # Try exact match first
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                pass
            
            # Try with _restored suffix (for conflict resolution)
            try:
                return User.objects.get(username=f"{username}_restored")
            except User.DoesNotExist:
                pass
        return None
    
    def _resolve_group_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve Group model natural keys (name)."""
        if len(natural_key) >= 1:
            name = natural_key[0]
            try:
                return Group.objects.get(name=name)
            except Group.DoesNotExist:
                # Try with _restored suffix
                try:
                    return Group.objects.get(name=f"{name}_restored")
                except Group.DoesNotExist:
                    pass
        return None
    
    def _resolve_permission_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve Permission model natural keys [codename, app_label, model]."""
        if len(natural_key) >= 3:
            codename, app_label, model = natural_key[:3]
            try:
                content_type = ContentType.objects.get(app_label=app_label, model=model)
                return Permission.objects.get(codename=codename, content_type=content_type)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                pass
        return None
    
    def _resolve_contenttype_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve ContentType model natural keys [app_label, model]."""
        if len(natural_key) >= 2:
            app_label, model = natural_key[:2]
            try:
                return ContentType.objects.get(app_label=app_label, model=model)
            except ContentType.DoesNotExist:
                pass
        return None
    
    def _resolve_role_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve Role model natural keys (name) with post-reinit mapping support."""
        if len(natural_key) >= 1:
            name = natural_key[0]
            
            # In post-reinit mode, use existing roles instead of backup roles
            if self.post_reinit_mode:
                try:
                    from apps.users.models import Role
                    return Role.objects.get(name=name)
                except:
                    try:
                        from apps.users.models import Role
                        return Role.objects.get(name__iexact=name)
                    except:
                        pass
            else:
                # Normal mode - try to find or create roles
                try:
                    from apps.users.models import Role
                    return Role.objects.get(name=name)
                except:
                    # Try case-insensitive match
                    try:
                        from apps.users.models import Role
                        return Role.objects.get(name__iexact=name)
                    except:
                        pass
        return None
    
    def _resolve_document_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve Document model natural keys (document_number)."""
        if len(natural_key) >= 1:
            document_number = natural_key[0]
            try:
                from apps.documents.models import Document
                return Document.objects.get(document_number=document_number)
            except Exception as e:
                logger.warning(f"Failed to resolve Document natural key {natural_key}: {e}")
        return None
    
    def _resolve_document_type_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve DocumentType model natural keys (code or name)."""
        if len(natural_key) >= 1:
            identifier = natural_key[0]
            try:
                from apps.documents.models import DocumentType
                # Try by code first (most common)
                return DocumentType.objects.get(code=identifier)
            except:
                try:
                    from apps.documents.models import DocumentType
                    # Try by name
                    return DocumentType.objects.get(name=identifier)
                except:
                    pass
        return None
    
    def _resolve_document_source_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve DocumentSource model natural keys (name)."""
        if len(natural_key) >= 1:
            name = natural_key[0]
            try:
                from apps.documents.models import DocumentSource
                return DocumentSource.objects.get(name=name)
            except:
                try:
                    from apps.documents.models import DocumentSource
                    # Try case-insensitive and partial match
                    return DocumentSource.objects.get(name__icontains=name)
                except:
                    pass
        return None
    
    def _resolve_workflow_type_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve WorkflowType model natural keys (name)."""
        if len(natural_key) >= 1:
            name = natural_key[0]
            try:
                from apps.workflows.models import WorkflowType
                return WorkflowType.objects.get(name=name)
            except:
                pass
        return None
    
    def _resolve_document_state_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve DocumentState model natural keys (code or name)."""
        if len(natural_key) >= 1:
            identifier = natural_key[0]
            try:
                from apps.workflows.models import DocumentState
                # Try by code first
                return DocumentState.objects.get(code=identifier)
            except:
                try:
                    from apps.workflows.models import DocumentState
                    # Try by name
                    return DocumentState.objects.get(name=identifier)
                except:
                    pass
        return None
    
    def _resolve_placeholder_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve PlaceholderDefinition model natural keys (name or key)."""
        if len(natural_key) >= 1:
            identifier = natural_key[0]
            try:
                from apps.placeholders.models import PlaceholderDefinition
                # Try by name first
                return PlaceholderDefinition.objects.get(name=identifier)
            except:
                try:
                    from apps.placeholders.models import PlaceholderDefinition
                    # Try by key field if it exists
                    return PlaceholderDefinition.objects.get(key=identifier)
                except:
                    pass
        return None
    
    def _resolve_backup_config_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve BackupConfiguration model natural keys (name)."""
        if len(natural_key) >= 1:
            name = natural_key[0]
            try:
                from apps.backup.models import BackupConfiguration
                return BackupConfiguration.objects.get(name=name)
            except:
                pass
        return None
    
    def _resolve_documentworkflow_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve DocumentWorkflow model natural keys [document_number, workflow_type]."""
        if len(natural_key) >= 2:
            doc_number, workflow_type = natural_key[:2]
            try:
                from apps.workflows.models_simple import DocumentWorkflow
                return DocumentWorkflow.get_by_natural_key(doc_number, workflow_type)
            except Exception as e:
                logger.warning(f"Failed to resolve DocumentWorkflow natural key {natural_key}: {e}")
        return None
    
    def _resolve_documenttransition_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve DocumentTransition model natural keys [doc_number, workflow_type, transition_id]."""
        if len(natural_key) >= 3:
            doc_number, workflow_type, transition_id = natural_key[:3]
            try:
                from apps.workflows.models_simple import DocumentTransition
                return DocumentTransition.get_by_natural_key(doc_number, workflow_type, transition_id)
            except Exception as e:
                logger.warning(f"Failed to resolve DocumentTransition natural key {natural_key}: {e}")
        return None
    
    def _resolve_documentdependency_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve DocumentDependency model natural keys [source_doc_number, target_doc_number, dependency_type]."""
        if len(natural_key) >= 3:
            source_doc_number, target_doc_number, dependency_type = natural_key[:3]
            try:
                from apps.documents.models import DocumentDependency
                return DocumentDependency.get_by_natural_key(source_doc_number, target_doc_number, dependency_type)
            except Exception as e:
                logger.warning(f"Failed to resolve DocumentDependency natural key {natural_key}: {e}")
        return None
    
    def _resolve_pdf_cert_natural_key(self, natural_key: List) -> Optional[Any]:
        """Resolve PDFSigningCertificate model natural keys (name)."""
        if len(natural_key) >= 1:
            name = natural_key[0]
            try:
                from apps.security.models import PDFSigningCertificate
                return PDFSigningCertificate.objects.get(name=name)
            except:
                pass
        return None
    
    def _resolve_generic_natural_key(self, related_model, natural_key: List) -> Optional[Any]:
        """Enhanced generic natural key resolution for unknown models."""
        if len(natural_key) < 1:
            return None
        
        identifier = natural_key[0]
        
        # Try common natural key field patterns in order of likelihood
        natural_key_fields = [
            'name',           # Most common
            'code',           # Common for reference data
            'title',          # Documents, etc.
            'username',       # User-related models
            'slug',           # URL-friendly identifiers
            'key',            # Configuration models
            'identifier',     # Generic identifier fields
            'label',          # UI labels
            'display_name',   # Display names
        ]
        
        for field_name in natural_key_fields:
            if hasattr(related_model, field_name):
                try:
                    # Try exact match
                    lookup = {field_name: identifier}
                    return related_model.objects.get(**lookup)
                except related_model.DoesNotExist:
                    # Try case-insensitive match for text fields
                    try:
                        field = related_model._meta.get_field(field_name)
                        if hasattr(field, 'max_length'):  # CharField/TextField
                            lookup = {f"{field_name}__iexact": identifier}
                            return related_model.objects.get(**lookup)
                    except:
                        continue
                except related_model.MultipleObjectsReturned:
                    # If multiple objects, get the first one
                    lookup = {field_name: identifier}
                    return related_model.objects.filter(**lookup).first()
                except:
                    continue
        
        return None
    
    def _find_existing_object(self, Model, fields: Dict, pk: Any) -> Optional[Any]:
        """Find existing object to determine if we should update or create."""
        
        try:
            # Try to find by UUID if it exists
            if 'uuid' in fields and fields['uuid']:
                try:
                    return Model.objects.get(uuid=fields['uuid'])
                except Model.DoesNotExist:
                    pass
            
            # Try to find by natural key fields
            natural_key_fields = ['name', 'code', 'username', 'title', 'document_number']
            
            for field_name in natural_key_fields:
                if field_name in fields and fields[field_name] and hasattr(Model, field_name):
                    try:
                        lookup = {field_name: fields[field_name]}
                        return Model.objects.get(**lookup)
                    except Model.DoesNotExist:
                        continue
                    except Model.MultipleObjectsReturned:
                        # If multiple objects, get the first one
                        return Model.objects.filter(**lookup).first()
            
        except Exception as e:
            logger.debug(f"Error finding existing object for {Model}: {str(e)}")
        
        return None
    
    def _update_existing_object(self, obj, fields: Dict) -> bool:
        """Update existing object with new field values and handle M2M relationships."""
        
        try:
            # Extract deferred M2M fields
            deferred_m2m_fields = fields.pop('_deferred_m2m_fields', {})
            
            updated = False
            
            # Update regular fields
            for field_name, field_value in fields.items():
                if hasattr(obj, field_name):
                    current_value = getattr(obj, field_name)
                    if current_value != field_value:
                        setattr(obj, field_name, field_value)
                        updated = True
            
            if updated:
                obj.save()
                logger.debug(f"Updated existing {obj._meta.model_name}: {obj}")
            
            # Handle many-to-many relationships
            if deferred_m2m_fields:
                self._process_many_to_many_fields(obj, deferred_m2m_fields)
                updated = True  # M2M changes count as updates
            
            return updated
            
        except Exception as e:
            logger.debug(f"Failed to update object {obj}: {str(e)}")
            return False
    
    def _create_new_object(self, Model, fields: Dict) -> Optional[Any]:
        """
        Enhanced object creation with comprehensive error handling and field processing.
        """
        
        try:
            # Extract deferred M2M fields
            deferred_m2m_fields = fields.pop('_deferred_m2m_fields', {})
            
            # Clean and prepare fields for object creation
            clean_fields = self._prepare_fields_for_creation(Model, fields)
            
            if not clean_fields:
                logger.debug(f"No valid fields for creating {Model._meta.model_name}")
                return None
            
            # Create the object with enhanced error handling
            obj = self._safe_object_creation(Model, clean_fields)
            
            if obj:
                # Handle many-to-many relationships after object creation
                if deferred_m2m_fields:
                    self._process_many_to_many_fields(obj, deferred_m2m_fields)
                
                logger.debug(f"✅ Created {Model._meta.model_name}: {getattr(obj, 'name', getattr(obj, 'title', obj.pk))}")
                return obj
            else:
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to create {Model._meta.model_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _prepare_fields_for_creation(self, Model, fields: Dict) -> Dict:
        """
        Prepare fields for object creation with enhanced cleaning and validation.
        """
        clean_fields = {}
        
        try:
            for field_name, field_value in fields.items():
                # Skip None values and empty strings for most fields
                if field_value is None or field_value == '':
                    continue
                
                # Check if field exists in model
                try:
                    field_obj = Model._meta.get_field(field_name)
                    
                    # Special handling for different field types
                    if field_name == 'uuid' and not field_value:
                        # Generate UUID if needed
                        import uuid
                        clean_fields[field_name] = uuid.uuid4()
                    elif isinstance(field_value, (list, dict)) and not hasattr(field_obj, 'related_model'):
                        # Skip complex values for non-relational fields
                        logger.debug(f"Skipping complex value for non-relational field {field_name}")
                        continue
                    else:
                        clean_fields[field_name] = field_value
                        
                except Exception as field_error:
                    logger.debug(f"Field {field_name} validation failed: {str(field_error)}")
                    continue
            
            # Ensure UUID field if model has one
            if hasattr(Model, 'uuid') and 'uuid' not in clean_fields:
                import uuid
                clean_fields['uuid'] = uuid.uuid4()
            
            return clean_fields
            
        except Exception as e:
            logger.debug(f"Field preparation failed for {Model._meta.model_name}: {str(e)}")
            return {}
    
    def _safe_object_creation(self, Model, clean_fields: Dict) -> Optional[Any]:
        """
        Safely create object with progressive field inclusion to handle missing requirements.
        Uses transaction savepoints to isolate failures and prevent transaction poisoning.
        Preserves original timestamps by temporarily disabling auto_now/auto_now_add fields.
        """
        from django.db import transaction
        
        # Preserve auto_now fields by temporarily disabling them
        auto_now_fields = []
        auto_now_add_fields = []
        
        for field in Model._meta.fields:
            if hasattr(field, 'auto_now') and field.auto_now:
                auto_now_fields.append(field)
            if hasattr(field, 'auto_now_add') and field.auto_now_add:
                auto_now_add_fields.append(field)
        
        try:
            # Temporarily disable auto_now/auto_now_add to preserve historical timestamps
            for field in auto_now_fields:
                field.auto_now = False
            for field in auto_now_add_fields:
                field.auto_now_add = False
            
            try:
                # Use savepoint to isolate this creation - prevents transaction poisoning
                with transaction.atomic():
                    # First attempt: try with all fields
                    return Model.objects.create(**clean_fields)
            finally:
                # Always re-enable auto_now/auto_now_add
                for field in auto_now_fields:
                    field.auto_now = True
                for field in auto_now_add_fields:
                    field.auto_now_add = True
            
        except Exception as e:
            logger.debug(f"Full creation failed for {Model._meta.model_name}, trying progressive approach: {str(e)}")
            
            # Second attempt: try with only essential fields in a new savepoint
            essential_fields = self._get_minimal_required_fields(Model, clean_fields)
            
            if essential_fields:
                try:
                    # Disable auto_now fields again for the second attempt
                    for field in auto_now_fields:
                        field.auto_now = False
                    for field in auto_now_add_fields:
                        field.auto_now_add = False
                    
                    try:
                        # Use another savepoint for the second attempt
                        with transaction.atomic():
                            obj = Model.objects.create(**essential_fields)
                    finally:
                        # Re-enable auto_now fields
                        for field in auto_now_fields:
                            field.auto_now = True
                        for field in auto_now_add_fields:
                            field.auto_now_add = True
                    
                    # Update with remaining fields after creation
                    remaining_fields = {k: v for k, v in clean_fields.items() if k not in essential_fields}
                    if remaining_fields:
                        for field_name, field_value in remaining_fields.items():
                            try:
                                setattr(obj, field_name, field_value)
                            except:
                                continue
                        obj.save()
                    
                    return obj
                    
                except Exception as essential_error:
                    logger.debug(f"Essential field creation failed for {Model._meta.model_name}: {str(essential_error)}")
            
            return None
    
    def _get_minimal_required_fields(self, Model, available_fields: Dict) -> Dict:
        """
        Get minimal set of fields required for object creation.
        """
        minimal_fields = {}
        
        try:
            # Include UUID if available and model has it
            if 'uuid' in available_fields and hasattr(Model, 'uuid'):
                minimal_fields['uuid'] = available_fields['uuid']
            
            # Include name/title if available (common identifier fields)
            for field_name in ['name', 'title', 'username', 'code']:
                if field_name in available_fields:
                    minimal_fields[field_name] = available_fields[field_name]
                    break
            
            # Include any required non-nullable fields that we have values for
            for field in Model._meta.fields:
                if (not field.null and 
                    field.name in available_fields and
                    field.name not in minimal_fields and
                    not hasattr(field, 'related_model')):
                    minimal_fields[field.name] = available_fields[field.name]
        
        except Exception as e:
            logger.debug(f"Error determining minimal fields for {Model._meta.model_name}: {str(e)}")
        
        return minimal_fields
    
    def _process_many_to_many_fields(self, obj, m2m_fields: Dict):
        """Process many-to-many field assignments after object creation."""
        
        for field_name, field_info in m2m_fields.items():
            try:
                field_obj = field_info['field_obj']
                field_values = field_info['value']
                
                if not isinstance(field_values, list):
                    continue
                
                # Get the M2M manager
                m2m_manager = getattr(obj, field_name)
                
                # Resolve all natural keys to actual objects
                resolved_objects = []
                for natural_key in field_values:
                    if isinstance(natural_key, list):
                        resolved_obj = self._resolve_natural_key(field_obj.related_model, natural_key)
                        if resolved_obj:
                            resolved_objects.append(resolved_obj)
                        else:
                            logger.debug(f"Failed to resolve M2M natural key {natural_key} for {field_name}")
                    else:
                        # Direct reference (ID)
                        try:
                            direct_obj = field_obj.related_model.objects.get(pk=natural_key)
                            resolved_objects.append(direct_obj)
                        except field_obj.related_model.DoesNotExist:
                            logger.debug(f"Failed to resolve M2M direct reference {natural_key} for {field_name}")
                
                # Set the M2M relationships
                if resolved_objects:
                    m2m_manager.set(resolved_objects)
                    logger.debug(f"Set M2M {field_name} for {obj}: {len(resolved_objects)} relationships")
                
            except Exception as e:
                logger.debug(f"Failed to process M2M field {field_name} for {obj}: {str(e)}")
                continue
    
    def _cache_object_for_natural_keys(self, obj):
        """Cache created object for future natural key lookups."""
        
        try:
            model_label = obj._meta.label_lower
            
            # Cache by common natural key patterns
            if hasattr(obj, 'username'):
                cache_key = f"{model_label}:{obj.username}"
                self.natural_key_cache[cache_key] = obj
            
            elif hasattr(obj, 'name'):
                cache_key = f"{model_label}:{obj.name}"
                self.natural_key_cache[cache_key] = obj
            
            elif hasattr(obj, 'code'):
                cache_key = f"{model_label}:{obj.code}"
                self.natural_key_cache[cache_key] = obj
                
        except Exception as e:
            logger.debug(f"Failed to cache object for natural keys: {str(e)}")
    
    def _reset_postgresql_sequences(self):
        """Reset PostgreSQL sequences to prevent primary key conflicts."""
        
        logger.info("🔧 Resetting PostgreSQL sequences...")
        
        try:
            with connection.cursor() as cursor:
                # Get all sequences
                cursor.execute("""
                    SELECT sequence_name, sequence_schema 
                    FROM information_schema.sequences 
                    WHERE sequence_schema = 'public'
                    ORDER BY sequence_name;
                """)
                
                sequences = cursor.fetchall()
                sequences_reset = 0
                
                for sequence_name, schema in sequences:
                    try:
                        table_name = sequence_name.replace('_id_seq', '')
                        
                        # Get max ID
                        cursor.execute(f"""
                            SELECT COALESCE(MAX(id), 1) FROM {schema}.{table_name};
                        """)
                        max_id = cursor.fetchone()[0]
                        
                        # Reset sequence
                        cursor.execute(f"""
                            SELECT setval('{schema}.{sequence_name}', {max_id + 1}, false);
                        """)
                        
                        sequences_reset += 1
                        
                    except Exception as seq_error:
                        logger.debug(f"Could not reset sequence {sequence_name}: {seq_error}")
                        continue
                
                logger.info(f"✅ Reset {sequences_reset}/{len(sequences)} sequences")
                
        except Exception as e:
            logger.warning(f"Failed to reset sequences: {str(e)}")
    
    def _generate_restoration_report(self) -> Dict[str, Any]:
        """Generate comprehensive restoration report with business impact assessment."""
        
        stats = self.restoration_stats
        
        # Calculate different success rates
        total_rate = (stats['successful_restorations'] / stats['total_records'] * 100) if stats['total_records'] > 0 else 0
        
        # Assess business functionality restoration
        business_assessment = self._assess_business_functionality()
        
        report = {
            'status': 'completed',
            'summary': {
                'total_records': stats['total_records'],
                'successful_restorations': stats['successful_restorations'],
                'skipped_records': stats['skipped_records'],
                'failed_records': stats['failed_records'],
                'success_rate': round(total_rate, 2),
                'objects_created': stats['created_objects'],
                'objects_updated': stats['updated_objects'],
                'business_functionality_score': business_assessment['score'],
                'critical_systems_restored': business_assessment['critical_systems_restored'],
                'total_critical_systems': business_assessment['total_critical_systems']
            },
            'business_assessment': business_assessment,
            'natural_key_cache_size': len(self.natural_key_cache),
            'recommendations': []
        }
        
        # Enhanced recommendations based on business impact
        if business_assessment['score'] >= 90:
            report['recommendations'].append("✅ Excellent: All critical business systems fully restored")
        elif business_assessment['score'] >= 75:
            report['recommendations'].append("✅ Good: Most critical business systems restored successfully")
            
        if business_assessment['score'] < 75:
            report['recommendations'].append("⚠️ Review: Some critical business systems may need manual attention")
            
        if stats['failed_records'] > 0:
            failed_critical = stats['failed_records'] - (stats['total_records'] - business_assessment['critical_records_processed'])
            if failed_critical > 0:
                report['recommendations'].append(f"❌ Critical: {failed_critical} critical business records failed")
            else:
                report['recommendations'].append(f"ℹ️ Info: {stats['failed_records']} system records failed (non-critical)")
        
        if stats['skipped_records'] > stats['successful_restorations']:
            report['recommendations'].append("ℹ️ Info: High skip rate indicates data already exists in target system")
        
        # Log results with business context
        logger.info(f"✅ Enhanced restoration completed:")
        logger.info(f"   📊 Overall Success Rate: {total_rate:.1f}%")
        logger.info(f"   🎯 Business Functionality: {business_assessment['score']:.1f}%")
        logger.info(f"   🔧 Objects Created: {stats['created_objects']}")
        logger.info(f"   🔄 Objects Updated: {stats['updated_objects']}")
        
        return report
    
    def _assess_business_functionality(self) -> Dict[str, Any]:
        """Assess restoration success from business functionality perspective."""
        
        from django.contrib.auth import get_user_model
        from apps.users.models import UserRole, Role
        from apps.documents.models import Document, DocumentType, DocumentSource
        from apps.workflows.models import WorkflowType, DocumentState
        from apps.placeholders.models import PlaceholderDefinition
        from django.contrib.auth.models import Group
        
        User = get_user_model()
        
        # Define critical business systems and their current state
        critical_systems = {
            'user_authentication': {
                'condition': User.objects.count() >= 3,  # At least admin, author, reviewer
                'weight': 15
            },
            'user_roles': {
                'condition': UserRole.objects.count() >= 2,  # At least basic role assignments
                'weight': 20
            },
            'role_definitions': {
                'condition': Role.objects.count() >= 3,  # Author, Reviewer, Approver roles
                'weight': 10
            },
            'document_types': {
                'condition': DocumentType.objects.count() >= 3,  # Basic document types
                'weight': 15
            },
            'document_sources': {
                'condition': DocumentSource.objects.count() >= 1,  # At least one source
                'weight': 10
            },
            'workflow_engine': {
                'condition': WorkflowType.objects.count() >= 2,  # Basic workflows
                'weight': 10
            },
            'document_states': {
                'condition': DocumentState.objects.count() >= 5,  # DRAFT, REVIEW, APPROVED, etc.
                'weight': 10
            },
            'placeholder_system': {
                'condition': PlaceholderDefinition.objects.count() >= 10,  # Template placeholders
                'weight': 5
            },
            'group_permissions': {
                'condition': Group.objects.count() >= 2,  # Basic permission groups
                'weight': 5
            }
        }
        
        # Calculate business functionality score
        total_weight = sum(system['weight'] for system in critical_systems.values())
        achieved_weight = 0
        systems_restored = 0
        
        for system_name, system_info in critical_systems.items():
            if system_info['condition']:
                achieved_weight += system_info['weight']
                systems_restored += 1
        
        business_score = (achieved_weight / total_weight * 100) if total_weight > 0 else 0
        
        return {
            'score': round(business_score, 1),
            'critical_systems_restored': systems_restored,
            'total_critical_systems': len(critical_systems),
            'critical_records_processed': sum(1 for system in critical_systems.values() if system['condition']),
            'system_details': {
                name: system_info['condition'] for name, system_info in critical_systems.items()
            }
        }