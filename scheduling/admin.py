from django.contrib import admin
from .models import Department, Schedule

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['display_name']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('관리자', {
            'fields': ('manager',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
@admin.register(Schedule) 
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_datetime', 'end_datetime', 'department', 'assignee', 'creator', 'status', 'priority']
    list_filter = ['status', 'priority', 'department', 'start_datetime']
    search_fields = ['title', 'description', 'assignee__username', 'creator__username']
    date_hierarchy = 'start_datetime'
    ordering = ['-start_datetime']
