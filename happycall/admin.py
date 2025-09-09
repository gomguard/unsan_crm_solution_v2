from django.contrib import admin
from .models import (
    HappyCall, HappyCallTemplate, HappyCallRevenue, 
    CallRejection, CallFailureRevenueLoss, CallbackSchedule,
    RevenueRecoveryLog, SMSLog
)

@admin.register(HappyCall)
class HappyCallAdmin(admin.ModelAdmin):
    list_display = [
        'customer_name', 'call_stage', 'service_date', 'overall_satisfaction',
        'assigned_caller', 'created_at', 'get_revenue_count'
    ]
    list_filter = [
        'call_stage', 'status', 'overall_satisfaction', 'will_revisit', 'recommend_to_others',
        'first_call_success', 'second_call_success', 'third_call_success', 'fourth_call_success',
        'additional_service_interest', 'no_call_request', 'created_at'
    ]
    search_fields = [
        'service_request__customer__name', 'service_request__customer__phone',
        'customer_feedback', 'first_call_notes', 'second_call_notes', 
        'third_call_notes', 'fourth_call_notes'
    ]
    readonly_fields = ['created_at', 'updated_at', 'total_revenue_generated', 'revenue_count']
    
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
        ('3차콜 정보', {
            'fields': (
                'third_call_scheduled_date', 'third_call_date',
                'third_call_caller', 'third_call_notes', 'third_call_success'
            ),
            'classes': ('collapse',)
        }),
        ('4차콜 정보', {
            'fields': (
                'fourth_call_scheduled_date', 'fourth_call_date',
                'fourth_call_caller', 'fourth_call_notes', 'fourth_call_success'
            ),
            'classes': ('collapse',)
        }),
        ('만족도 조사', {
            'fields': (
                'overall_satisfaction', 'service_quality', 
                'staff_kindness', 'price_satisfaction'
            )
        }),
        ('고객 의견 및 관심사항', {
            'fields': (
                'customer_feedback', 'improvement_suggestions', 
                'additional_needs', 'will_revisit', 'recommend_to_others',
                'additional_service_interest', 'interested_service_notes'
            )
        }),
        ('특수 옵션', {
            'fields': (
                'no_call_request', 'follow_up_needed', 'customer_rejected'
            )
        }),
        ('매출 정보', {
            'fields': (
                'total_revenue_generated', 'revenue_count'
            ),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        return obj.service_request.customer.name
    customer_name.short_description = '고객명'
    
    def service_date(self, obj):
        return obj.service_request.service_date
    service_date.short_description = '서비스 일자'
    
    def assigned_caller(self, obj):
        """현재 단계의 담당자 표시"""
        if obj.call_stage.startswith('1st') and obj.first_call_caller:
            return obj.first_call_caller.get_full_name() or obj.first_call_caller.username
        elif obj.call_stage.startswith('2nd') and obj.second_call_caller:
            return obj.second_call_caller.get_full_name() or obj.second_call_caller.username
        elif obj.call_stage.startswith('3rd') and obj.third_call_caller:
            return obj.third_call_caller.get_full_name() or obj.third_call_caller.username
        elif obj.call_stage.startswith('4th') and obj.fourth_call_caller:
            return obj.fourth_call_caller.get_full_name() or obj.fourth_call_caller.username
        return '미지정'
    assigned_caller.short_description = '담당자'
    
    def get_revenue_count(self, obj):
        return obj.happycallrevenue_set.count()
    get_revenue_count.short_description = '매출건수'

@admin.register(HappyCallTemplate)
class HappyCallTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'script_content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HappyCallRevenue)
class HappyCallRevenueAdmin(admin.ModelAdmin):
    list_display = [
        'happy_call_customer', 'call_stage', 'revenue_type', 
        'status', 'proposed_at'
    ]
    list_filter = [
        'call_stage', 'revenue_type', 'status', 'proposed_at'
    ]
    search_fields = [
        'happy_call__service_request__customer__name',
    ]
    readonly_fields = ['proposed_at', 'accepted_at', 'completed_at']
    
    def happy_call_customer(self, obj):
        return obj.happy_call.service_request.customer.name
    happy_call_customer.short_description = '고객명'


@admin.register(CallRejection)
class CallRejectionAdmin(admin.ModelAdmin):
    list_display = [
        'happy_call_customer', 'rejection_type', 'status', 
        'customer_reason', 'created_at'
    ]
    list_filter = ['rejection_type', 'status', 'created_at']
    search_fields = [
        'happy_call__service_request__customer__name',
        'customer_reason', 'manager_notes'
    ]
    readonly_fields = ['created_at', 'manager_reviewed_at', 'admin_approved_at']
    
    def happy_call_customer(self, obj):
        return obj.happy_call.service_request.customer.name
    happy_call_customer.short_description = '고객명'


@admin.register(CallFailureRevenueLoss)
class CallFailureRevenueLossAdmin(admin.ModelAdmin):
    list_display = [
        'happy_call_customer', 'failed_stage', 'failure_reason',
        'estimated_revenue_loss'
    ]
    list_filter = ['failed_stage', 'failure_reason']
    search_fields = [
        'happy_call__service_request__customer__name',
        'failure_reason'
    ]
    
    def happy_call_customer(self, obj):
        return obj.happy_call.service_request.customer.name
    happy_call_customer.short_description = '고객명'


@admin.register(CallbackSchedule)
class CallbackScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'happy_call_customer', 'scheduled_date', 'status', 
        'priority', 'attempted_at', 'completed_at'
    ]
    list_filter = ['status', 'priority', 'scheduled_date', 'created_at']
    search_fields = [
        'happy_call__service_request__customer__name',
        'result_notes', 'customer_notes'
    ]
    readonly_fields = ['created_at', 'attempted_at', 'completed_at']
    
    def happy_call_customer(self, obj):
        return obj.happy_call.service_request.customer.name
    happy_call_customer.short_description = '고객명'


@admin.register(RevenueRecoveryLog)
class RevenueRecoveryLogAdmin(admin.ModelAdmin):
    list_display = [
        'failure_record_customer', 'recovery_source', 'recovered_amount',
        'recovery_date'
    ]
    list_filter = ['recovery_source', 'recovery_date']
    search_fields = [
        'failure_record__happy_call__service_request__customer__name',
    ]
    readonly_fields = ['recovery_date']
    
    def failure_record_customer(self, obj):
        return obj.failure_record.happy_call.service_request.customer.name
    failure_record_customer.short_description = '고객명'


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = [
        'happy_call_customer', 'sms_type', 'sent_at', 
        'success', 'phone_number'
    ]
    list_filter = ['sms_type', 'success', 'sent_at']
    search_fields = [
        'happy_call__service_request__customer__name',
        'phone_number', 'message_content'
    ]
    readonly_fields = ['sent_at']
    
    def happy_call_customer(self, obj):
        return obj.happy_call.service_request.customer.name
    happy_call_customer.short_description = '고객명'