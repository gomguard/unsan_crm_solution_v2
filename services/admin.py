from django.contrib import admin
from .models import ServiceType, ServiceRequest, ServiceHistory, ServiceQuickButton

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'department', 'estimated_duration', 'base_price', 'is_active', 'created_at')
    list_filter = ('category', 'department', 'is_active', 'created_at')
    search_fields = ('name', 'category', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('category', 'name')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'category', 'description', 'is_active')
        }),
        ('서비스 세부사항', {
            'fields': ('estimated_duration', 'base_price', 'department')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ServiceQuickButton)
class ServiceQuickButtonAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'button_text', 'display_order', 'is_active', 'created_at')
    list_filter = ('service_type', 'is_active', 'created_at')
    search_fields = ('button_text', 'service_content', 'service_type__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('service_type', 'display_order', 'button_text')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('service_type', 'button_text', 'display_order', 'is_active')
        }),
        ('서비스 내용', {
            'fields': ('service_content',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('get_customer_name', 'service_type', 'status', 'priority', 'scheduled_date', 'assigned_employee', 'created_at')
    list_filter = ('status', 'priority', 'service_type__category', 'created_at')
    search_fields = ('customer__name', 'customer__phone', 'vehicle__vehicle_number', 'temp_customer_name', 'temp_customer_phone', 'temp_vehicle_number')
    readonly_fields = ('created_at', 'updated_at', 'linked_schedule')
    ordering = ('-created_at',)
    
    def get_customer_name(self, obj):
        return obj.customer.name if obj.customer else obj.temp_customer_name
    get_customer_name.short_description = '고객명'
    get_customer_name.admin_order_field = 'customer__name'
    
    fieldsets = (
        ('고객/차량 연결', {
            'fields': ('customer', 'vehicle')
        }),
        ('새 고객 정보 (기존 고객이 없을 때)', {
            'fields': ('temp_customer_name', 'temp_customer_phone', 'temp_customer_city', 'temp_customer_district', 'temp_customer_dong'),
            'classes': ('collapse',)
        }),
        ('새 차량 정보 (기존 차량이 없을 때)', {
            'fields': ('temp_vehicle_number', 'temp_vehicle_model', 'temp_vehicle_year', 'temp_vehicle_mileage'),
            'classes': ('collapse',)
        }),
        ('검사 정보', {
            'fields': ('last_inspection_date', 'next_inspection_date', 'inspection_notes'),
            'classes': ('collapse',)
        }),
        ('서비스 정보', {
            'fields': ('service_type', 'service_detail', 'description', 'estimated_price', 'status', 'priority')
        }),
        ('일정 정보', {
            'fields': ('requested_date', 'scheduled_date', 'assigned_employee')
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at', 'updated_at', 'linked_schedule'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ServiceHistory)
class ServiceHistoryAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'actual_start_time', 'actual_end_time', 'actual_price', 'satisfaction_score', 'vehicle_mileage_at_service')
    list_filter = ('satisfaction_score', 'created_at')
    search_fields = ('service_request__customer__name', 'service_request__temp_customer_name', 'work_summary')
    readonly_fields = ('created_at', 'updated_at', 'customer', 'vehicle', 'service_duration_minutes')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('서비스 정보', {
            'fields': ('service_request', 'customer', 'vehicle')
        }),
        ('실제 수행 정보', {
            'fields': ('actual_start_time', 'actual_end_time', 'service_duration_minutes', 'actual_price')
        }),
        ('작업 내용', {
            'fields': ('work_summary', 'parts_used', 'notes')
        }),
        ('차량 정보', {
            'fields': ('vehicle_mileage_at_service', 'vehicle_condition_notes')
        }),
        ('고객 피드백', {
            'fields': ('satisfaction_score', 'customer_feedback')
        }),
        ('다음 서비스', {
            'fields': ('next_service_date', 'next_service_notes')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
