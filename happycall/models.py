from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from services.models import ServiceRequest

User = get_user_model()

class HappyCall(models.Model):
    """해피콜 - 서비스 완료 후 고객 만족도 조사"""
    
    CALL_STAGE_CHOICES = [
        # 1차콜 (1주일 후) - 만족도 + 엔진오일 프로모션
        ('1st_pending_approval', '1차콜 생성승인대기'),
        ('1st_pending', '1차콜 대기'),
        ('1st_in_progress', '1차콜 진행중'),
        ('1st_completed', '1차콜 완료'),
        ('1st_failed', '1차콜 실패'),
        
        # 2차콜 (3개월 후) - 운행상태 + 서비스소개 + 보험상담의향
        ('2nd_pending_approval', '2차콜 생성승인대기'),
        ('2nd_pending', '2차콜 대기'),
        ('2nd_in_progress', '2차콜 진행중'),
        ('2nd_completed', '2차콜 완료'),
        ('2nd_failed', '2차콜 실패'),
        
        # 3차콜 (6개월 후) - 보험상담 (2차콜 의향확인 시에만)
        ('3rd_pending_approval', '3차콜 생성승인대기'),
        ('3rd_pending', '3차콜 대기'),
        ('3rd_in_progress', '3차콜 진행중'),
        ('3rd_completed', '3차콜 완료'),
        ('3rd_failed', '3차콜 실패'),
        
        # 4차콜 (9-12개월 후) - 다음 검사 안내 + 장기고객 관리
        ('4th_pending_approval', '4차콜 생성승인대기'),
        ('4th_pending', '4차콜 대기'),
        ('4th_in_progress', '4차콜 진행중'),
        ('4th_completed', '4차콜 완료'),
        ('4th_failed', '4차콜 실패'),
        
        ('skip', '건너뜀'),
        ('rejected', '고객거부'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('failed', '실패'),
        ('skip', '건너뜀'),
    ]
    
    SATISFACTION_CHOICES = [
        (5, '매우 만족'),
        (4, '만족'),
        (3, '보통'),
        (2, '불만족'),
        (1, '매우 불만족'),
    ]
    
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, verbose_name='서비스 요청')
    
    # 해피콜 기본 정보
    call_stage = models.CharField('콜 단계', max_length=20, choices=CALL_STAGE_CHOICES, default='1st_pending')
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 1차콜 정보
    first_call_scheduled_date = models.DateTimeField('1차콜 예정일시', null=True, blank=True)
    first_call_date = models.DateTimeField('1차콜 통화일시', null=True, blank=True)
    first_call_caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='1차콜 통화자', null=True, blank=True, related_name='first_calls')
    first_call_notes = models.TextField('1차콜 메모', blank=True)
    first_call_success = models.BooleanField('1차콜 성공', null=True, blank=True)
    
    # 2차콜 정보
    second_call_scheduled_date = models.DateTimeField('2차콜 예정일시', null=True, blank=True)
    second_call_date = models.DateTimeField('2차콜 통화일시', null=True, blank=True)
    second_call_caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='2차콜 통화자', null=True, blank=True, related_name='second_calls')
    second_call_notes = models.TextField('2차콜 메모', blank=True)
    second_call_success = models.BooleanField('2차콜 성공', null=True, blank=True)
    
    # 3차콜 정보
    third_call_scheduled_date = models.DateTimeField('3차콜 예정일시', null=True, blank=True)
    third_call_date = models.DateTimeField('3차콜 통화일시', null=True, blank=True)
    third_call_caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='3차콜 통화자', null=True, blank=True, related_name='third_calls')
    third_call_notes = models.TextField('3차콜 메모', blank=True)
    third_call_success = models.BooleanField('3차콜 성공', null=True, blank=True)
    
    # 4차콜 정보
    fourth_call_scheduled_date = models.DateTimeField('4차콜 예정일시', null=True, blank=True)
    fourth_call_date = models.DateTimeField('4차콜 통화일시', null=True, blank=True)
    fourth_call_caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='4차콜 통화자', null=True, blank=True, related_name='fourth_calls')
    fourth_call_notes = models.TextField('4차콜 메모', blank=True)
    fourth_call_success = models.BooleanField('4차콜 성공', null=True, blank=True)
    
    # 만족도 조사
    overall_satisfaction = models.IntegerField(
        '전체 만족도', 
        choices=SATISFACTION_CHOICES, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    service_quality = models.IntegerField(
        '서비스 품질', 
        choices=SATISFACTION_CHOICES, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    staff_kindness = models.IntegerField(
        '직원 친절도', 
        choices=SATISFACTION_CHOICES, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    price_satisfaction = models.IntegerField(
        '가격 만족도', 
        choices=SATISFACTION_CHOICES, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # 추가 의견
    customer_feedback = models.TextField('고객 의견', blank=True)
    improvement_suggestions = models.TextField('개선사항', blank=True)
    additional_needs = models.TextField('추가 요구사항', blank=True)
    
    # 재방문 의향
    will_revisit = models.BooleanField('재방문 의향', null=True, blank=True)
    recommend_to_others = models.BooleanField('타인 추천 의향', null=True, blank=True)
    
    # 1차콜 특화 필드 (엔진오일 프로모션)
    engine_oil_promotion_interest = models.BooleanField('엔진오일 프로모션 관심도', null=True, blank=True)
    engine_oil_promotion_notes = models.TextField('엔진오일 프로모션 메모', blank=True)
    
    # 2차콜 특화 필드 (보험 상담 의향)
    INSURANCE_INTEREST_CHOICES = [
        ('very_interested', '매우 관심'),
        ('interested', '관심있음'),
        ('neutral', '보통'),
        ('not_interested', '관심없음'),
        ('refused', '거부'),
    ]
    
    car_insurance_interest = models.CharField('자동차보험 관심도', max_length=20, 
                                            choices=INSURANCE_INTEREST_CHOICES, 
                                            null=True, blank=True)
    driver_insurance_interest = models.CharField('운전자보험 관심도', max_length=20, 
                                               choices=INSURANCE_INTEREST_CHOICES, 
                                               null=True, blank=True)
    insurance_consultation_requested = models.BooleanField('보험 상담 요청', null=True, blank=True)
    current_insurance_company = models.CharField('현재 보험사', max_length=100, blank=True)
    
    # 3차콜 특화 필드 (보험 상담 진행)
    insurance_consultation_completed = models.BooleanField('보험 상담 완료', null=True, blank=True)
    insurance_consultation_result = models.TextField('보험 상담 결과', blank=True)
    insurance_policy_applied = models.BooleanField('보험 가입 신청', null=True, blank=True)
    
    # 4차콜 특화 필드 (다음 검사 안내)
    next_inspection_scheduled = models.BooleanField('다음 검사 예약', null=True, blank=True)
    next_inspection_date = models.DateField('다음 검사 예약일', null=True, blank=True)
    long_term_customer_notes = models.TextField('장기고객 관리 메모', blank=True)
    
    # 통화 결과
    total_call_attempts = models.IntegerField('총 통화 시도 횟수', default=0)
    next_call_date = models.DateTimeField('다음 통화 예정일', null=True, blank=True)
    
    # 매출 통계 필드 (HappyCallRevenue와 연동)
    total_revenue_generated = models.DecimalField('총 발생 매출', max_digits=12, decimal_places=0, default=0)
    revenue_count = models.PositiveIntegerField('매출전표 수', default=0)
    
    # 승인 관리 필드
    manager_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                          verbose_name='팀장 승인자', null=True, blank=True, 
                                          related_name='manager_approved_calls')
    manager_approved_at = models.DateTimeField('팀장 승인일시', null=True, blank=True)
    
    admin_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        verbose_name='관리자 승인자', null=True, blank=True,
                                        related_name='admin_approved_calls')
    admin_approved_at = models.DateTimeField('관리자 승인일시', null=True, blank=True)
    
    # 추가 서비스 관심도
    additional_service_interest = models.BooleanField('추가 서비스 관심', null=True, blank=True)
    interested_service_notes = models.TextField('관심 서비스 메모', blank=True, help_text='고객이 관심있어하는 서비스나 후속조치 내용')
    follow_up_needed = models.BooleanField('후속 조치 필요', null=True, blank=True)
    
    # 고객 거부 의사
    customer_rejected = models.BooleanField('고객 거부', default=False)
    no_call_request = models.BooleanField('통화 금지 요청', default=False, help_text='고객이 향후 해피콜을 거부하는 경우')
    rejection_reason = models.TextField('거부 사유', blank=True)
    rejection_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                            verbose_name='거부 승인자', null=True, blank=True,
                                            related_name='rejection_approved_calls')
    rejection_approved_at = models.DateTimeField('거부 승인일시', null=True, blank=True)
    
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '해피콜'
        verbose_name_plural = '해피콜들'
        ordering = ['-first_call_scheduled_date', '-created_at']
    
    def __str__(self):
        return f"해피콜 - {self.service_request.customer.name} ({self.get_call_stage_display()})"
    
    @property
    def customer_name(self):
        return self.service_request.customer.name
    
    @property
    def customer_phone(self):
        return self.service_request.customer.phone
    
    @property
    def service_date(self):
        return self.service_request.preferred_date
    
    @property
    def service_description(self):
        return self.service_request.description
    
    @property
    def average_satisfaction(self):
        """평균 만족도 계산"""
        scores = [
            self.overall_satisfaction,
            self.service_quality, 
            self.staff_kindness,
            self.price_satisfaction
        ]
        valid_scores = [score for score in scores if score is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else None
    
    @property
    def current_call_stage_korean(self):
        """현재 콜 단계를 한글로 반환"""
        return self.get_call_stage_display()
    
    @property
    def current_stage_number(self):
        """현재 콜 단계 번호 반환 (1, 2, 3, 4)"""
        if self.call_stage.startswith('1st_'):
            return 1
        elif self.call_stage.startswith('2nd_'):
            return 2
        elif self.call_stage.startswith('3rd_'):
            return 3
        elif self.call_stage.startswith('4th_'):
            return 4
        return 0
    
    @property
    def is_pending_approval(self):
        """승인 대기 상태인지 확인"""
        return 'pending_approval' in self.call_stage
    
    @property
    def next_stage_available(self):
        """다음 단계로 넘어갈 수 있는지 확인"""
        current = self.current_stage_number
        if current == 2 and self.call_stage == '2nd_completed':
            # 3차콜은 보험 상담 의향이 있을 때만
            return (self.car_insurance_interest in ['very_interested', 'interested'] or 
                   self.driver_insurance_interest in ['very_interested', 'interested'])
        elif current in [1, 4] and f'{["","1st","2nd","3rd","4th"][current]}_completed' == self.call_stage:
            return True
        return False
    
    def get_scheduled_date_for_stage(self, stage_number):
        """단계별 예정일 반환"""
        field_map = {
            1: 'first_call_scheduled_date',
            2: 'second_call_scheduled_date', 
            3: 'third_call_scheduled_date',
            4: 'fourth_call_scheduled_date'
        }
        field_name = field_map.get(stage_number)
        return getattr(self, field_name) if field_name else None
    
    def get_caller_for_stage(self, stage_number):
        """단계별 통화자 반환"""
        field_map = {
            1: 'first_call_caller',
            2: 'second_call_caller',
            3: 'third_call_caller', 
            4: 'fourth_call_caller'
        }
        field_name = field_map.get(stage_number)
        return getattr(self, field_name) if field_name else None
    
    def move_to_next_stage(self):
        """다음 콜 단계로 이동 (승인 대기 상태로)"""
        stage_transitions = {
            '1st_completed': '2nd_pending_approval',
            '1st_failed': '2nd_pending_approval',
            '2nd_completed': '3rd_pending_approval' if self.next_stage_available else '4th_pending_approval',
            '2nd_failed': '4th_pending_approval',
            '3rd_completed': '4th_pending_approval',
            '3rd_failed': '4th_pending_approval',
        }
        
        next_stage = stage_transitions.get(self.call_stage)
        if next_stage:
            self.call_stage = next_stage
            self.save()
    
    def complete_current_stage(self):
        """현재 콜 단계를 완료로 변경"""
        stage_completion_map = {
            '1st_in_progress': ('1st_completed', 'first_call_success'),
            '2nd_in_progress': ('2nd_completed', 'second_call_success'), 
            '3rd_in_progress': ('3rd_completed', 'third_call_success'),
            '4th_in_progress': ('4th_completed', 'fourth_call_success')
        }
        
        completion_data = stage_completion_map.get(self.call_stage)
        if completion_data:
            new_stage, success_field = completion_data
            self.call_stage = new_stage
            setattr(self, success_field, True)
            self.save()
    
    def approve_stage_creation(self, approver, approval_type='manager'):
        """콜 단계 생성 승인 처리"""
        if approval_type == 'manager':
            self.manager_approved_by = approver
            self.manager_approved_at = timezone.now()
            # 관리자 승인도 필요한 경우 대기 상태 유지, 아니면 대기로 변경
            if self.call_stage.endswith('_pending_approval'):
                stage_prefix = self.call_stage.replace('_pending_approval', '')
                self.call_stage = f'{stage_prefix}_pending'
        elif approval_type == 'admin':
            self.admin_approved_by = approver
            self.admin_approved_at = timezone.now()
            # 최종 승인 완료, 실제 콜 대기 상태로 변경
            if self.call_stage.endswith('_pending_approval'):
                stage_prefix = self.call_stage.replace('_pending_approval', '') 
                self.call_stage = f'{stage_prefix}_pending'
        
        self.save()
    
    def update_revenue_stats(self):
        """매출 통계 업데이트"""
        from django.db.models import Sum, Count
        revenues = self.happycallrevenue_set.filter(status='completed')
        self.total_revenue_generated = revenues.aggregate(
            total=Sum('actual_amount'))['total'] or 0
        self.revenue_count = revenues.count()
        self.save()
    
    # Task 7.3: 실패된 콜의 다음 주기 대기 처리 + 예상 매출 이월 관리
    def defer_revenue_to_next_cycle(self):
        """콜 실패 시 예상 매출을 다음 주기로 이월"""
        from decimal import Decimal
        deferred_amount = Decimal('0')
        
        # 현재 단계에서 예상되던 매출을 계산
        current_stage_revenues = self.happycallrevenue_set.filter(
            call_stage=self.call_stage,
            status__in=['proposed', 'accepted']
        )
        
        for revenue in current_stage_revenues:
            deferred_amount += revenue.expected_amount
            # 매출 기록을 지연 상태로 변경
            revenue.status = 'deferred'
            # revenue.deferred_reason = f'콜 실패로 인한 {self.get_next_call_stage()}단계 이월'
            # revenue.deferred_at = timezone.now()
            revenue.save()
        
        # 다음 주기 대기 상태로 변경
        next_stage = self.get_next_call_stage()
        if next_stage:
            self.call_stage = f'{next_stage}_pending'
            self.deferred_revenue_amount = deferred_amount
            self.save()
            
            # 콜백 스케줄 생성
            self.create_callback_schedule(
                callback_reason='call_failed',
                expected_revenue=deferred_amount
            )
        
        return deferred_amount
    
    def get_next_call_stage(self):
        """다음 콜 단계 반환"""
        stage_progression = {
            '1st': '2nd',
            '2nd': '3rd', 
            '3rd': '4th',
            '4th': None  # 마지막 단계
        }
        current = self.call_stage.replace('_pending_approval', '').replace('_pending', '').replace('_completed', '')
        return stage_progression.get(current)
    
    def create_callback_schedule(self, callback_reason='customer_request', expected_revenue=None):
        """콜백 스케줄 생성 (Task 7.1 연동)"""
        from datetime import datetime, timedelta
        
        # 콜백 예정일 계산 (단계별 차등 적용)
        stage_to_days = {
            '1st': 7,   # 1주 후
            '2nd': 14,  # 2주 후  
            '3rd': 21,  # 3주 후
            '4th': 30,  # 한달 후
        }
        
        current_stage = self.call_stage.replace('_pending_approval', '').replace('_pending', '')
        callback_days = stage_to_days.get(current_stage, 14)
        
        callback_schedule = CallbackSchedule.objects.create(
            happy_call=self,
            callback_reason=callback_reason,
            scheduled_datetime=timezone.now() + timedelta(days=callback_days),
            potential_revenue=expected_revenue or self.calculate_stage_potential_revenue(),
            revenue_opportunity_maintained=True,
            created_by=None,  # 시스템 자동 생성
            notes=f'{current_stage}차 콜 실패로 인한 자동 콜백 생성'
        )
        
        return callback_schedule
    
    def calculate_stage_potential_revenue(self):
        """현재 단계의 잠재 매출 계산"""
        from decimal import Decimal
        
        # 단계별 평균 예상 매출 (히스토리컬 데이터 기반)
        stage_avg_revenue = {
            '1st': Decimal('50000'),   # 엔진오일 등
            '2nd': Decimal('200000'),  # 브레이크, 타이어 등
            '3rd': Decimal('150000'),  # 보험 중개수수료
            '4th': Decimal('300000'),  # VIP 패키지, 다음 검사
        }
        
        current_stage = self.call_stage.replace('_pending_approval', '').replace('_pending', '')
        return stage_avg_revenue.get(current_stage, Decimal('100000'))
    
    # Task 7.2: 콜 실패 시 고객 안내 문자 자동 발송 + 매출 기회 손실 기록
    def handle_call_failure(self, failure_reason='customer_unavailable', send_sms=True):
        """콜 실패 처리 - SMS 발송 및 매출 손실 기록"""
        from decimal import Decimal
        
        # 1. 콜 상태를 실패로 변경
        self.status = 'failed'
        self.call_stage = f'{self.call_stage}_failed'
        self.save()
        
        # 2. 매출 기회 손실 계산
        potential_loss = self.calculate_stage_potential_revenue()
        
        # 3. 매출 손실 기록 생성
        revenue_loss_record = CallFailureRevenueLoss.objects.create(
            happy_call=self,
            failed_stage=self.call_stage.replace('_failed', ''),
            failure_reason=failure_reason,
            estimated_revenue_loss=potential_loss,
            recorded_at=timezone.now(),
            recorded_by=None  # 시스템 자동 기록
        )
        
        # 4. 고객에게 안내 SMS 발송
        if send_sms:
            sms_sent = self.send_call_failure_sms(failure_reason)
            revenue_loss_record.sms_notification_sent = sms_sent
            revenue_loss_record.save()
        
        # 5. 다음 주기로 매출 이월
        deferred_amount = self.defer_revenue_to_next_cycle()
        
        return {
            'revenue_loss_record': revenue_loss_record,
            'deferred_amount': deferred_amount,
            'sms_sent': send_sms and sms_sent
        }
    
    def send_call_failure_sms(self, failure_reason):
        """콜 실패 시 고객 안내 SMS 발송"""
        try:
            customer = self.service_request.customer
            stage_names = {'1st': '1차', '2nd': '2차', '3rd': '3차', '4th': '4차'}
            current_stage = self.call_stage.replace('_failed', '').replace('_pending', '')
            stage_display = stage_names.get(current_stage, current_stage)
            
            # SMS 템플릿 선택
            sms_templates = {
                'customer_unavailable': f"""
안녕하세요, {customer.name}님.
운산카센터입니다.

{stage_display} 해피콜을 시도했으나 연결이 어려워 
다시 연락드리겠습니다.

편하신 시간에 연락 주시면 감사하겠습니다.
문의: 1588-0000
                """.strip(),
                
                'customer_busy': f"""
안녕하세요, {customer.name}님.
운산카센터입니다.

바쁘신 중에 {stage_display} 해피콜을 드려 죄송합니다.
다음 기회에 다시 연락드리겠습니다.

언제든 문의 주세요.
문의: 1588-0000
                """.strip(),
                
                'technical_issue': f"""
안녕하세요, {customer.name}님.
운산카센터입니다.

시스템 문제로 {stage_display} 해피콜이 지연되었습니다.
빠른 시일 내 다시 연락드리겠습니다.

문의: 1588-0000
                """.strip()
            }
            
            message = sms_templates.get(failure_reason, sms_templates['customer_unavailable'])
            
            # 실제 SMS API 호출 (현재는 mock)
            sms_result = self.send_sms_via_api(customer.phone, message)
            
            # SMS 발송 로그 기록
            SMSLog.objects.create(
                happy_call=self,
                phone_number=customer.phone,
                message_content=message,
                sent_at=timezone.now(),
                success=sms_result['success'],
                provider_response=sms_result.get('response', ''),
                sms_type='call_failure_notification'
            )
            
            return sms_result['success']
            
        except Exception as e:
            # SMS 발송 실패 로그
            SMSLog.objects.create(
                happy_call=self,
                phone_number=getattr(customer, 'phone', 'unknown'),
                message_content='SMS 발송 오류 발생',
                sent_at=timezone.now(),
                success=False,
                provider_response=str(e),
                sms_type='call_failure_notification'
            )
            return False
    
    def send_sms_via_api(self, phone_number, message):
        """SMS API 호출 (실제 구현 시 외부 API 연동)"""
        # TODO: 실제 SMS 서비스 API 연동 구현
        # 현재는 mock 응답 반환
        return {
            'success': True,
            'response': 'Mock SMS sent successfully',
            'message_id': f'mock_msg_{timezone.now().timestamp()}'
        }

class HappyCallRevenue(models.Model):
    """해피콜을 통한 매출 기록"""
    
    REVENUE_TYPE_CHOICES = [
        ('engine_oil', '엔진오일 프로모션'),
        ('additional_service', '추가 서비스'),
        ('insurance_commission', '보험 중개수수료'),
        ('next_inspection', '다음 검사 예약'),
        ('other', '기타'),
    ]
    
    STATUS_CHOICES = [
        ('proposed', '제안됨'),
        ('accepted', '수락됨'),
        ('voucher_created', '전표생성됨'),
        ('completed', '완료됨'),
        ('cancelled', '취소됨'),
        ('deferred', '다음 주기 이월'),  # Task 7.3: 매출 이월 상태 추가
    ]
    
    happy_call = models.ForeignKey(HappyCall, on_delete=models.CASCADE, verbose_name='해피콜')
    call_stage = models.CharField('콜 단계', max_length=20, choices=[
        ('1st', '1차콜'),
        ('2nd', '2차콜'), 
        ('3rd', '3차콜'),
        ('4th', '4차콜'),
    ])
    
    # 매출 유형 및 정보
    revenue_type = models.CharField('매출 유형', max_length=30, choices=REVENUE_TYPE_CHOICES)
    description = models.CharField('상세 설명', max_length=200, blank=True)
    
    # 매출전표 연결 (지연된 import로 처리)
    sales_voucher = models.OneToOneField('accounting.SalesVoucher', on_delete=models.CASCADE, 
                                       verbose_name='매출전표', null=True, blank=True)
    
    # 매출 정보
    expected_amount = models.DecimalField('예상 매출액', max_digits=12, decimal_places=0, default=0)
    actual_amount = models.DecimalField('실제 매출액', max_digits=12, decimal_places=0, default=0)
    commission_rate = models.DecimalField('수수료율(%)', max_digits=5, decimal_places=2, null=True, blank=True)
    commission_amount = models.DecimalField('수수료 금액', max_digits=12, decimal_places=0, default=0)
    
    # 상태 관리
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='proposed')
    
    # 기록 정보
    proposed_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='제안자')
    proposed_at = models.DateTimeField('제안일시', auto_now_add=True)
    accepted_at = models.DateTimeField('수락일시', null=True, blank=True)
    completed_at = models.DateTimeField('완료일시', null=True, blank=True)
    notes = models.TextField('비고', blank=True)
    
    # Task 7.3: 매출 이월 관련 필드 (임시 제거)
    # deferred_reason = models.TextField('이월 사유', blank=True, help_text='콜 실패 등으로 인한 매출 이월 사유')
    # deferred_at = models.DateTimeField('이월 일시', null=True, blank=True)
    
    class Meta:
        verbose_name = '해피콜 매출 기록'
        verbose_name_plural = '해피콜 매출 기록들'
        ordering = ['-proposed_at']
        indexes = [
            models.Index(fields=['happy_call', 'call_stage']),
            models.Index(fields=['revenue_type', 'status']),
            models.Index(fields=['proposed_at']),
        ]
    
    def __str__(self):
        return f"{self.happy_call} - {self.get_revenue_type_display()} ({self.actual_amount:,}원)"
    
    def save(self, *args, **kwargs):
        # 수수료 자동 계산
        if self.commission_rate and self.actual_amount:
            self.commission_amount = self.actual_amount * (self.commission_rate / 100)
        
        super().save(*args, **kwargs)
        
        # 해피콜의 매출 통계 업데이트
        if self.status == 'completed':
            self.happy_call.update_revenue_stats()
    
    def mark_as_completed(self):
        """매출 기록을 완료 상태로 변경"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def create_sales_voucher_data(self):
        """매출전표 생성을 위한 기본 데이터 반환"""
        customer = self.happy_call.service_request.customer
        return {
            'customer_name': customer.name,
            'customer_phone': customer.phone,
            'total_amount': self.expected_amount,
            'description': f'{self.get_revenue_type_display()} - {self.description}',
            'revenue_source': f'happy_call_{self.call_stage}',
            'happy_call_revenue': self,
        }


class CallRejection(models.Model):
    """Task 6.2: 고객 거부 의사 관리 (유형별 세분화)"""
    REJECTION_TYPE_CHOICES = [
        ('all_calls', '모든 해피콜 거부'),
        ('current_stage', '현재 단계만 거부'),
        ('remaining_stages', '이후 단계 거부'),
        ('specific_service', '특정 서비스 거부'),
    ]
    
    # Task 6.2: 고객 거부 사유 세분화
    CUSTOMER_REASON_CHOICES = [
        ('too_frequent', '전화가 너무 자주 옴'),
        ('not_interested', '서비스에 관심 없음'),
        ('financial_burden', '경제적 부담'),
        ('satisfied_with_current', '현재 서비스에 만족'),
        ('time_inconvenient', '통화 시간이 불편함'),
        ('privacy_concerns', '개인정보 우려'),
        ('bad_experience', '이전 서비스 불만족'),
        ('competitor_using', '타 업체 이용 중'),
        ('moving_relocating', '이사/이전 예정'),
        ('vehicle_sold', '차량 매각'),
        ('other', '기타'),
    ]
    
    # 고객 태도 분류
    CUSTOMER_ATTITUDE_CHOICES = [
        ('polite', '정중함'),
        ('neutral', '보통'),
        ('annoyed', '약간 짜증'),
        ('angry', '화남'),
        ('very_angry', '매우 화남'),
    ]
    
    # 향후 연락 가능 여부
    FUTURE_CONTACT_CHOICES = [
        ('yes', '필요시 연락 가능'),
        ('limited', '긴급시에만 연락'),
        ('no', '일체 연락 거부'),
    ]
    
    STATUS_CHOICES = [
        ('pending_review', '팀장 검토 대기'),
        ('manager_approved', '팀장 승인 - 관리자 검토 대기'),
        ('admin_approved', '관리자 최종 승인'),
        ('rejected', '승인 거부'),
    ]
    
    happy_call = models.ForeignKey(HappyCall, on_delete=models.CASCADE, verbose_name='해피콜')
    rejection_type = models.CharField('거부 유형', max_length=20, choices=REJECTION_TYPE_CHOICES)
    
    # Task 6.2: 세분화된 거부 정보
    customer_reason = models.CharField('고객 거부 사유', max_length=30, choices=CUSTOMER_REASON_CHOICES)
    customer_reason_details = models.TextField('상세 사유', blank=True, help_text='기타 선택 시 또는 추가 설명')
    customer_attitude = models.CharField('고객 태도', max_length=20, choices=CUSTOMER_ATTITUDE_CHOICES, blank=True)
    future_contact_ok = models.CharField('향후 연락 가능성', max_length=10, choices=FUTURE_CONTACT_CHOICES, blank=True)
    
    # 특정 서비스 거부 시
    rejected_services = models.JSONField('거부 서비스 목록', default=list, blank=True, 
                                       help_text='["engine_oil", "insurance", "additional_maintenance", "next_inspection"]')
    
    staff_notes = models.TextField('담당자 메모', blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_rejections', verbose_name='요청자')
    
    # Task 6.4: 매출 기회 손실 추적
    estimated_revenue_loss = models.DecimalField('예상 매출 손실', max_digits=12, decimal_places=0, default=0)
    current_stage_loss = models.DecimalField('현재 단계 손실', max_digits=12, decimal_places=0, default=0)
    
    # Task 6.3: 다단계 승인 시스템
    status = models.CharField('처리 상태', max_length=30, choices=STATUS_CHOICES, default='pending_review')
    manager_reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                          related_name='manager_reviewed_rejections', verbose_name='팀장 검토자')
    manager_reviewed_at = models.DateTimeField('팀장 검토일', null=True, blank=True)
    manager_notes = models.TextField('팀장 검토 의견', blank=True)
    
    admin_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                        related_name='admin_approved_rejections', verbose_name='관리자 승인자')
    admin_approved_at = models.DateTimeField('관리자 승인일', null=True, blank=True)
    admin_notes = models.TextField('관리자 승인 의견', blank=True)
    
    # 거부 처리 완료 후 추적
    rejection_applied = models.BooleanField('거부 처리 적용됨', default=False)
    applied_at = models.DateTimeField('적용일', null=True, blank=True)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '고객 거부 요청'
        verbose_name_plural = '고객 거부 요청들'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['rejection_type', 'customer_reason']),
            models.Index(fields=['happy_call', 'status']),
        ]
    
    def __str__(self):
        return f"{self.happy_call.service_request.customer_name} - {self.get_rejection_type_display()}"
    
    def can_be_approved_by_manager(self):
        """팀장이 승인할 수 있는지 확인"""
        return self.status == 'pending_review'
    
    def can_be_approved_by_admin(self):
        """관리자가 최종 승인할 수 있는지 확인"""
        return self.status == 'manager_approved'
    
    def approve_by_manager(self, manager_user, notes=''):
        """팀장 승인"""
        if not self.can_be_approved_by_manager():
            raise ValueError("팀장 승인이 불가능한 상태입니다.")
        
        self.status = 'manager_approved'
        self.manager_reviewed_by = manager_user
        self.manager_reviewed_at = timezone.now()
        self.manager_notes = notes
        self.save()
    
    def approve_by_admin(self, admin_user, notes=''):
        """관리자 최종 승인 및 적용"""
        if not self.can_be_approved_by_admin():
            raise ValueError("관리자 승인이 불가능한 상태입니다.")
        
        self.status = 'admin_approved'
        self.admin_approved_by = admin_user
        self.admin_approved_at = timezone.now()
        self.admin_notes = notes
        self.save()
        
        # Task 6.4: 거부 처리 적용
        self.apply_rejection()
    
    def apply_rejection(self):
        """Task 6.4: 승인된 거부 의사에 따른 해당 콜 자동 제외"""
        if self.status != 'admin_approved' or self.rejection_applied:
            return
        
        happycall = self.happy_call
        
        if self.rejection_type == 'all_calls':
            # 모든 해피콜 시리즈 중단
            happycall.call_stage = 'rejected_all'
            happycall.status = 'rejected'
            happycall.rejection_reason = 'customer_request_all'
            
        elif self.rejection_type == 'current_stage':
            # 현재 단계만 거부
            stage_prefix = happycall.call_stage.split('_')[0]  # '1st', '2nd', etc.
            happycall.call_stage = f'{stage_prefix}_rejected'
            
        elif self.rejection_type == 'remaining_stages':
            # 이후 단계 거부
            happycall.remaining_stages_rejected = True
            happycall.rejection_reason = 'customer_request_remaining'
            
        elif self.rejection_type == 'specific_service':
            # 특정 서비스 거부 - JSON 필드에 저장
            current_rejected = happycall.rejected_services or []
            for service in self.rejected_services:
                if service not in current_rejected:
                    current_rejected.append(service)
            happycall.rejected_services = current_rejected
        
        happycall.save()
        
        # 적용 완료 표시
        self.rejection_applied = True
        self.applied_at = timezone.now()
        self.save()
    
    def get_revenue_loss_display(self):
        """매출 손실 표시"""
        if self.estimated_revenue_loss:
            return f"₩{self.estimated_revenue_loss:,}"
        return "₩0"
        return f"{self.happy_call} - {self.get_rejection_type_display()} ({self.get_status_display()})"
    
    def approve_rejection(self, reviewer):
        """거부 요청 승인"""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        
        # 해피콜 상태 업데이트
        if self.rejection_type == 'all_calls':
            self.happy_call.call_stage = 'rejected'
            self.happy_call.customer_rejected = True
            self.happy_call.rejection_reason = self.customer_reason
            self.happy_call.rejection_approved_by = reviewer
            self.happy_call.rejection_approved_at = timezone.now()
            self.happy_call.save()
    
    def reject_request(self, reviewer, reason):
        """거부 요청 반려"""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = reason
        self.save()


class CallbackSchedule(models.Model):
    """Task 7: 콜백 스케줄 관리 (매출 기회 추적 포함)"""
    
    CALLBACK_TYPE_CHOICES = [
        ('customer_request', '고객 요청'),
        ('failed_call', '콜 실패 후 재시도'),
        ('specific_time', '특정 시간 재연락'),
        ('technical_issue', '기술적 문제'),
        ('schedule_conflict', '일정 충돌'),
        ('follow_up', '후속 연락'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', '예정됨'),
        ('in_progress', '진행중'),
        ('completed', '완료됨'),
        ('failed', '실패'),
        ('cancelled', '취소됨'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '낮음'),
        ('normal', '보통'),
        ('high', '높음'),
        ('urgent', '긴급'),
    ]
    
    happy_call = models.ForeignKey(HappyCall, on_delete=models.CASCADE, verbose_name='해피콜')
    original_call_stage = models.CharField('원래 콜 단계', max_length=20)
    callback_type = models.CharField('콜백 유형', max_length=20, choices=CALLBACK_TYPE_CHOICES)
    
    # Task 7.1: 매출 기회 추적
    potential_revenue = models.DecimalField('예상 매출', max_digits=12, decimal_places=0, default=0)
    revenue_opportunity_maintained = models.BooleanField('매출 기회 유지', default=True)
    expected_services = models.JSONField('예상 서비스 목록', default=list, blank=True, 
                                       help_text='["engine_oil", "insurance", "maintenance"]')
    
    # 스케줄 정보
    scheduled_date = models.DateTimeField('예정 일시')
    preferred_time_start = models.TimeField('선호 시작 시간', null=True, blank=True)
    preferred_time_end = models.TimeField('선호 종료 시간', null=True, blank=True)
    priority = models.CharField('우선순위', max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Task 7.4: 원래 콜과의 연관 관계 추적
    original_attempt_date = models.DateTimeField('원래 콜 시도 일시', null=True, blank=True)
    callback_count = models.PositiveIntegerField('콜백 횟수', default=1)
    max_callback_attempts = models.PositiveIntegerField('최대 콜백 시도', default=3)
    
    # 담당자 정보
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='담당자', 
                                  related_name='callback_assignments')
    
    # 실행 정보
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='scheduled')
    attempted_at = models.DateTimeField('시도 일시', null=True, blank=True)
    completed_at = models.DateTimeField('완료 일시', null=True, blank=True)
    
    # 결과 및 메모
    result_notes = models.TextField('결과 메모', blank=True)
    customer_notes = models.TextField('고객 요청사항', blank=True)
    callback_reason = models.TextField('콜백 사유', blank=True)
    
    # Task 7.2: SMS 발송 정보 확장
    sms_sent = models.BooleanField('안내 문자 발송', default=False)
    sms_sent_at = models.DateTimeField('문자 발송 일시', null=True, blank=True)
    sms_template_used = models.CharField('사용된 SMS 템플릿', max_length=50, blank=True)
    sms_delivery_status = models.CharField('SMS 전송 상태', max_length=20, blank=True)
    
    # Task 7.3: 다음 주기 대기 처리
    moved_to_next_cycle = models.BooleanField('다음 주기로 이동', default=False)
    next_cycle_date = models.DateTimeField('다음 주기 예정일', null=True, blank=True)
    revenue_deferred = models.DecimalField('이월된 매출 기회', max_digits=12, decimal_places=0, default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='생성자')
    created_at = models.DateTimeField('생성일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)
    
    class Meta:
        verbose_name = '콜백 스케줄'
        verbose_name_plural = '콜백 스케줄들'
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['happy_call', 'status']),
            models.Index(fields=['assigned_to', 'scheduled_date']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.happy_call} - 콜백 ({self.scheduled_date.strftime('%Y-%m-%d %H:%M')})"
    
    def mark_as_completed(self, result_notes=''):
        """콜백을 완료로 처리"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.result_notes = result_notes
        self.save()
    
    def mark_as_failed(self, result_notes=''):
        """콜백을 실패로 처리"""
        self.status = 'failed'
        self.attempted_at = timezone.now()
        self.result_notes = result_notes
        
        # Task 7.3: 최대 시도 횟수 확인 후 다음 주기 이동 결정
        if self.callback_count >= self.max_callback_attempts:
            self.move_to_next_cycle()
        else:
            # 다음 콜백 스케줄 생성
            self.schedule_next_callback()
        
        self.save()
    
    def move_to_next_cycle(self):
        """Task 7.3: 실패된 콜의 다음 주기 대기 처리"""
        self.moved_to_next_cycle = True
        
        # 다음 주기 날짜 계산 (현재 단계에 따라)
        stage_to_days = {
            '1st': 90,   # 1차 실패 -> 2차로 이동 (3개월)
            '2nd': 90,   # 2차 실패 -> 3차로 이동 (3개월)
            '3rd': 120,  # 3차 실패 -> 4차로 이동 (4개월)
            '4th': 365   # 4차 실패 -> 1년 후 재시작
        }
        
        stage_prefix = self.original_call_stage.split('_')[0]
        days_to_add = stage_to_days.get(stage_prefix, 90)
        
        self.next_cycle_date = timezone.now() + timedelta(days=days_to_add)
        self.revenue_deferred = self.potential_revenue  # 매출 기회 이월
        
        # 해피콜 상태 업데이트
        self.happy_call.add_deferred_revenue(self.potential_revenue)
    
    def schedule_next_callback(self):
        """다음 콜백 스케줄 생성"""
        # 콜백 횟수 증가하여 새로운 콜백 생성
        next_callback = CallbackSchedule.objects.create(
            happy_call=self.happy_call,
            original_call_stage=self.original_call_stage,
            callback_type='failed_call',
            potential_revenue=self.potential_revenue,
            expected_services=self.expected_services,
            scheduled_date=timezone.now() + timedelta(days=1),  # 하루 후 재시도
            priority='high' if self.callback_count >= 2 else 'normal',
            original_attempt_date=self.original_attempt_date or self.created_at,
            callback_count=self.callback_count + 1,
            assigned_to=self.assigned_to,
            created_by=self.created_by,
            callback_reason=f'{self.callback_count + 1}차 콜백 시도'
        )
        
        return next_callback
    
    def send_customer_notification_sms(self, template_type='default'):
        """Task 7.2: 고객에게 콜 실패 안내 문자 발송 (확장된 기능)"""
        customer_phone = self.happy_call.service_request.customer.phone_number
        
        # SMS 템플릿 선택
        templates = {
            'default': f"안녕하세요. 검사 후 만족도 조사를 위해 연락드렸으나 통화가 어려워 다음에 다시 연락드리겠습니다. 문의: 1234-5678",
            'callback_scheduled': f"안녕하세요. 고객님께서 요청하신 시간({self.scheduled_date.strftime('%m월 %d일 %H시')})에 다시 연락드리겠습니다. 문의: 1234-5678",
            'final_attempt': f"안녕하세요. 해피콜 관련하여 마지막으로 연락드립니다. 추가 문의사항이 있으시면 1234-5678로 연락주세요.",
            'next_cycle': f"안녕하세요. 다음 서비스 시기({self.next_cycle_date.strftime('%Y년 %m월')})에 다시 안내드리겠습니다. 문의: 1234-5678"
        }
        
        message = templates.get(template_type, templates['default'])
        
        # TODO: 실제 SMS API 연동 구현
        # delivery_result = sms_service.send(customer_phone, message)
        
        # Mock SMS 발송 (실제로는 SMS API 결과 처리)
        self.sms_sent = True
        self.sms_sent_at = timezone.now()
        self.sms_template_used = template_type
        self.sms_delivery_status = 'sent'  # 'sent', 'failed', 'delivered'
        self.save()
        
        return True
    
    def calculate_revenue_opportunity_impact(self):
        """Task 7.4: 매출 기회 영향 계산"""
        return {
            'potential_revenue': self.potential_revenue,
            'opportunity_maintained': self.revenue_opportunity_maintained,
            'days_delayed': (timezone.now().date() - self.original_attempt_date.date()).days if self.original_attempt_date else 0,
            'revenue_at_risk': self.potential_revenue if not self.revenue_opportunity_maintained else 0
        }
    
    # Task 7.4: 콜백과 원래 콜의 연관 관계 + 매출 히스토리 통합 추적
    def get_callback_chain(self):
        """현재 콜백의 전체 체인 조회 (원래 콜 -> 콜백들)"""
        # 같은 해피콜의 같은 단계에서 발생한 모든 콜백들을 시간순으로 반환
        all_callbacks = CallbackSchedule.objects.filter(
            happy_call=self.happy_call,
            original_call_stage=self.original_call_stage
        ).order_by('created_at')
        
        return {
            'original_call': {
                'stage': self.original_call_stage,
                'attempt_date': self.original_attempt_date,
                'potential_revenue': self.potential_revenue
            },
            'callbacks': list(all_callbacks.values(
                'id', 'callback_count', 'status', 'created_at', 
                'attempted_at', 'completed_at', 'result_notes'
            )),
            'total_callbacks': all_callbacks.count(),
            'success_rate': self.calculate_callback_success_rate(),
            'total_revenue_impact': self.calculate_total_revenue_impact()
        }
    
    def calculate_callback_success_rate(self):
        """콜백 성공률 계산"""
        callbacks = CallbackSchedule.objects.filter(
            happy_call=self.happy_call,
            original_call_stage=self.original_call_stage
        )
        
        total_callbacks = callbacks.count()
        successful_callbacks = callbacks.filter(status='completed').count()
        
        if total_callbacks == 0:
            return 0.0
            
        return (successful_callbacks / total_callbacks) * 100
    
    def calculate_total_revenue_impact(self):
        """전체 매출 영향 계산"""
        callbacks = CallbackSchedule.objects.filter(
            happy_call=self.happy_call,
            original_call_stage=self.original_call_stage
        )
        
        # 실제 달성된 매출 조회
        achieved_revenues = HappyCallRevenue.objects.filter(
            happy_call=self.happy_call,
            call_stage=self.original_call_stage.replace('_', ''),
            status='completed'
        )
        
        achieved_amount = sum(revenue.actual_amount for revenue in achieved_revenues)
        
        return {
            'original_potential': self.potential_revenue,
            'achieved_revenue': achieved_amount,
            'achievement_rate': (achieved_amount / self.potential_revenue * 100) if self.potential_revenue > 0 else 0,
            'lost_opportunity': max(0, self.potential_revenue - achieved_amount),
            'callback_cost_estimate': self.estimate_callback_costs(),
            'roi': self.calculate_callback_roi(achieved_amount)
        }
    
    def estimate_callback_costs(self):
        """콜백 비용 추정 (SMS + 인건비 등)"""
        callbacks = CallbackSchedule.objects.filter(
            happy_call=self.happy_call,
            original_call_stage=self.original_call_stage
        )
        
        # 기본 비용 추정
        sms_cost = 50  # SMS 발송비 (원)
        staff_time_cost = 5000  # 담당자 시간당 비용 (원) 
        avg_call_time_minutes = 10  # 평균 통화 시간 (분)
        
        total_sms_sent = callbacks.filter(sms_sent=True).count()
        total_call_attempts = callbacks.exclude(status='scheduled').count()
        
        estimated_cost = (
            (total_sms_sent * sms_cost) + 
            (total_call_attempts * (staff_time_cost * avg_call_time_minutes / 60))
        )
        
        return estimated_cost
    
    def calculate_callback_roi(self, achieved_revenue):
        """콜백 ROI 계산"""
        callback_costs = self.estimate_callback_costs()
        
        if callback_costs == 0:
            return float('inf') if achieved_revenue > 0 else 0
            
        roi = ((achieved_revenue - callback_costs) / callback_costs) * 100
        return max(-100, roi)  # 최소 -100%로 제한
    
    def get_revenue_history_integration(self):
        """Task 7.4: 매출 히스토리 통합 추적"""
        # 해당 해피콜의 전체 매출 히스토리와 콜백의 연관성 분석
        happycall_revenues = HappyCallRevenue.objects.filter(
            happy_call=self.happy_call
        ).order_by('proposed_at')
        
        callback_chain = self.get_callback_chain()
        
        return {
            'happy_call_id': self.happy_call.id,
            'customer_info': {
                'name': self.happy_call.service_request.customer.name,
                'phone': self.happy_call.service_request.customer.phone,
            },
            'original_call_timeline': {
                'stage': self.original_call_stage,
                'original_attempt': self.original_attempt_date,
                'callback_chain': callback_chain
            },
            'revenue_progression': [
                {
                    'stage': rev.call_stage,
                    'revenue_type': rev.revenue_type,
                    'proposed_at': rev.proposed_at,
                    'status': rev.status,
                    'expected_amount': rev.expected_amount,
                    'actual_amount': rev.actual_amount,
                    'related_to_callback': self.is_revenue_from_callback(rev)
                }
                for rev in happycall_revenues
            ],
            'callback_impact_summary': {
                'total_callbacks': callback_chain['total_callbacks'],
                'success_rate': callback_chain['success_rate'],
                'revenue_impact': callback_chain['total_revenue_impact'],
                'cost_benefit': self.analyze_callback_cost_benefit()
            }
        }
    
    def is_revenue_from_callback(self, revenue):
        """매출이 콜백에서 발생했는지 판단"""
        # 매출 제안 시점이 콜백 시도 이후인지 확인
        callback_attempts = CallbackSchedule.objects.filter(
            happy_call=self.happy_call,
            original_call_stage=self.original_call_stage,
            attempted_at__lte=revenue.proposed_at
        ).order_by('-attempted_at')
        
        return callback_attempts.exists()
    
    def analyze_callback_cost_benefit(self):
        """콜백 비용 대비 효과 분석"""
        revenue_impact = self.calculate_total_revenue_impact()
        
        cost_benefit_ratio = 0
        if revenue_impact['callback_cost_estimate'] > 0:
            cost_benefit_ratio = revenue_impact['achieved_revenue'] / revenue_impact['callback_cost_estimate']
        
        return {
            'cost_benefit_ratio': cost_benefit_ratio,
            'break_even_achieved': cost_benefit_ratio >= 1.0,
            'recommendation': self.generate_callback_recommendation(cost_benefit_ratio),
            'efficiency_score': min(100, cost_benefit_ratio * 20)  # 0-100 스코어
        }
    
    def generate_callback_recommendation(self, cost_benefit_ratio):
        """콜백 전략 추천"""
        if cost_benefit_ratio >= 3.0:
            return "매우 효과적 - 콜백 전략 확대 권장"
        elif cost_benefit_ratio >= 1.5:
            return "효과적 - 현재 콜백 전략 유지 권장"
        elif cost_benefit_ratio >= 1.0:
            return "손익분기점 달성 - 콜백 방식 개선 고려"
        elif cost_benefit_ratio >= 0.5:
            return "비효율적 - 콜백 전략 재검토 필요"
        else:
            return "매우 비효율적 - 콜백 중단 또는 전면 재설계 권장"
    
    def get_callback_history(self):
        """Task 7.4: 해당 해피콜의 모든 콜백 이력"""
        return CallbackSchedule.objects.filter(
            happy_call=self.happy_call,
            original_call_stage=self.original_call_stage
        ).order_by('created_at')
    
    @classmethod
    def create_from_failed_call(cls, happy_call, stage, reason, user, potential_revenue=0, expected_services=None):
        """콜 실패 시 콜백 스케줄 생성"""
        return cls.objects.create(
            happy_call=happy_call,
            original_call_stage=stage,
            callback_type='failed_call',
            potential_revenue=potential_revenue,
            expected_services=expected_services or [],
            scheduled_date=timezone.now() + timedelta(hours=24),
            priority='normal',
            original_attempt_date=timezone.now(),
            assigned_to=user,
            created_by=user,
            callback_reason=reason
        )


