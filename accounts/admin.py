from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    # 목록 페이지에서 표시할 필드
    list_display = ('username', 'last_name', 'first_name', 'email', 'department', 'position', 'user_type', 'is_active', 'is_staff', 'hire_date')
    list_filter = ('user_type', 'department', 'position', 'is_active', 'is_staff', 'is_superuser', 'hire_date')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'department', 'position')
    ordering = ('department', 'position', 'last_name', 'first_name')
    
    # 상세 페이지 필드 그룹화
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('개인정보', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('직원정보', {
            'fields': ('user_type', 'department', 'position', 'hire_date', 'is_active_employee')
        }),
        ('권한', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('중요한 날짜', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # 새 사용자 추가 시 필드
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone', 'user_type', 'department', 'position', 'hire_date'),
        }),
    )

# User 모델 등록
admin.site.register(User, UserAdmin)
