"""
Bulk operations optimization for natural key operations
P4.3: Optimize backup/restore for large datasets
"""

from django.db import transaction
from django.core.management.base import BaseCommand
from django.core.serializers import deserialize
import json
import logging

logger = logging.getLogger(__name__)

class BulkNaturalKeyRestorer:
    """Optimized bulk restore operations with natural key support"""
    
    def __init__(self):
        self.batch_size = 100
        self.processed_objects = 0
        self.failed_objects = 0
        self.model_cache = {}
    
    def restore_objects_in_batches(self, fixture_data, progress_callback=None):
        """
        Restore objects in optimized batches with natural key support
        """
        print(f"🚀 Starting bulk restore with batch size: {self.batch_size}")
        
        # Group objects by model for efficient processing
        objects_by_model = {}
        for obj_data in fixture_data:
            model_name = obj_data.get('model')
            if model_name not in objects_by_model:
                objects_by_model[model_name] = []
            objects_by_model[model_name].append(obj_data)
        
        print(f"📊 Grouped {len(fixture_data)} objects into {len(objects_by_model)} model types")
        
        # Process each model type in dependency order
        dependency_order = [
            'auth.user', 'users.user',  # Users first
            'documents.documenttype', 'documents.documentsource',  # Document types
            'workflows.documentstate',  # Workflow states
            'documents.document',  # Documents
            'workflows.documentworkflow',  # Workflows
            'placeholders.placeholderdefinition',  # Placeholders
            'backup.backupconfiguration'  # System config
        ]
        
        processed_models = set()
        
        # Process models in dependency order
        for model_name in dependency_order:
            if model_name in objects_by_model and model_name not in processed_models:
                self._process_model_batch(model_name, objects_by_model[model_name])
                processed_models.add(model_name)
                if progress_callback:
                    progress_callback(len(processed_models), len(objects_by_model))
        
        # Process remaining models
        for model_name, objects in objects_by_model.items():
            if model_name not in processed_models:
                self._process_model_batch(model_name, objects)
                processed_models.add(model_name)
                if progress_callback:
                    progress_callback(len(processed_models), len(objects_by_model))
        
        print(f"✅ Bulk restore complete: {self.processed_objects} objects processed, {self.failed_objects} failures")
        return {
            'processed': self.processed_objects,
            'failed': self.failed_objects,
            'success_rate': (self.processed_objects / (self.processed_objects + self.failed_objects)) * 100 if (self.processed_objects + self.failed_objects) > 0 else 0
        }
    
    def _process_model_batch(self, model_name, objects):
        """Process a batch of objects for a specific model"""
        print(f"📦 Processing {len(objects)} {model_name} objects...")
        
        batch_processed = 0
        batch_failed = 0
        
        # Process objects in smaller batches
        for i in range(0, len(objects), self.batch_size):
            batch = objects[i:i + self.batch_size]
            
            try:
                with transaction.atomic():
                    # Use Django's deserializer with natural key support
                    deserialized_objects = []
                    
                    for obj_data in batch:
                        try:
                            # Convert to Django deserializer format
                            django_format = [obj_data]
                            deserialized = list(deserialize('json', json.dumps(django_format), use_natural_foreign_keys=True, use_natural_primary_keys=True))
                            deserialized_objects.extend(deserialized)
                        except Exception as e:
                            logger.warning(f"Failed to deserialize {model_name} object: {e}")
                            batch_failed += 1
                    
                    # Save deserialized objects
                    for deserialized_obj in deserialized_objects:
                        try:
                            deserialized_obj.save()
                            batch_processed += 1
                        except Exception as e:
                            logger.warning(f"Failed to save {model_name} object: {e}")
                            batch_failed += 1
                            
            except Exception as e:
                logger.error(f"Batch processing failed for {model_name}: {e}")
                batch_failed += len(batch)
        
        print(f"   ✅ {model_name}: {batch_processed} processed, {batch_failed} failed")
        self.processed_objects += batch_processed
        self.failed_objects += batch_failed

class OptimizedBackupCreator:
    """Optimized backup creation with performance enhancements"""
    
    def __init__(self):
        self.batch_size = 1000
        
    def create_optimized_backup(self, output_file, include_models=None):
        """Create backup with optimized queries and natural key serialization"""
        from django.core.management import call_command
        import tempfile
        import os
        
        print("🚀 Creating optimized backup with natural keys...")
        
        # Use optimized dumpdata with natural keys and chunking
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            try:
                # Enhanced dumpdata command with optimization flags
                call_command(
                    'dumpdata',
                    '--format=json',
                    '--natural-foreign',  # Use natural foreign keys
                    '--natural-primary',  # Use natural primary keys  
                    '--indent=0',         # Compact format for efficiency
                    '--output', temp_file.name,
                    '--exclude=contenttypes',
                    '--exclude=auth.permission',
                    '--exclude=sessions',
                    verbosity=1
                )
                
                print(f"✅ Optimized backup created: {temp_file.name}")
                
                # Move to final location
                import shutil
                shutil.move(temp_file.name, output_file)
                
                # Get file stats
                file_size = os.path.getsize(output_file)
                print(f"📊 Backup size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                return {
                    'file_path': output_file,
                    'file_size': file_size,
                    'format': 'natural_keys_optimized'
                }
                
            except Exception as e:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                raise e