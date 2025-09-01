from django.contrib import admin
from .models import Department, Schedule

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'manager', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'display_name']
    
@admin.register(Schedule) 
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_datetime', 'end_datetime', 'department', 'assignee', 'creator', 'status', 'priority']
    list_filter = ['status', 'priority', 'department', 'start_datetime']
    search_fields = ['title', 'description', 'assignee__username', 'creator__username']
    date_hierarchy = 'start_datetime'
    ordering = ['-start_datetime']
