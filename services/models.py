from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from customers.models import Customer, Vehicle, CustomerVehicle

User = get_user_model()

class ServiceType(models.Model):
    """서비스 유형"""
    name = models.CharField('서비스명', max_length=100, help_text='서비스 이름 (예: 엔진오일 교환, 정기점검)')
    category = models.CharField('카테고리', max_length=50, help_text='서비스 카테고리 (예: 엔진오일교환, 정비점검, 자동차검사)')
    description = models.TextField('설명', blank=True, help_text='서비스에 대한 상세 설명')
    estimated_duration = models.PositiveIntegerField('예상 소요시간(분)', default=60, help_text='서비스 수행에 필요한 예상 시간')
    base_price = models.DecimalField('기본 가격', max_digits=10, decimal_places=0, default=0, help_text='기본 서비스 가격 (원)')
    department = models.ForeignKey('scheduling.Department', on_delete=models.CASCADE, verbose_name='담당 부서')
    is_active = models.BooleanField('활성화', default=True, help_text='서비스 유형 활성화 여부')
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '서비스 유형'
        verbose_name_plural = '서비스 유형'
        ordering = ['category', 'name']
        unique_together = ['name', 'category']
    
    def __str__(self):
        return f"{self.category} - {self.name}"
    
    def get_category_display(self):
        """카테고리 표시명 반환 (backward compatibility)"""
        return self.category

class ServiceQuickButton(models.Model):
    """서비스 빠른 입력 버튼"""
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, verbose_name='서비스 유형', related_name='quick_buttons')
    button_text = models.CharField('버튼 텍스트', max_length=100, help_text='버튼에 표시될 텍스트 (예: 5W-30 엔진오일, 부동액 교환)')
    service_content = models.TextField('서비스 내용', help_text='버튼 클릭 시 추가될 서비스 내용')
    display_order = models.PositiveIntegerField('표시 순서', default=0, help_text='버튼 표시 순서 (숫자가 작을수록 먼저 표시)')
    is_active = models.BooleanField('활성화', default=True, help_text='버튼 활성화 여부')
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '서비스 빠른 입력 버튼'
        verbose_name_plural = '서비스 빠른 입력 버튼'
        ordering = ['service_type', 'display_order', 'button_text']
        unique_together = ['service_type', 'button_text']
    
    def __str__(self):
        return f"{self.service_type.name} - {self.button_text}"