class HappyCallTemplate(models.Model):
    """해피콜 스크립트 템플릿"""
    
    name = models.CharField('템플릿명', max_length=100)
    description = models.TextField('설명', blank=True)
    script_content = models.TextField('스크립트 내용')
    is_active = models.BooleanField('활성화', default=True)
    
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '해피콜 템플릿'
        verbose_name_plural = '해피콜 템플릿들'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Task 7.2: 콜 실패로 인한 매출 손실 추적 모델
class CallFailureRevenueLoss(models.Model):
    """콜 실패로 인한 매출 기회 손실 기록"""
    
    FAILURE_REASON_CHOICES = [
        ('customer_unavailable', '고객 부재'),
        ('customer_busy', '고객 바쁨'),
        ('technical_issue', '기술적 문제'),
        ('customer_refused', '고객 거부'),
        ('staff_unavailable', '담당자 부재'),
        ('system_error', '시스템 오류'),
        ('other', '기타'),
    ]
    
    happy_call = models.ForeignKey(HappyCall, on_delete=models.CASCADE, verbose_name='해피콜')
    failed_stage = models.CharField('실패 단계', max_length=20, choices=[
        ('1st', '1차콜'),
        ('2nd', '2차콜'), 
        ('3rd', '3차콜'),
        ('4th', '4차콜'),
    ])
    
    failure_reason = models.CharField('실패 사유', max_length=30, choices=FAILURE_REASON_CHOICES)
    estimated_revenue_loss = models.DecimalField('예상 매출 손실액', max_digits=12, decimal_places=0)
    
    # SMS 발송 정보
    sms_notification_sent = models.BooleanField('안내 문자 발송', default=False)
    sms_sent_at = models.DateTimeField('문자 발송 시간', null=True, blank=True)
    
    # 기록 정보
    recorded_at = models.DateTimeField('기록 일시', auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name='기록자')
    
    # 후속 처리
    callback_scheduled = models.BooleanField('콜백 예약됨', default=False)
    revenue_recovered = models.BooleanField('매출 회복됨', default=False)
    recovered_amount = models.DecimalField('회복된 매출액', max_digits=12, decimal_places=0, default=0)
    recovery_date = models.DateTimeField('회복 일자', null=True, blank=True)
    
    class Meta:
        verbose_name = '콜 실패 매출 손실 기록'
        verbose_name_plural = '콜 실패 매출 손실 기록들'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['happy_call', 'failed_stage']),
            models.Index(fields=['failure_reason', 'recorded_at']),
            models.Index(fields=['revenue_recovered']),
        ]
    
    def __str__(self):
        return f"{self.happy_call} - {self.failed_stage} ({self.estimated_revenue_loss:,}원 손실)"
    
    def mark_revenue_recovered(self, recovered_amount, recovery_source='callback_success'):
        """매출 회복 처리"""
        self.revenue_recovered = True
        self.recovered_amount = recovered_amount
        self.recovery_date = timezone.now()
        self.save()
        
        # 매출 회복 로그 생성
        RevenueRecoveryLog.objects.create(
            failure_record=self,
            recovered_amount=recovered_amount,
            recovery_source=recovery_source,
            recovery_date=timezone.now()
        )


