from django.contrib import admin
from .models import HappyCall, HappyCallTemplate

@admin.register(HappyCall)
class HappyCallAdmin(admin.ModelAdmin):
    list_display = [
        'customer_name', 'call_stage', 'service_date', 'overall_satisfaction',
        'first_call_caller', 'second_call_caller', 'created_at'
    ]
    list_filter = [
        'call_stage', 'status', 'overall_satisfaction', 'will_revisit', 'recommend_to_others',
        'first_call_success', 'second_call_success', 'created_at'
    ]
    search_fields = [
        'service_request__customer__name', 'service_request__customer__phone',
        'customer_feedback', 'first_call_notes', 'second_call_notes'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': (
                'service_request', 'call_stage', 'status', 
                'total_call_attempts', 'next_call_date'
            )
        }),
        ('1차콜 정보', {
            'fields': (
                'first_call_scheduled_date', 'first_call_date', 
                'first_call_caller', 'first_call_notes', 'first_call_success'
            )
        }),
        ('2차콜 정보', {
            'fields': (
                'second_call_scheduled_date', 'second_call_date',
                'second_call_caller', 'second_call_notes', 'second_call_success'
            )
        }),
        ('만족도 조사', {
            'fields': (
                'overall_satisfaction', 'service_quality', 
                'staff_kindness', 'price_satisfaction'
            )
        }),
        ('고객 의견', {
            'fields': (
                'customer_feedback', 'improvement_suggestions', 
                'additional_needs', 'will_revisit', 'recommend_to_others'
            )
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def customer_name(self, obj):
        return obj.service_request.customer.name
    customer_name.short_description = '고객명'
    
    def service_date(self, obj):
        return obj.service_request.preferred_date
    service_date.short_description = '서비스 일자'

@admin.register(HappyCallTemplate)
class HappyCallTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'script_content']
    readonly_fields = ['created_at', 'updated_at']