from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Department(models.Model):
    """부서 모델"""
    name = models.CharField('부서 코드', max_length=50, unique=True, help_text='시스템에서 사용하는 부서 코드 (예: engine_oil, insurance)')
    display_name = models.CharField('표시명', max_length=50, help_text='사용자에게 표시될 부서명 (예: 엔진오일팀, 보험영업팀)')
    description = models.TextField('설명', blank=True, help_text='부서에 대한 상세 설명')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments', verbose_name='부서 관리자')
    is_active = models.BooleanField('활성화', default=True, help_text='부서 활성화 여부')
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '부서'
        verbose_name_plural = '부서'
        ordering = ['display_name']
        
    def __str__(self):
        return self.display_name

class Schedule(models.Model):
    """일정 모델"""
    STATUS_CHOICES = [
        ('pending', '대기'),
        ('confirmed', '확인됨'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '낮음'),
        ('normal', '보통'),
        ('high', '높음'),
        ('urgent', '긴급'),
    ]
    
    title = models.CharField('제목', max_length=200)
    description = models.TextField('설명', blank=True)
    start_datetime = models.DateTimeField('시작 일시')
    end_datetime = models.DateTimeField('종료 일시')
    location = models.CharField('장소', max_length=200, blank=True)
    
    # 담당자 정보
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules', verbose_name='생성자')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='담당 부서')
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_schedules', verbose_name='담당자')
    
    # 상태 관리
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField('우선순위', max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_confirmed_by_assignee = models.BooleanField('담당자 확인', default=False)
    confirmed_at = models.DateTimeField('확인 일시', null=True, blank=True)
    
    # 메타 정보
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_schedules', verbose_name='수정자')
    
    # iCal 관련
    ical_uid = models.CharField('iCal UID', max_length=255, blank=True, unique=True)
    
    class Meta:
        verbose_name = '일정'
        verbose_name_plural = '일정'
        ordering = ['start_datetime']
        
    def __str__(self):
        return f"{self.title} ({self.start_datetime.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        # iCal UID 자동 생성
        if not self.ical_uid:
            self.ical_uid = f"schedule-{timezone.now().timestamp()}-{self.pk or 0}@unsan-crm.local"
        super().save(*args, **kwargs)
    
    def can_be_edited_by(self, user):
        """사용자가 이 일정을 편집할 수 있는지 확인"""
        # 생성자, 담당자, 부서 관리자, 전체 관리자는 편집 가능
        return (
            user == self.creator or 
            user == self.assignee or 
            user == self.department.manager or 
            user.is_superuser
        )
    
    def can_be_deleted_by(self, user):
        """사용자가 이 일정을 삭제할 수 있는지 확인"""
        # 생성자, 부서 관리자, 전체 관리자만 삭제 가능
        return (
            user == self.creator or 
            user == self.department.manager or 
            user.is_superuser
        )