# Task 7.2: SMS 발송 로그 추적
class SMSLog(models.Model):
    """SMS 발송 로그"""
    
    SMS_TYPE_CHOICES = [
        ('call_failure_notification', '콜 실패 안내'),
        ('callback_reminder', '콜백 리마인더'),
        ('revenue_proposal', '매출 제안'),
        ('satisfaction_survey', '만족도 조사'),
        ('other', '기타'),
    ]
    
    happy_call = models.ForeignKey(HappyCall, on_delete=models.CASCADE, verbose_name='해피콜')
    phone_number = models.CharField('전화번호', max_length=20)
    message_content = models.TextField('메시지 내용')
    sms_type = models.CharField('SMS 유형', max_length=30, choices=SMS_TYPE_CHOICES)
    
    # 발송 결과
    sent_at = models.DateTimeField('발송 시간', auto_now_add=True)
    success = models.BooleanField('발송 성공', default=False)
    provider_response = models.TextField('발송 결과 응답', blank=True)
    cost = models.DecimalField('발송 비용', max_digits=8, decimal_places=0, default=0)
    
    # 메시지 추적
    delivery_confirmed = models.BooleanField('전달 확인', default=False)
    delivery_confirmed_at = models.DateTimeField('전달 확인 시간', null=True, blank=True)
    read_confirmed = models.BooleanField('읽기 확인', default=False) 
    read_confirmed_at = models.DateTimeField('읽기 확인 시간', null=True, blank=True)
    
    class Meta:
        verbose_name = 'SMS 발송 로그'
        verbose_name_plural = 'SMS 발송 로그들'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['happy_call', 'sms_type']),
            models.Index(fields=['success', 'sent_at']),
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        status = '성공' if self.success else '실패'
        return f"{self.phone_number} - {self.get_sms_type_display()} ({status})"


