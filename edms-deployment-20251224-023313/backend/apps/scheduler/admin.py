from django.contrib import admin
from .models import ScheduledTask

@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    """Admin interface for simple scheduled tasks"""
    list_display = ('name', 'scheduled_time', 'completed', 'created_at')
    list_filter = ('completed', 'scheduled_time')
    search_fields = ('name', 'description')
    ordering = ['-scheduled_time']
