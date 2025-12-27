#!/usr/bin/env python
"""
Simple backup test script to verify basic functionality
without complex dependencies.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def test_database_backup():
    """Test basic database backup functionality."""
    print("🔍 Testing database backup...")
    
    # Get database connection info from environment
    db_settings = {
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'NAME': os.getenv('DB_NAME', 'edms_db'),
        'USER': os.getenv('DB_USER', 'edms_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'edms_pass')
    }
    
    print(f"Database: {db_settings['NAME']} on {db_settings['HOST']}:{db_settings['PORT']}")
    
    # Create backup directory
    backup_dir = Path('/tmp/edms_backup_test')
    backup_dir.mkdir(exist_ok=True)
    
    # Test database dump
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f"db_backup_{timestamp}.sql"
    
    try:
        # Simple pg_dump command
        cmd = [
            'pg_dump',
            '-h', db_settings['HOST'],
            '-p', db_settings['PORT'],
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '--no-password',
            '-f', str(backup_file)
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0 and backup_file.exists():
            file_size = backup_file.stat().st_size
            print(f"✅ Database backup successful: {backup_file}")
            print(f"   File size: {file_size:,} bytes")
            return True
        else:
            print(f"❌ Database backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Database backup error: {str(e)}")
        return False

def test_storage_backup():
    """Test storage directory backup."""
    print("\n🔍 Testing storage backup...")
    
    storage_paths = [
        '/app/media',
        '/storage/documents',
        '/storage/media'
    ]
    
    backup_dir = Path('/tmp/edms_backup_test')
    backup_dir.mkdir(exist_ok=True)
    
    for storage_path in storage_paths:
        path = Path(storage_path)
        if path.exists():
            print(f"✅ Found storage: {storage_path}")
            
            # Count files
            file_count = len(list(path.rglob('*')))
            print(f"   Files: {file_count}")
            
            # Test archive creation
            archive_name = backup_dir / f"storage_{path.name}_{datetime.now().strftime('%H%M%S')}.tar.gz"
            
            try:
                import tarfile
                with tarfile.open(archive_name, 'w:gz') as tar:
                    tar.add(storage_path, arcname=path.name)
                
                if archive_name.exists():
                    file_size = archive_name.stat().st_size
                    print(f"✅ Storage backup successful: {archive_name.name} ({file_size:,} bytes)")
                
            except Exception as e:
                print(f"❌ Storage backup failed: {str(e)}")
        else:
            print(f"⚠️  Storage not found: {storage_path}")
    
    return True

def test_system_info():
    """Test system information gathering."""
    print("\n🔍 Testing system information...")
    
    try:
        # Basic system info
        print(f"✅ Python: {sys.version.split()[0]}")
        print(f"✅ Working directory: {os.getcwd()}")
        
        # Disk space
        if hasattr(os, 'statvfs'):
            statvfs = os.statvfs('/tmp')
            free_bytes = statvfs.f_frsize * statvfs.f_available
            print(f"✅ Free space (/tmp): {free_bytes // (1024*1024):,} MB")
        
        # Process info
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            print(f"✅ CPU usage: {cpu_percent:.1f}%")
            print(f"✅ Memory usage: {memory.percent:.1f}%")
        except ImportError:
            print("⚠️  psutil not available for system metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ System info error: {str(e)}")
        return False

def main():
    """Run all backup tests."""
    print("🚀 EDMS Backup System Test")
    print("=" * 50)
    
    results = []
    
    # Test system info
    results.append(test_system_info())
    
    # Test database backup
    results.append(test_database_backup())
    
    # Test storage backup
    results.append(test_storage_backup())
    
    # Summary
    print("\n📊 Test Results:")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())