# Task 7.4: 매출 회복 로그 (콜백 성공으로 인한 매출 회복 추적)  
class RevenueRecoveryLog(models.Model):
    """매출 회복 로그"""
    
    RECOVERY_SOURCE_CHOICES = [
        ('callback_success', '콜백 성공'),
        ('customer_contact', '고객 직접 연락'),
        ('next_stage_success', '다음 단계 성공'),
        ('alternative_channel', '대체 채널'),
        ('other', '기타'),
    ]
    
    failure_record = models.ForeignKey(CallFailureRevenueLoss, on_delete=models.CASCADE, 
                                     verbose_name='실패 기록', related_name='recovery_logs')
    recovered_amount = models.DecimalField('회복된 매출액', max_digits=12, decimal_places=0)
    recovery_source = models.CharField('회복 경로', max_length=30, choices=RECOVERY_SOURCE_CHOICES)
    recovery_date = models.DateTimeField('회복 일자', auto_now_add=True)
    
    # 회복률 계산
    recovery_rate = models.DecimalField('회복률', max_digits=5, decimal_places=2, default=0.00,
                                       help_text='원래 손실 대비 회복 비율 (%)')
    
    notes = models.TextField('회복 경위', blank=True)
    
    class Meta:
        verbose_name = '매출 회복 로그'
        verbose_name_plural = '매출 회복 로그들'
        ordering = ['-recovery_date']
    
    def save(self, *args, **kwargs):
        # 회복률 자동 계산
        if self.failure_record and self.failure_record.estimated_revenue_loss > 0:
            self.recovery_rate = (self.recovered_amount / self.failure_record.estimated_revenue_loss) * 100
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.failure_record.happy_call} 매출 회복 - {self.recovered_amount:,}원 ({self.recovery_rate:.1f}%)"


