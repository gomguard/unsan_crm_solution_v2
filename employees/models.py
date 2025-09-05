from django.db import models
from django.contrib.auth import get_user_model
from scheduling.models import Department

User = get_user_model()

class Employee(models.Model):
    """직원 추가 정보 모델"""
    POSITION_CHOICES = [
        ('staff', '직원'),
        ('manager', '팀장'),
        ('director', '부장'),
        ('ceo', '대표'),
    ]
    
    STATUS_CHOICES = [
        ('active', '재직'),
        ('inactive', '휴직'),
        ('retired', '퇴사'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', verbose_name='사용자')
    employee_id = models.CharField('사번', max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='부서')
    position = models.CharField('직급', max_length=20, choices=POSITION_CHOICES, default='staff')
    phone = models.CharField('연락처', max_length=20, blank=True)
    hire_date = models.DateField('입사일', null=True, blank=True)
    status = models.CharField('재직상태', max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField('메모', blank=True)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '직원'
        verbose_name_plural = '직원'
        
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.employee_id})"
