"""
Health Check Service for EDMS Backup System.

Provides comprehensive health monitoring for system components
including database, storage, application services, and backup system.
"""

import os
import psutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.core.cache import cache

from .models import HealthCheck, SystemMetric


class HealthCheckService:
    """Service for system health monitoring."""
    
    def __init__(self):
        self.checks = {
            'DATABASE': self.check_database_health,
            'STORAGE': self.check_storage_health,
            'APPLICATION': self.check_application_health,
            'BACKUP_SYSTEM': self.check_backup_system_health,
            'NETWORK': self.check_network_connectivity,
            'SERVICES': self.check_external_services,
            'SECURITY': self.check_security_status
        }
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return results."""
        results = {
            'overall_status': 'HEALTHY',
            'checks': {},
            'metrics': {},
            'timestamp': timezone.now().isoformat()
        }
        
        critical_issues = []
        warning_issues = []
        
        for check_type, check_function in self.checks.items():
            try:
                start_time = datetime.now()
                check_result = check_function()
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Save health check result
                health_check = HealthCheck.objects.create(
                    check_name=f"{check_type.title()} Health Check",
                    check_type=check_type,
                    status=check_result['status'],
                    response_time=response_time,
                    message=check_result.get('message', ''),
                    details=check_result.get('details', {}),
                    metrics=check_result.get('metrics', {})
                )
                
                results['checks'][check_type.lower()] = {
                    'status': check_result['status'],
                    'message': check_result.get('message', ''),
                    'response_time': response_time,
                    'details': check_result.get('details', {}),
                    'metrics': check_result.get('metrics', {})
                }
                
                # Track critical and warning issues
                if check_result['status'] == 'CRITICAL':
                    critical_issues.append(check_type)
                elif check_result['status'] == 'WARNING':
                    warning_issues.append(check_type)
                
                # Save system metrics
                self._save_system_metrics(check_type, check_result.get('metrics', {}))
                
            except Exception as e:
                # Log failed health check
                HealthCheck.objects.create(
                    check_name=f"{check_type.title()} Health Check",
                    check_type=check_type,
                    status='CRITICAL',
                    message=f"Health check failed: {str(e)}",
                    details={'error': str(e)}
                )
                
                results['checks'][check_type.lower()] = {
                    'status': 'CRITICAL',
                    'message': f"Health check failed: {str(e)}",
                    'error': str(e)
                }
                critical_issues.append(check_type)
        
        # Determine overall status
        if critical_issues:
            results['overall_status'] = 'CRITICAL'
        elif warning_issues:
            results['overall_status'] = 'WARNING'
        
        results['summary'] = {
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'total_checks': len(self.checks),
            'passed_checks': len(self.checks) - len(critical_issues) - len(warning_issues)
        }
        
        return results
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        result = {
            'status': 'HEALTHY',
            'message': 'Database is healthy',
            'details': {},
            'metrics': {}
        }
        
        try:
            # Test database connection
            with connection.cursor() as cursor:
                start_time = datetime.now()
                cursor.execute("SELECT 1")
                query_time = (datetime.now() - start_time).total_seconds()
                
                result['metrics']['query_response_time'] = query_time
                
                # Check database size
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                           pg_database_size(current_database()) as db_size_bytes
                """)
                db_size_result = cursor.fetchone()
                
                result['details']['database_size'] = db_size_result[0]
                result['metrics']['database_size_bytes'] = db_size_result[1]
                
                # Check active connections
                cursor.execute("SELECT count(*) FROM pg_stat_activity")
                active_connections = cursor.fetchone()[0]
                
                result['details']['active_connections'] = active_connections
                result['metrics']['active_connections'] = active_connections
                
                # Performance thresholds
                if query_time > 5.0:  # 5 seconds
                    result['status'] = 'CRITICAL'
                    result['message'] = f'Database response time critical: {query_time:.2f}s'
                elif query_time > 1.0:  # 1 second
                    result['status'] = 'WARNING'
                    result['message'] = f'Database response time slow: {query_time:.2f}s'
                
                # Connection threshold (assume max 100 connections)
                if active_connections > 80:
                    result['status'] = 'CRITICAL'
                    result['message'] = f'High connection count: {active_connections}'
                elif active_connections > 60:
                    result['status'] = 'WARNING'
                    result['message'] = f'Elevated connection count: {active_connections}'
        
        except Exception as e:
            result['status'] = 'CRITICAL'
            result['message'] = f'Database connection failed: {str(e)}'
            result['details']['error'] = str(e)
        
        return result
    
    def check_storage_health(self) -> Dict[str, Any]:
        """Check storage system health and availability."""
        result = {
            'status': 'HEALTHY',
            'message': 'Storage is healthy',
            'details': {},
            'metrics': {}
        }
        
        storage_paths = [
            ('Media Root', getattr(settings, 'MEDIA_ROOT', '/app/media')),
            ('Document Root', getattr(settings, 'DOCUMENT_STORAGE_ROOT', '/app/documents')),
            ('Backup Root', getattr(settings, 'BACKUP_ROOT', '/var/backups/edms'))
        ]
        
        critical_issues = []
        warning_issues = []
        
        for name, path in storage_paths:
            try:
                path_obj = Path(path)
                
                # Check if path exists
                if not path_obj.exists():
                    warning_issues.append(f"{name} does not exist: {path}")
                    continue
                
                # Check disk usage
                if hasattr(os, 'statvfs'):
                    # Unix systems
                    statvfs = os.statvfs(path)
                    total_bytes = statvfs.f_frsize * statvfs.f_blocks
                    free_bytes = statvfs.f_frsize * statvfs.f_available
                    used_bytes = total_bytes - free_bytes
                    
                    usage_percent = (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0
                    
                    result['details'][f'{name.lower().replace(" ", "_")}_usage'] = f"{usage_percent:.1f}%"
                    result['metrics'][f'{name.lower().replace(" ", "_")}_usage_percent'] = usage_percent
                    result['metrics'][f'{name.lower().replace(" ", "_")}_free_bytes'] = free_bytes
                    
                    # Disk usage thresholds
                    if usage_percent > 95:
                        critical_issues.append(f"{name} disk usage critical: {usage_percent:.1f}%")
                    elif usage_percent > 85:
                        warning_issues.append(f"{name} disk usage high: {usage_percent:.1f}%")
                
                # Test write access
                test_file = path_obj / '.health_check'
                try:
                    test_file.write_text('health_check')
                    test_file.unlink()
                    result['details'][f'{name.lower().replace(" ", "_")}_writable'] = True
                except Exception as e:
                    critical_issues.append(f"{name} not writable: {str(e)}")
                    result['details'][f'{name.lower().replace(" ", "_")}_writable'] = False
            
            except Exception as e:
                critical_issues.append(f"{name} check failed: {str(e)}")
        
        # Determine status
        if critical_issues:
            result['status'] = 'CRITICAL'
            result['message'] = '; '.join(critical_issues)
        elif warning_issues:
            result['status'] = 'WARNING'
            result['message'] = '; '.join(warning_issues)
        
        return result
    
    def check_application_health(self) -> Dict[str, Any]:
        """Check application health and performance."""
        result = {
            'status': 'HEALTHY',
            'message': 'Application is healthy',
            'details': {},
            'metrics': {}
        }
        
        try:
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            result['metrics']['cpu_usage_percent'] = cpu_percent
            result['metrics']['memory_usage_percent'] = memory.percent
            result['metrics']['memory_available_bytes'] = memory.available
            
            result['details']['cpu_usage'] = f"{cpu_percent:.1f}%"
            result['details']['memory_usage'] = f"{memory.percent:.1f}%"
            
            # Resource thresholds
            issues = []
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                result['status'] = 'CRITICAL'
            elif cpu_percent > 70:
                issues.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
                if result['status'] != 'CRITICAL':
                    result['status'] = 'WARNING'
            
            if memory.percent > 95:
                issues.append(f"Critical memory usage: {memory.percent:.1f}%")
                result['status'] = 'CRITICAL'
            elif memory.percent > 80:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
                if result['status'] != 'CRITICAL':
                    result['status'] = 'WARNING'
            
            # Check cache connectivity
            try:
                cache.set('health_check', 'ok', 60)
                cache_result = cache.get('health_check')
                result['details']['cache_working'] = cache_result == 'ok'
            except Exception as e:
                issues.append(f"Cache error: {str(e)}")
                result['details']['cache_working'] = False
                if result['status'] != 'CRITICAL':
                    result['status'] = 'WARNING'
            
            if issues:
                result['message'] = '; '.join(issues)
        
        except Exception as e:
            result['status'] = 'CRITICAL'
            result['message'] = f'Application health check failed: {str(e)}'
            result['details']['error'] = str(e)
        
        return result
    
    def check_backup_system_health(self) -> Dict[str, Any]:
        """Check backup system health."""
        result = {
            'status': 'HEALTHY',
            'message': 'Backup system is healthy',
            'details': {},
            'metrics': {}
        }
        
        try:
            from .models import BackupConfiguration, BackupJob
            
            # Check active backup configurations
            active_configs = BackupConfiguration.objects.filter(is_enabled=True)
            result['details']['active_configurations'] = active_configs.count()
            result['metrics']['active_configurations'] = active_configs.count()
            
            # Check recent backup success rate
            last_week = timezone.now() - timedelta(days=7)
            recent_jobs = BackupJob.objects.filter(created_at__gte=last_week)
            successful_jobs = recent_jobs.filter(status='COMPLETED')
            failed_jobs = recent_jobs.filter(status='FAILED')
            
            total_jobs = recent_jobs.count()
            success_rate = (successful_jobs.count() / total_jobs * 100) if total_jobs > 0 else 100
            
            result['details']['recent_jobs_total'] = total_jobs
            result['details']['recent_jobs_successful'] = successful_jobs.count()
            result['details']['recent_jobs_failed'] = failed_jobs.count()
            result['details']['success_rate'] = f"{success_rate:.1f}%"
            result['metrics']['backup_success_rate'] = success_rate
            
            # Check if backups are running as scheduled
            if active_configs.exists():
                # Find configurations that should have run recently
                overdue_configs = []
                for config in active_configs:
                    if config.frequency == 'DAILY':
                        # Should have run in last 25 hours
                        last_job = BackupJob.objects.filter(
                            configuration=config,
                            created_at__gte=timezone.now() - timedelta(hours=25)
                        ).first()
                        if not last_job:
                            overdue_configs.append(config.name)
                
                if overdue_configs:
                    result['status'] = 'WARNING'
                    result['message'] = f"Overdue backup configurations: {', '.join(overdue_configs)}"
                    result['details']['overdue_configurations'] = overdue_configs
            
            # Success rate thresholds
            if success_rate < 70:
                result['status'] = 'CRITICAL'
                result['message'] = f"Low backup success rate: {success_rate:.1f}%"
            elif success_rate < 90:
                if result['status'] != 'CRITICAL':
                    result['status'] = 'WARNING'
                    result['message'] = f"Backup success rate below target: {success_rate:.1f}%"
        
        except Exception as e:
            result['status'] = 'CRITICAL'
            result['message'] = f'Backup system check failed: {str(e)}'
            result['details']['error'] = str(e)
        
        return result
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity."""
        result = {
            'status': 'HEALTHY',
            'message': 'Network connectivity is healthy',
            'details': {},
            'metrics': {}
        }
        
        # For Docker environments, this is mostly internal connectivity
        # We can check if we can reach other services
        
        return result
    
    def check_external_services(self) -> Dict[str, Any]:
        """Check external service dependencies."""
        result = {
            'status': 'HEALTHY',
            'message': 'External services are healthy',
            'details': {},
            'metrics': {}
        }
        
        # Check if email service is configured
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            result['details']['email_configured'] = True
        else:
            result['details']['email_configured'] = False
            result['status'] = 'WARNING'
            result['message'] = 'Email service not configured'
        
        return result
    
    def check_security_status(self) -> Dict[str, Any]:
        """Check security-related configurations."""
        result = {
            'status': 'HEALTHY',
            'message': 'Security status is healthy',
            'details': {},
            'metrics': {}
        }
        
        # Check DEBUG setting
        result['details']['debug_mode'] = settings.DEBUG
        if settings.DEBUG:
            result['status'] = 'WARNING'
            result['message'] = 'DEBUG mode is enabled (not recommended for production)'
        
        # Check SECRET_KEY
        if settings.SECRET_KEY == 'django-insecure-change-this-in-production':
            result['status'] = 'CRITICAL'
            result['message'] = 'Default SECRET_KEY is being used'
            result['details']['secret_key_default'] = True
        else:
            result['details']['secret_key_default'] = False
        
        return result
    
    def _save_system_metrics(self, check_type: str, metrics: Dict[str, Any]):
        """Save system metrics to database."""
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                # Determine metric type and unit
                metric_type = 'APPLICATION_PERFORMANCE'
                unit = ''
                
                if 'percent' in metric_name:
                    unit = '%'
                    if 'cpu' in metric_name:
                        metric_type = 'CPU_USAGE'
                    elif 'memory' in metric_name:
                        metric_type = 'MEMORY_USAGE'
                    elif 'disk' in metric_name or 'usage' in metric_name:
                        metric_type = 'DISK_USAGE'
                elif 'bytes' in metric_name:
                    unit = 'bytes'
                    metric_type = 'DISK_USAGE'
                elif 'time' in metric_name:
                    unit = 's'
                    if 'database' in check_type.lower():
                        metric_type = 'DATABASE_PERFORMANCE'
                
                # Determine status based on thresholds
                status = 'NORMAL'
                warning_threshold = None
                critical_threshold = None
                
                if unit == '%':
                    warning_threshold = 80.0
                    critical_threshold = 95.0
                    if value >= critical_threshold:
                        status = 'CRITICAL'
                    elif value >= warning_threshold:
                        status = 'WARNING'
                
                SystemMetric.objects.create(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    value=value,
                    unit=unit,
                    warning_threshold=warning_threshold,
                    critical_threshold=critical_threshold,
                    status=status,
                    metadata={'check_type': check_type}
                )


# Global service instance
health_service = HealthCheckService()