# Task 7.5: 콜 실패율과 매출 손실 상관관계 분석을 위한 매니저
class CallFailureAnalysisManager:
    """콜 실패율과 매출 손실 상관관계 분석 매니저"""
    
    @staticmethod
    def generate_failure_revenue_correlation_report(date_from=None, date_to=None):
        """Task 7.5: 콜 실패율과 매출 손실 상관관계 분석 리포트 생성"""
        from django.db.models import Count, Sum, Avg, Q
        from datetime import datetime, timedelta
        
        if not date_from:
            date_from = timezone.now() - timedelta(days=90)  # 기본 3개월
        if not date_to:
            date_to = timezone.now()
        
        # 1. 전체 해피콜 통계
        total_happycalls = HappyCall.objects.filter(
            created_at__range=[date_from, date_to]
        )
        
        # 2. 실패한 콜들 통계
        failed_calls = total_happycalls.filter(
            status='failed'
        )
        
        # 3. 콜백 스케줄 통계
        callbacks = CallbackSchedule.objects.filter(
            created_at__range=[date_from, date_to]
        )
        
        # 4. 매출 손실 기록 통계
        revenue_losses = CallFailureRevenueLoss.objects.filter(
            recorded_at__range=[date_from, date_to]
        )
        
        # 5. 단계별 실패율 및 매출 손실 분석
        stage_analysis = CallFailureAnalysisManager.analyze_by_call_stage(date_from, date_to)
        
        # 6. 실패 사유별 분석
        reason_analysis = CallFailureAnalysisManager.analyze_by_failure_reason(date_from, date_to)
        
        # 7. 매출 회복 분석
        recovery_analysis = CallFailureAnalysisManager.analyze_revenue_recovery(date_from, date_to)
        
        # 8. 상관관계 분석
        correlation_analysis = CallFailureAnalysisManager.calculate_failure_revenue_correlation()
        
        return {
            'report_period': {
                'start_date': date_from,
                'end_date': date_to,
                'duration_days': (date_to - date_from).days
            },
            'overall_statistics': {
                'total_happy_calls': total_happycalls.count(),
                'failed_calls': failed_calls.count(),
                'failure_rate': (failed_calls.count() / total_happycalls.count() * 100) if total_happycalls.count() > 0 else 0,
                'total_callbacks_created': callbacks.count(),
                'callback_success_rate': CallFailureAnalysisManager.calculate_overall_callback_success_rate(callbacks),
                'total_revenue_loss': revenue_losses.aggregate(total=Sum('estimated_revenue_loss'))['total'] or 0,
                'total_revenue_recovered': revenue_losses.aggregate(total=Sum('recovered_amount'))['total'] or 0
            },
            'stage_analysis': stage_analysis,
            'reason_analysis': reason_analysis,
            'recovery_analysis': recovery_analysis,
            'correlation_analysis': correlation_analysis,
            'recommendations': CallFailureAnalysisManager.generate_improvement_recommendations(
                stage_analysis, reason_analysis, recovery_analysis
            )
        }
    
    @staticmethod
    def analyze_by_call_stage(date_from, date_to):
        """단계별 실패율 및 매출 손실 분석"""
        from django.db.models import Count, Sum, Avg
        
        stages = ['1st', '2nd', '3rd', '4th']
        stage_data = {}
        
        for stage in stages:
            # 해당 단계의 전체 콜 수
            stage_calls = HappyCall.objects.filter(
                created_at__range=[date_from, date_to],
                call_stage__icontains=stage
            )
            
            # 해당 단계의 실패 콜 수
            failed_stage_calls = stage_calls.filter(status='failed')
            
            # 해당 단계의 매출 손실
            stage_losses = CallFailureRevenueLoss.objects.filter(
                recorded_at__range=[date_from, date_to],
                failed_stage=stage
            )
            
            # 해당 단계의 콜백 성공률
            stage_callbacks = CallbackSchedule.objects.filter(
                created_at__range=[date_from, date_to],
                original_call_stage__icontains=stage
            )
            
            successful_callbacks = stage_callbacks.filter(status='completed')
            
            stage_data[stage] = {
                'total_calls': stage_calls.count(),
                'failed_calls': failed_stage_calls.count(),
                'failure_rate': (failed_stage_calls.count() / stage_calls.count() * 100) if stage_calls.count() > 0 else 0,
                'total_revenue_loss': stage_losses.aggregate(total=Sum('estimated_revenue_loss'))['total'] or 0,
                'avg_loss_per_failure': stage_losses.aggregate(avg=Avg('estimated_revenue_loss'))['avg'] or 0,
                'callbacks_created': stage_callbacks.count(),
                'callbacks_successful': successful_callbacks.count(),
                'callback_success_rate': (successful_callbacks.count() / stage_callbacks.count() * 100) if stage_callbacks.count() > 0 else 0,
                'revenue_recovery_rate': CallFailureAnalysisManager.calculate_stage_recovery_rate(stage, date_from, date_to)
            }
        
        return stage_data
    
    @staticmethod
    def analyze_by_failure_reason(date_from, date_to):
        """실패 사유별 분석"""
        from django.db.models import Count, Sum, Avg
        
        reason_data = {}
        
        failure_reasons = CallFailureRevenueLoss.objects.filter(
            recorded_at__range=[date_from, date_to]
        ).values('failure_reason').distinct()
        
        for reason_obj in failure_reasons:
            reason = reason_obj['failure_reason']
            
            reason_losses = CallFailureRevenueLoss.objects.filter(
                recorded_at__range=[date_from, date_to],
                failure_reason=reason
            )
            
            # 해당 사유의 콜백 성공률
            related_callbacks = CallbackSchedule.objects.filter(
                happy_call__callfailurerevenue_loss__failure_reason=reason,
                created_at__range=[date_from, date_to]
            )
            
            reason_data[reason] = {
                'total_occurrences': reason_losses.count(),
                'total_revenue_loss': reason_losses.aggregate(total=Sum('estimated_revenue_loss'))['total'] or 0,
                'avg_loss_per_occurrence': reason_losses.aggregate(avg=Avg('estimated_revenue_loss'))['avg'] or 0,
                'recovery_rate': (reason_losses.filter(revenue_recovered=True).count() / reason_losses.count() * 100) if reason_losses.count() > 0 else 0,
                'callback_effectiveness': CallFailureAnalysisManager.calculate_callback_effectiveness_by_reason(reason, date_from, date_to)
            }
        
        return reason_data
    
    @staticmethod
    def analyze_revenue_recovery(date_from, date_to):
        """매출 회복 분석"""
        from django.db.models import Sum, Avg, Count
        
        recovery_logs = RevenueRecoveryLog.objects.filter(
            recovery_date__range=[date_from, date_to]
        )
        
        recovery_sources = recovery_logs.values('recovery_source').annotate(
            count=Count('id'),
            total_recovered=Sum('recovered_amount'),
            avg_recovery_rate=Avg('recovery_rate')
        )
        
        return {
            'total_recoveries': recovery_logs.count(),
            'total_recovered_amount': recovery_logs.aggregate(total=Sum('recovered_amount'))['total'] or 0,
            'avg_recovery_rate': recovery_logs.aggregate(avg=Avg('recovery_rate'))['avg'] or 0,
            'recovery_by_source': list(recovery_sources),
            'best_recovery_method': CallFailureAnalysisManager.identify_best_recovery_method(recovery_sources),
            'recovery_timeline': CallFailureAnalysisManager.analyze_recovery_timeline(recovery_logs)
        }
    
    @staticmethod
    def calculate_failure_revenue_correlation():
        """실패율과 매출 손실의 상관관계 계산"""
        from django.db.models import Count, Sum
        import json
        
        # 월별 실패율과 매출 손실 데이터 수집
        monthly_data = []
        
        # 최근 12개월 데이터 분석
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=31)
            
            month_calls = HappyCall.objects.filter(
                created_at__range=[month_start, month_end]
            )
            
            month_failures = month_calls.filter(status='failed')
            month_losses = CallFailureRevenueLoss.objects.filter(
                recorded_at__range=[month_start, month_end]
            )
            
            if month_calls.count() > 0:
                failure_rate = month_failures.count() / month_calls.count() * 100
                total_loss = month_losses.aggregate(total=Sum('estimated_revenue_loss'))['total'] or 0
                
                monthly_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'failure_rate': failure_rate,
                    'revenue_loss': float(total_loss),
                    'total_calls': month_calls.count()
                })
        
        # 상관계수 계산 (간단한 피어슨 상관계수)
        correlation_coefficient = CallFailureAnalysisManager.calculate_pearson_correlation(
            [data['failure_rate'] for data in monthly_data],
            [data['revenue_loss'] for data in monthly_data]
        )
        
        return {
            'monthly_data': monthly_data,
            'correlation_coefficient': correlation_coefficient,
            'correlation_strength': CallFailureAnalysisManager.interpret_correlation_strength(correlation_coefficient),
            'trend_analysis': CallFailureAnalysisManager.analyze_trend(monthly_data)
        }
    
    @staticmethod
    def calculate_pearson_correlation(x_values, y_values):
        """피어슨 상관계수 계산"""
        import math
        
        n = len(x_values)
        if n < 2:
            return 0
        
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_x2 = sum(x*x for x in x_values)
        sum_y2 = sum(y*y for y in y_values)
        sum_xy = sum(x*y for x, y in zip(x_values, y_values))
        
        denominator = math.sqrt((n*sum_x2 - sum_x*sum_x) * (n*sum_y2 - sum_y*sum_y))
        
        if denominator == 0:
            return 0
        
        return (n*sum_xy - sum_x*sum_y) / denominator
    
    @staticmethod
    def interpret_correlation_strength(coefficient):
        """상관계수 강도 해석"""
        abs_coef = abs(coefficient)
        
        if abs_coef >= 0.9:
            strength = "매우 강한"
        elif abs_coef >= 0.7:
            strength = "강한"
        elif abs_coef >= 0.5:
            strength = "중간"
        elif abs_coef >= 0.3:
            strength = "약한"
        else:
            strength = "매우 약한"
        
        direction = "양의" if coefficient > 0 else "음의"
        
        return f"{direction} {strength} 상관관계"
    
    @staticmethod
    def generate_improvement_recommendations(stage_analysis, reason_analysis, recovery_analysis):
        """개선 방안 추천"""
        recommendations = []
        
        # 1. 가장 문제가 되는 단계 식별
        worst_stage = max(stage_analysis.items(), key=lambda x: x[1]['failure_rate'])
        if worst_stage[1]['failure_rate'] > 20:  # 20% 이상 실패율
            recommendations.append({
                'category': 'stage_improvement',
                'priority': 'high',
                'title': f'{worst_stage[0]}차 콜 개선 필요',
                'description': f'{worst_stage[0]}차 콜의 실패율이 {worst_stage[1]["failure_rate"]:.1f}%로 높습니다.',
                'suggested_actions': [
                    '콜 시간대 최적화',
                    '스크립트 개선',
                    '담당자 교육 강화'
                ]
            })
        
        # 2. 주요 실패 사유 개선
        if reason_analysis:
            worst_reason = max(reason_analysis.items(), key=lambda x: x[1]['total_revenue_loss'])
            recommendations.append({
                'category': 'reason_improvement',
                'priority': 'medium',
                'title': f'{worst_reason[0]} 사유 개선',
                'description': f'{worst_reason[0]} 사유로 인한 매출 손실이 {worst_reason[1]["total_revenue_loss"]:,}원입니다.',
                'suggested_actions': CallFailureAnalysisManager.get_reason_specific_actions(worst_reason[0])
            })
        
        # 3. 콜백 전략 개선
        overall_callback_success = sum(stage['callback_success_rate'] for stage in stage_analysis.values()) / len(stage_analysis)
        if overall_callback_success < 60:  # 60% 미만
            recommendations.append({
                'category': 'callback_improvement',
                'priority': 'medium',
                'title': '콜백 전략 개선',
                'description': f'전체 콜백 성공률이 {overall_callback_success:.1f}%로 낮습니다.',
                'suggested_actions': [
                    '콜백 타이밍 조정',
                    '고객 선호 시간대 파악',
                    'SMS 템플릿 개선'
                ]
            })
        
        return recommendations
    
    @staticmethod
    def get_reason_specific_actions(reason):
        """실패 사유별 구체적 개선 방안"""
        action_map = {
            'customer_unavailable': ['통화 가능 시간대 사전 확인', 'SMS 사전 안내', '여러 연락처 확보'],
            'customer_busy': ['짧은 통화 옵션 제공', '콜백 스케줄링', '비업무시간 통화'],
            'technical_issue': ['시스템 점검 강화', 'VoIP 품질 개선', '백업 통화 수단'],
            'customer_refused': ['거부 사유 분석', '서비스 가치 전달 교육', '맞춤형 접근'],
            'staff_unavailable': ['스태프 스케줄 최적화', '교대 근무 체계', '업무량 분산']
        }
        
        return action_map.get(reason, ['해당 사유에 대한 세부 분석 필요', '맞춤형 개선 방안 수립'])
    
    # 기타 helper 메소드들
    @staticmethod
    def calculate_overall_callback_success_rate(callbacks):
        """전체 콜백 성공률 계산"""
        if callbacks.count() == 0:
            return 0
        return (callbacks.filter(status='completed').count() / callbacks.count()) * 100
    
    @staticmethod
    def calculate_stage_recovery_rate(stage, date_from, date_to):
        """단계별 매출 회복률 계산"""
        stage_losses = CallFailureRevenueLoss.objects.filter(
            recorded_at__range=[date_from, date_to],
            failed_stage=stage
        )
        
        if stage_losses.count() == 0:
            return 0
            
        recovered_losses = stage_losses.filter(revenue_recovered=True)
        return (recovered_losses.count() / stage_losses.count()) * 100
    
    @staticmethod
    def calculate_callback_effectiveness_by_reason(reason, date_from, date_to):
        """실패 사유별 콜백 효과 계산"""
        # 해당 실패 사유로 인한 콜백들의 성공률
        reason_callbacks = CallbackSchedule.objects.filter(
            happy_call__callfailurerevenue_loss__failure_reason=reason,
            created_at__range=[date_from, date_to]
        )
        
        if reason_callbacks.count() == 0:
            return 0
            
        successful = reason_callbacks.filter(status='completed').count()
        return (successful / reason_callbacks.count()) * 100
    
    @staticmethod
    def identify_best_recovery_method(recovery_sources):
        """최고의 매출 회복 방법 식별"""
        if not recovery_sources:
            return None
            
        best_method = max(recovery_sources, key=lambda x: x['avg_recovery_rate'])
        return {
            'method': best_method['recovery_source'],
            'avg_recovery_rate': best_method['avg_recovery_rate'],
            'total_recoveries': best_method['count']
        }
    
    @staticmethod
    def analyze_recovery_timeline(recovery_logs):
        """매출 회복 타임라인 분석"""
        if not recovery_logs.exists():
            return {}
        
        # 회복까지 걸리는 평균 시간 등 계산
        timeline_analysis = {}
        # 구현 생략 (복잡한 시간 분석 로직)
        
        return timeline_analysis
    
    @staticmethod
    def analyze_trend(monthly_data):
        """추세 분석"""
        if len(monthly_data) < 3:
            return "데이터 부족"
        
        # 최근 3개월 평균과 이전 3개월 평균 비교
        recent_avg = sum(data['failure_rate'] for data in monthly_data[:3]) / 3
        previous_avg = sum(data['failure_rate'] for data in monthly_data[3:6]) / 3
        
        if recent_avg > previous_avg * 1.1:
            return "악화 추세"
        elif recent_avg < previous_avg * 0.9:
            return "개선 추세"
        else:
            return "유지 추세"