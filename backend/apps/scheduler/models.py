from django.db import models

# Simplified scheduler models - keeping only essential scheduled task functionality
# NotificationQueue removed - using direct WorkflowTask querying instead

class ScheduledTask(models.Model):
    """Simple scheduled task model for future batch operations"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_time = models.DateTimeField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
        
    class Meta:
        ordering = ['-scheduled_time']
