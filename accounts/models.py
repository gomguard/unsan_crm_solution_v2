from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPES = [
        ('admin', '관리자'),
        ('employee', '직원'),
        ('customer', '고객'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='employee')
    phone = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey('scheduling.Department', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='부서')  # ForeignKey로 변경
    position = models.CharField(max_length=50, blank=True)    # 직원용
    hire_date = models.DateField(null=True, blank=True)       # 직원용
    is_active_employee = models.BooleanField(default=True)    # 퇴사 여부
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'
    
    @property
    def is_employee(self):
        return self.user_type == 'employee'
    
    @property
    def is_customer(self):
        return self.user_type == 'customer'