class ServiceRequest(models.Model):
    """서비스 요청"""
    STATUS_CHOICES = [
        ('pending', '접수대기'),
        ('scheduled', '일정확정'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '낮음'),
        ('normal', '보통'), 
        ('high', '높음'),
        ('urgent', '긴급'),
    ]
    
    # 고객 및 차량 정보 (FK 관계)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='고객', null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, verbose_name='차량', blank=True, null=True)
    
    # 임시 정보 (새 고객/차량 생성용)
    temp_customer_name = models.CharField('임시 고객명', max_length=100, blank=True)
    temp_customer_phone = models.CharField('임시 연락처', max_length=20, blank=True)
    temp_customer_city = models.CharField('임시 시/도', max_length=50, blank=True)
    temp_customer_district = models.CharField('임시 시/군/구', max_length=100, blank=True)
    temp_customer_dong = models.CharField('임시 행정동', max_length=100, blank=True)
    temp_vehicle_number = models.CharField('임시 차량번호', max_length=20, blank=True)
    temp_vehicle_model = models.CharField('임시 차량모델', max_length=100, blank=True)
    temp_vehicle_year = models.PositiveIntegerField('임시 연식', blank=True, null=True)
    temp_vehicle_mileage = models.PositiveIntegerField('임시 주행거리(km)', blank=True, null=True)
    
    # 자동차 검사 정보
    last_inspection_date = models.DateField('최근 검사일', blank=True, null=True, help_text='최근 정기검사 또는 종합검사일')
    next_inspection_date = models.DateField('다음 검사일', blank=True, null=True, help_text='다음 정기검사 또는 종합검사 예정일')
    inspection_notes = models.TextField('검사 관련 메모', blank=True, help_text='검사 관련 특이사항이나 메모')
    
    # 서비스 정보
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, verbose_name='서비스 유형')
    service_detail = models.TextField('세부설명', blank=True, help_text='서비스에 대한 세부 설명')
    description = models.TextField('요청 내용', blank=True)
    estimated_price = models.DecimalField('예상 가격', max_digits=10, decimal_places=0, blank=True, null=True, help_text='예상 서비스 가격 (원)')
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField('우선순위', max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # 일정 정보
    requested_date = models.DateTimeField('희망 일시', blank=True, null=True)
    scheduled_date = models.DateTimeField('확정 일시', blank=True, null=True)
    service_date = models.DateTimeField('서비스 실행일시', blank=True, null=True, help_text='실제 서비스가 수행된 날짜와 시간')
    assigned_employee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                        related_name='assigned_services', verbose_name='담당 직원')
    
    # 처리 정보
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_services', verbose_name='접수자')
    created_at = models.DateTimeField('접수일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    # 연동 정보
    linked_schedule = models.ForeignKey('scheduling.Schedule', on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name='연결된 일정')
    source_happycall = models.ForeignKey('happycall.HappyCall', on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name='연관 해피콜', help_text='해피콜에서 추가 서비스 요청으로 생성된 경우')
    
    class Meta:
        verbose_name = '서비스 요청'
        verbose_name_plural = '서비스 요청'
        ordering = ['-created_at']
    
    def __str__(self):
        customer_name = self.customer.name if self.customer else self.temp_customer_name
        return f"{customer_name} - {self.service_type} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # 임시 데이터로 고객/차량 자동 생성
        self._create_customer_vehicle_if_needed()
        
        # 서비스 요청이 저장될 때 일정관리에 자동 연동
        is_new = self.pk is None
        old_scheduled_date = None
        old_assigned_employee = None
        
        if not is_new:
            old_instance = ServiceRequest.objects.get(pk=self.pk)
            old_scheduled_date = old_instance.scheduled_date
            old_assigned_employee = old_instance.assigned_employee
        
        super().save(*args, **kwargs)
        
        # 일정 자동 생성/업데이트 로직
        self._sync_with_schedule(is_new, old_scheduled_date, old_assigned_employee)
    
    def _create_customer_vehicle_if_needed(self):
        """임시 데이터가 있으면 고객과 차량을 자동 생성"""
        # 고객이 없고 임시 고객 정보가 있으면 새 고객 생성
        if not self.customer and self.temp_customer_name and self.temp_customer_phone:
            customer, created = Customer.objects.get_or_create(
                phone=self.temp_customer_phone,
                defaults={
                    'name': self.temp_customer_name,
                    'city': self.temp_customer_city,
                    'district': self.temp_customer_district,
                    'dong': self.temp_customer_dong,
                    'status': 'temporary'  # 임시 고객으로 생성
                }
            )
            self.customer = customer
            
            # 임시 데이터 초기화
            self.temp_customer_name = ''
            self.temp_customer_phone = ''
            self.temp_customer_city = ''
            self.temp_customer_district = ''
            self.temp_customer_dong = ''
        
        # 차량이 없고 임시 차량 정보가 있으면 새 차량 생성 및 연결
        if not self.vehicle and self.temp_vehicle_number:
            vehicle, created = Vehicle.objects.get_or_create(
                vehicle_number=self.temp_vehicle_number,
                defaults={
                    'model': self.temp_vehicle_model or '',
                    'year': self.temp_vehicle_year
                }
            )
            self.vehicle = vehicle
            
            # 고객과 차량 연결
            if self.customer:
                from django.utils import timezone
                customer_vehicle, cv_created = CustomerVehicle.objects.get_or_create(
                    customer=self.customer,
                    vehicle=vehicle,
                    defaults={
                        'start_date': timezone.now().date()
                    }
                )
            
            # 임시 데이터 초기화
            self.temp_vehicle_number = ''
            self.temp_vehicle_model = ''
            self.temp_vehicle_year = None
            self.temp_vehicle_mileage = None
    
    def _sync_with_schedule(self, is_new, old_scheduled_date, old_assigned_employee):
        """일정관리 시스템과 동기화"""
        from scheduling.models import Schedule
        
        # 일정 확정 상태이고 담당자와 일시가 있을 때만 동기화
        if self.status in ['scheduled', 'in_progress', 'completed'] and self.scheduled_date and self.assigned_employee:
            
            if self.linked_schedule:
                # 기존 일정 업데이트
                schedule = self.linked_schedule
                customer_name = self.customer.name if self.customer else self.temp_customer_name
                customer_phone = self.customer.phone if self.customer else self.temp_customer_phone
                schedule.title = f"서비스: {self.service_type.name} - {customer_name}"
                schedule.description = f"고객: {customer_name}\n연락처: {customer_phone}\n요청사항: {self.description}"
                schedule.start_datetime = self.scheduled_date
                # 종료 시간 = 시작 시간 + 예상 소요 시간
                from datetime import timedelta
                schedule.end_datetime = self.scheduled_date + timedelta(minutes=self.service_type.estimated_duration)
                schedule.assignee = self.assigned_employee
                schedule.department = self.service_type.department
                schedule.priority = self.priority
                schedule.save()
            else:
                # 새 일정 생성
                from datetime import timedelta
                customer_name = self.customer.name if self.customer else self.temp_customer_name
                customer_phone = self.customer.phone if self.customer else self.temp_customer_phone
                schedule = Schedule.objects.create(
                    title=f"서비스: {self.service_type.name} - {customer_name}",
                    description=f"고객: {customer_name}\n연락처: {customer_phone}\n요청사항: {self.description}",
                    start_datetime=self.scheduled_date,
                    end_datetime=self.scheduled_date + timedelta(minutes=self.service_type.estimated_duration),
                    assignee=self.assigned_employee,
                    department=self.service_type.department,
                    creator=self.created_by,
                    priority=self.priority,
                    status='confirmed'
                )
                self.linked_schedule = schedule
                super().save(update_fields=['linked_schedule'])
        
        elif self.linked_schedule and self.status == 'cancelled':
            # 서비스가 취소되면 연결된 일정도 취소
            schedule = self.linked_schedule
            schedule.status = 'cancelled'
            schedule.save()

class ServiceHistory(models.Model):
    """서비스 이력"""
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, verbose_name='서비스 요청')
    
    # 실제 수행 정보
    actual_start_time = models.DateTimeField('실제 시작시간', blank=True, null=True)
    actual_end_time = models.DateTimeField('실제 종료시간', blank=True, null=True)
    actual_price = models.DecimalField('실제 가격', max_digits=10, decimal_places=0, blank=True, null=True)
    
    # 작업 내용
    work_summary = models.TextField('작업 요약', blank=True)
    parts_used = models.TextField('사용 부품/재료', blank=True)
    notes = models.TextField('특이사항', blank=True)
    
    # 고객 만족도
    satisfaction_score = models.PositiveIntegerField('만족도', 
                                                   validators=[MinValueValidator(1), MaxValueValidator(5)],
                                                   blank=True, null=True, 
                                                   help_text='1-5점 (5점이 최고)')
    customer_feedback = models.TextField('고객 피드백', blank=True)
    
    # 다음 서비스
    next_service_date = models.DateField('다음 서비스 권장일', blank=True, null=True)
    next_service_notes = models.TextField('다음 서비스 메모', blank=True)
    
    # 차량 관련 정보 (완료 시점의 차량 상태)
    vehicle_mileage_at_service = models.PositiveIntegerField('서비스 시 주행거리', blank=True, null=True)
    vehicle_condition_notes = models.TextField('차량 상태 메모', blank=True)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '서비스 이력'
        verbose_name_plural = '서비스 이력'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.service_request} - 이력"
    
    @property
    def customer(self):
        """연결된 고객 정보"""
        return self.service_request.customer
    
    @property
    def vehicle(self):
        """연결된 차량 정보"""
        return self.service_request.vehicle
    
    @property
    def service_duration_minutes(self):
        """실제 서비스 소요 시간(분)"""
        if self.actual_start_time and self.actual_end_time:
            delta = self.actual_end_time - self.actual_start_time
            return int(delta.total_seconds() / 60)
        return None
    
    def save(self, *args, **kwargs):
        # 서비스 이력이 생성될 때 차량 주행거리 업데이트
        if self.vehicle_mileage_at_service and self.service_request.vehicle:
            vehicle = self.service_request.vehicle
            if not vehicle.mileage or self.vehicle_mileage_at_service > vehicle.mileage:
                vehicle.mileage = self.vehicle_mileage_at_service
                vehicle.save()
        
        super().save(*args, **kwargs)
