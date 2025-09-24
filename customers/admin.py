from django.contrib import admin
from .models import (
    Customer, Tag, CustomerTag, Vehicle, CustomerVehicle,
    CustomerCommunication, MarketingCampaign,
    CustomerCampaignHistory, CustomerPointHistory
)


# Inline classes
class CustomerTagInline(admin.TabularInline):
    model = CustomerTag
    extra = 0
    readonly_fields = ('created_at',)


class CustomerVehicleInline(admin.TabularInline):
    model = CustomerVehicle
    extra = 0
    readonly_fields = ('created_at',)


class CustomerCommunicationInline(admin.TabularInline):
    model = CustomerCommunication
    extra = 0
    fields = ('communication_date', 'communication_type', 'method', 'title', 'result')
    readonly_fields = ('created_at',)
    ordering = ('-communication_date',)



class CustomerPointHistoryInline(admin.TabularInline):
    model = CustomerPointHistory
    extra = 0
    fields = ('transaction_date', 'point_type', 'points', 'balance_after', 'reason')
    readonly_fields = ('created_at',)
    ordering = ('-transaction_date',)


# Main admin classes
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'get_display_name', 'phone', 'customer_status', 'customer_type', 
        'membership_status', 'marketing_consent', 'created_at'
    ]
    list_filter = [
        'customer_status', 'customer_type', 'membership_status', 
        'marketing_consent', 'do_not_contact', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'phone', 'email', 'company_name']
    readonly_fields = ['created_at', 'updated_at', 'total_service_count', 'total_service_amount']
    inlines = [CustomerTagInline, CustomerVehicleInline, CustomerCommunicationInline, 
               CustomerPointHistoryInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('customer_status', 'customer_type', 'name', 'phone')
        }),
        ('연락처 정보', {
            'fields': ('email', 'preferred_contact_method')
        }),
        ('주소 정보', {
            'fields': ('address_main', 'address_detail')
        }),
        ('법인 정보', {
            'fields': ('business_number', 'company_name'),
            'classes': ['collapse']
        }),
        ('멤버십 정보', {
            'fields': ('membership_status', 'membership_join_date', 'membership_expire_date', 'membership_points')
        }),
        ('마케팅/소통 설정', {
            'fields': ('marketing_consent', 'marketing_consent_date', 'do_not_contact', 'do_not_contact_reason', 'do_not_contact_date')
        }),
        ('고객 분석', {
            'fields': ('acquisition_source', 'customer_grade', 'first_service_date', 'last_service_date', 'last_contact_date'),
            'classes': ['collapse']
        }),
        ('서비스 통계', {
            'fields': ('total_service_count', 'total_service_amount'),
            'classes': ['collapse']
        }),
        ('기타', {
            'fields': ('notes', 'is_active')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    def get_display_name(self, obj):
        return obj.get_display_name()
    get_display_name.short_description = '고객명'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(CustomerTag)
class CustomerTagAdmin(admin.ModelAdmin):
    list_display = ['customer', 'tag', 'created_by', 'created_at']
    list_filter = ['tag', 'created_at']
    search_fields = ['customer__name', 'customer__phone', 'tag__name']
    readonly_fields = ['created_at']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['vehicle_number', 'model', 'year', 'created_at']
    list_filter = ['year', 'created_at']
    search_fields = ['vehicle_number', 'model']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CustomerVehicleInline]


@admin.register(CustomerVehicle)
class CustomerVehicleAdmin(admin.ModelAdmin):
    list_display = ['customer', 'vehicle', 'start_date', 'end_date', 'is_current_owner']
    list_filter = ['start_date', 'end_date']
    search_fields = ['customer__name', 'customer__phone', 'vehicle__vehicle_number']
    readonly_fields = ['created_at']
    
    def is_current_owner(self, obj):
        return obj.is_current_owner
    is_current_owner.boolean = True
    is_current_owner.short_description = '현재소유'


@admin.register(CustomerCommunication)
class CustomerCommunicationAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'communication_date', 'communication_type', 
        'method', 'direction', 'title', 'result', 'created_by'
    ]
    list_filter = [
        'communication_type', 'method', 'direction', 'result', 
        'follow_up_needed', 'communication_date'
    ]
    search_fields = ['customer__name', 'customer__phone', 'title', 'content']
    readonly_fields = ['created_at']
    date_hierarchy = 'communication_date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('customer', 'communication_date', 'communication_type', 'method', 'direction')
        }),
        ('내용', {
            'fields': ('title', 'content', 'result')
        }),
        ('후속 조치', {
            'fields': ('follow_up_needed', 'follow_up_date')
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at'),
            'classes': ['collapse']
        }),
    )



@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign_type', 'start_date', 'end_date', 'status', 'created_by', 'created_at']
    list_filter = ['campaign_type', 'status', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('캠페인 정보', {
            'fields': ('name', 'description', 'campaign_type')
        }),
        ('기간 설정', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('타겟팅', {
            'fields': ('target_criteria',)
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at'),
            'classes': ['collapse']
        }),
    )


@admin.register(CustomerCampaignHistory)
class CustomerCampaignHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'campaign', 'sent_date', 'delivery_status',
        'response_type', 'roi_amount'
    ]
    list_filter = ['delivery_status', 'response_type', 'sent_date']
    search_fields = ['customer__name', 'customer__phone', 'campaign__name']
    readonly_fields = ['created_at'] if hasattr(CustomerCampaignHistory, 'created_at') else []
    date_hierarchy = 'sent_date'


@admin.register(CustomerPointHistory)
class CustomerPointHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'transaction_date', 'point_type', 'points', 
        'balance_after', 'reason', 'created_by'
    ]
    list_filter = ['point_type', 'transaction_date']
    search_fields = ['customer__name', 'customer__phone', 'reason']
    readonly_fields = ['created_at']
    date_hierarchy = 'transaction_date'
