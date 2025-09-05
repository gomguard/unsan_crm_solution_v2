from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone


class Customer(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ('individual', '개인'),
        ('corporate', '법인'),
    ]
    
    CUSTOMER_STATUS_CHOICES = [
        ('temporary', '임시고객'),     # 전화번호만 있는 상태
        ('registered', '정식고객'),   # 정식 등록된 고객
        ('prospect', '잠재고객'),     # 관심있지만 서비스 미이용
        ('inactive', '비활성'),       # 장기 미이용
    ]
    
    MEMBERSHIP_STATUS_CHOICES = [
        ('none', '비회원'),
        ('basic', '일반회원'),
        ('premium', '우수회원'),
        ('vip', 'VIP회원'),
    ]
    
    CONTACT_METHOD_CHOICES = [
        ('sms', 'SMS'),
        ('phone', '전화'),
        ('email', '이메일'),
    ]
    
    CUSTOMER_GRADE_CHOICES = [
        ('A', 'A등급'),
        ('B', 'B등급'),
        ('C', 'C등급'),
        ('D', 'D등급'),
    ]
    
    # 기본 정보
    customer_status = models.CharField(
        max_length=20,
        choices=CUSTOMER_STATUS_CHOICES,
        default='temporary',
        verbose_name='고객상태'
    )
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default='individual',
        verbose_name='고객구분'
    )
    name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name='고객명'
    )
    
    # 연락처 정보 (전화번호는 필수)
    phone_regex = RegexValidator(
        regex=r'^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$',
        message="전화번호는 '010-1234-5678' 형식으로 입력해주세요."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        verbose_name='휴대폰번호'
    )
    email = models.EmailField(blank=True, verbose_name='이메일')
    
    # 주소 정보
    address_main = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='주소'
    )
    address_detail = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='상세주소'
    )
    
    # 법인 정보
    business_number = models.CharField(
        max_length=12,
        blank=True,
        verbose_name='사업자번호'
    )
    company_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='회사명'
    )
    
    # 멤버십 정보
    membership_status = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_STATUS_CHOICES,
        default='none',
        verbose_name='멤버십'
    )
    membership_join_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='멤버십 가입일'
    )
    membership_expire_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='멤버십 만료일'
    )
    membership_points = models.PositiveIntegerField(
        default=0,
        verbose_name='적립포인트'
    )
    
    # 개인정보 및 마케팅/소통 설정
    privacy_consent = models.BooleanField(
        default=False,
        verbose_name='개인정보 처리 동의',
        help_text='필수: 개인정보 수집/이용 동의'
    )
    privacy_consent_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='개인정보 동의일'
    )
    marketing_consent = models.BooleanField(
        default=False,
        verbose_name='마케팅 활용 동의'
    )
    marketing_consent_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='마케팅 동의일'
    )
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        default='sms',
        verbose_name='선호 연락방법'
    )
    do_not_contact = models.BooleanField(
        default=False,
        verbose_name='연락거부'
    )
    do_not_contact_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='연락거부 사유'
    )
    do_not_contact_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='연락거부 설정일'
    )
    is_banned = models.BooleanField(
        default=False,
        verbose_name='금지고객',
        help_text='악성 고객, 서비스 거부 등 금지고객 지정'
    )
    banned_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='금지 사유'
    )
    banned_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='금지 설정일'
    )
    banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='banned_customers',
        verbose_name='금지 설정자'
    )
    
    # 고객 분석 정보
    acquisition_source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='유입경로'
    )
    customer_grade = models.CharField(
        max_length=1,
        choices=CUSTOMER_GRADE_CHOICES,
        blank=True,
        verbose_name='고객등급'
    )
    first_service_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='첫 서비스일'
    )
    last_service_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='마지막 서비스일'
    )
    last_contact_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='마지막 연락일'
    )
    total_service_count = models.PositiveIntegerField(
        default=0,
        verbose_name='총 서비스 횟수'
    )
    total_service_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='총 서비스 금액'
    )
    
    # 메모 및 시스템 정보
    notes = models.TextField(blank=True, verbose_name='메모')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    class Meta:
        verbose_name = '고객'
        verbose_name_plural = '고객들'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['name']),
            models.Index(fields=['customer_status']),
            models.Index(fields=['membership_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.get_display_name()
    
    def get_display_name(self, show_phone=False):
        """표시용 이름 반환"""
        if self.name:
            if show_phone:
                return f"{self.name} ({self.phone})"
            else:
                return self.name
        else:
            # 임시고객의 경우 전화번호 마스킹
            return f"{self.get_masked_phone()}"
    
    def get_masked_phone(self):
        """마스킹된 전화번호 반환 - 가운데 네 자리 마스킹"""
        raw_phone = self._get_raw_phone()
        if len(raw_phone) >= 11:
            # 010-1234-5678 -> 010-****-5678
            return f"{raw_phone[:4]}****{raw_phone[-4:]}"
        elif len(raw_phone) >= 10:
            # 0101234567 -> 010****567
            return f"{raw_phone[:3]}****{raw_phone[-3:]}"
        else:
            return "***-****"
    
    def get_phone_for_user(self, user, show_full=False):
        """사용자 권한에 따른 전화번호 반환"""
        # 관리자이고 명시적으로 전체보기 요청한 경우에만 전체 번호
        if user.is_superuser and show_full:
            return self._get_raw_phone()
        # 그 외 모든 경우는 마스킹
        else:
            return self.get_masked_phone()
    
    def can_view_phone(self, user, show_full=False):
        """전화번호 보기 권한 확인"""
        # 관리자이고 명시적으로 전체보기 요청한 경우에만 가능
        return user.is_superuser and show_full
    
    def get_absolute_url(self):
        return reverse('customers:customer_detail', kwargs={'pk': self.pk})
    
    def get_full_address(self):
        """전체 주소를 반환"""
        address_parts = []
        if self.address_main:
            address_parts.append(self.address_main)
        if self.address_detail:
            address_parts.append(self.address_detail)
        return ' '.join(address_parts) if address_parts else ''
    
    def is_registered_customer(self):
        """정식 등록된 고객인지 확인"""
        return self.customer_status == 'registered'
    
    def is_member(self):
        """멤버십 회원인지 확인"""
        return self.membership_status != 'none'
    
    def get_membership_display_korean(self):
        """멤버십 상태를 한국어로 반환"""
        return dict(self.MEMBERSHIP_STATUS_CHOICES).get(self.membership_status, '비회원')
    
    def can_contact(self):
        """연락 가능 여부 확인"""
        return not (self.do_not_contact or self.is_banned)
    
    def can_provide_service(self):
        """서비스 제공 가능 여부 확인"""
        return not self.is_banned
    
    def has_privacy_consent(self):
        """개인정보 동의 여부 확인"""
        return self.privacy_consent
    
    def ban_customer(self, reason, user):
        """고객 금지 처리"""
        from django.utils import timezone
        self.is_banned = True
        self.banned_reason = reason
        self.banned_date = timezone.now()
        self.banned_by = user
        self.save()
    
    def unban_customer(self):
        """고객 금지 해제"""
        self.is_banned = False
        self.banned_reason = ''
        self.banned_date = None
        self.banned_by = None
        self.save()
    
    def to_dict(self, user=None, show_full_phone=False):
        """안전한 딕셔너리 변환 (전화번호 보호)"""
        from django.forms.models import model_to_dict
        data = model_to_dict(self)
        
        # 전화번호 필드를 안전하게 처리
        if user and hasattr(user, 'is_superuser'):
            data['phone'] = self.get_phone_for_user(user, show_full_phone)
        else:
            data['phone'] = self.get_masked_phone()
        
        return data
    
    def __getattribute__(self, name):
        """속성 접근 시 전화번호 보호"""
        # phone 필드 직접 접근 시 보호
        if name == 'phone':
            # 스택 추적을 통해 호출자 확인
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_function = frame.f_back.f_code.co_name
                caller_class = None
                if 'self' in frame.f_back.f_locals:
                    caller_class = frame.f_back.f_locals['self'].__class__.__name__
                
                # Django 내부 또는 허용된 접근
                allowed_functions = [
                    'get_phone_for_user', 'get_masked_phone', '__init__', 'save', 
                    'clean', 'full_clean', 'validate_unique', '_save_table',
                    'get_prep_value', 'to_python', 'refresh_from_db', 
                    '_get_pk_val', '__setstate__'
                ]
                allowed_classes = [
                    'Customer', 'CharField', 'RegexValidator', 'Model'
                ]
                
                if (caller_class in allowed_classes or 
                    caller_function in allowed_functions or
                    caller_function.startswith('_') or  # Django internal methods
                    'django' in (frame.f_back.f_globals.get('__name__', '') or '')):
                    return super().__getattribute__(name)
                
                # 외부에서의 직접 접근은 마스킹된 값 반환
                return self.get_masked_phone()
            
        return super().__getattribute__(name)
    
    def _get_raw_phone(self):
        """내부용 원본 전화번호 획득 메서드"""
        return super().__getattribute__('phone')
    
    def save(self, *args, **kwargs):
        """저장 시 원본 전화번호 사용"""
        # 저장 시에는 원본 phone 값을 사용해야 함
        return super().save(*args, **kwargs)


class Tag(models.Model):
    """고객 태그 마스터"""
    name = models.CharField(max_length=50, unique=True, verbose_name='태그명')
    color = models.CharField(
        max_length=7,
        default='#6B7280',
        verbose_name='색상',
        help_text='HEX 색상코드 (예: #3B82F6)'
    )
    is_active = models.BooleanField(default=True, verbose_name='사용여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '태그'
        verbose_name_plural = '태그들'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CustomerTag(models.Model):
    """고객-태그 연결"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='customer_tags',
        verbose_name='고객'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='customer_tags',
        verbose_name='태그'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='태그 부여일')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='태그 부여자'
    )
    
    class Meta:
        verbose_name = '고객 태그'
        verbose_name_plural = '고객 태그들'
        unique_together = ['customer', 'tag']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.name} - {self.tag.name}"


class Vehicle(models.Model):
    """차량 마스터"""
    vehicle_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='차량번호'
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='모델명'
    )
    year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='연식'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '차량'
        verbose_name_plural = '차량들'
        ordering = ['vehicle_number']
    
    def __str__(self):
        return f"{self.vehicle_number} {self.model}".strip()
    
    def get_absolute_url(self):
        return reverse('vehicles:vehicle_detail', kwargs={'pk': self.pk})


class CustomerVehicle(models.Model):
    """고객-차량 소유 관계"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='vehicle_ownerships',
        verbose_name='고객'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='ownerships',
        verbose_name='차량'
    )
    start_date = models.DateField(verbose_name='소유 시작일')
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='소유 종료일'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')
    
    class Meta:
        verbose_name = '고객 차량 소유관계'
        verbose_name_plural = '고객 차량 소유관계들'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.customer.name} - {self.vehicle.vehicle_number}"
    
    @property
    def is_current_owner(self):
        """현재 소유중인지 여부"""
        return self.end_date is None


# 소통 이력과 해피콜 분리
class CustomerCommunication(models.Model):
    """고객 소통 이력 (일반 상담, 마케팅, 불만 등)"""
    COMMUNICATION_TYPES = [
        ('consultation', '상담'),
        ('marketing', '마케팅'),
        ('complaint', '불만'),
        ('inquiry', '문의'),
        ('follow_up', '후속연락'),
    ]
    
    METHOD_CHOICES = [
        ('sms', 'SMS'),
        ('phone', '전화'),
        ('email', '이메일'),
        ('visit', '방문'),
    ]
    
    DIRECTION_CHOICES = [
        ('inbound', '고객→업체'),
        ('outbound', '업체→고객'),
    ]
    
    RESULT_CHOICES = [
        ('success', '성공'),
        ('no_answer', '연락안됨'),
        ('refused', '거부'),
        ('failed', '실패'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='communications',
        verbose_name='고객'
    )
    communication_date = models.DateTimeField(verbose_name='소통일시')
    communication_type = models.CharField(
        max_length=20,
        choices=COMMUNICATION_TYPES,
        verbose_name='소통구분'
    )
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        verbose_name='소통방법'
    )
    direction = models.CharField(
        max_length=20,
        choices=DIRECTION_CHOICES,
        verbose_name='방향'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(blank=True, verbose_name='내용')
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        verbose_name='결과'
    )
    follow_up_needed = models.BooleanField(
        default=False,
        verbose_name='후속조치 필요'
    )
    follow_up_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='후속조치 예정일'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='작성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    
    class Meta:
        verbose_name = '고객 소통이력'
        verbose_name_plural = '고객 소통이력들'
        ordering = ['-communication_date']
        indexes = [
            models.Index(fields=['customer', '-communication_date']),
            models.Index(fields=['communication_type', '-communication_date']),
        ]
    
    def __str__(self):
        return f"{self.customer.get_display_name()} - {self.get_communication_type_display()} - {self.title}"


class HappyCall(models.Model):
    """해피콜 전용 테이블"""
    CALL_SEQUENCE_CHOICES = [
        (1, '1차콜'),
        (2, '2차콜'),
        (3, '3차콜'),
    ]
    
    CONTACT_RESULT_CHOICES = [
        ('completed', '연락완료'),
        ('no_answer', '연락안됨'),
        ('refused', '거부'),
        ('wrong_number', '잘못된번호'),
    ]
    
    SATISFACTION_CHOICES = [
        (1, '매우불만'),
        (2, '불만'),
        (3, '보통'),
        (4, '만족'),
        (5, '매우만족'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='happy_calls',
        verbose_name='고객'
    )
    service_record_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='연관 서비스 ID'
    )
    call_sequence = models.PositiveIntegerField(
        choices=CALL_SEQUENCE_CHOICES,
        verbose_name='콜 차수'
    )
    scheduled_date = models.DateTimeField(verbose_name='예정일시')
    completed_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='완료일시'
    )
    contact_result = models.CharField(
        max_length=20,
        choices=CONTACT_RESULT_CHOICES,
        blank=True,
        verbose_name='연락결과'
    )
    satisfaction_score = models.PositiveIntegerField(
        choices=SATISFACTION_CHOICES,
        blank=True,
        null=True,
        verbose_name='만족도'
    )
    complaint_exists = models.BooleanField(
        default=False,
        verbose_name='불만사항 있음'
    )
    complaint_details = models.TextField(
        blank=True,
        verbose_name='불만내용'
    )
    follow_up_service_needed = models.BooleanField(
        default=False,
        verbose_name='추가 서비스 필요'
    )
    next_call_scheduled = models.BooleanField(
        default=False,
        verbose_name='다음 콜 예정'
    )
    notes = models.TextField(blank=True, verbose_name='메모')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='작성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    
    class Meta:
        verbose_name = '해피콜'
        verbose_name_plural = '해피콜들'
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['customer', '-scheduled_date']),
            models.Index(fields=['call_sequence', '-scheduled_date']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.customer.get_display_name()} - {self.get_call_sequence_display()}"
    
    @property
    def is_completed(self):
        return self.completed_date is not None


# 마케팅 캠페인 관리
class MarketingCampaign(models.Model):
    """마케팅 캠페인"""
    CAMPAIGN_TYPES = [
        ('sms', 'SMS'),
        ('email', '이메일'),
        ('dm', 'DM우편'),
        ('phone', '전화마케팅'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '준비중'),
        ('active', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='캠페인명')
    description = models.TextField(blank=True, verbose_name='설명')
    campaign_type = models.CharField(
        max_length=20,
        choices=CAMPAIGN_TYPES,
        verbose_name='캠페인 유형'
    )
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')
    target_criteria = models.TextField(
        blank=True,
        verbose_name='타겟 조건'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='상태'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='생성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '마케팅 캠페인'
        verbose_name_plural = '마케팅 캠페인들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_campaign_type_display()})"


class CustomerCampaignHistory(models.Model):
    """고객별 캠페인 이력"""
    DELIVERY_STATUS_CHOICES = [
        ('sent', '발송완료'),
        ('failed', '발송실패'),
        ('refused', '수신거부'),
    ]
    
    RESPONSE_TYPES = [
        ('interested', '관심표시'),
        ('purchased', '구매'),
        ('refused', '거부'),
        ('no_response', '무반응'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='campaign_history',
        verbose_name='고객'
    )
    campaign = models.ForeignKey(
        MarketingCampaign,
        on_delete=models.CASCADE,
        related_name='customer_history',
        verbose_name='캠페인'
    )
    sent_date = models.DateTimeField(verbose_name='발송일시')
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        verbose_name='발송상태'
    )
    opened_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='오픈일시'
    )
    response_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='반응일시'
    )
    response_type = models.CharField(
        max_length=20,
        choices=RESPONSE_TYPES,
        blank=True,
        verbose_name='반응유형'
    )
    roi_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='매출발생액'
    )
    notes = models.TextField(blank=True, verbose_name='메모')
    
    class Meta:
        verbose_name = '캠페인 이력'
        verbose_name_plural = '캠페인 이력들'
        ordering = ['-sent_date']
        unique_together = ['customer', 'campaign']
    
    def __str__(self):
        return f"{self.customer.get_display_name()} - {self.campaign.name}"


# 멤버십 포인트 관리
class CustomerPointHistory(models.Model):
    """고객 포인트 적립/사용 이력"""
    POINT_TYPES = [
        ('earned', '적립'),
        ('used', '사용'),
        ('expired', '만료'),
        ('adjusted', '조정'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='point_history',
        verbose_name='고객'
    )
    transaction_date = models.DateTimeField(verbose_name='거래일시')
    point_type = models.CharField(
        max_length=20,
        choices=POINT_TYPES,
        verbose_name='포인트 구분'
    )
    points = models.IntegerField(verbose_name='포인트')  # +적립, -사용
    reason = models.CharField(max_length=200, verbose_name='사유')
    related_service_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='연관 서비스 ID'
    )
    balance_after = models.PositiveIntegerField(verbose_name='거래 후 잔액')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='처리자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='처리일')
    
    class Meta:
        verbose_name = '포인트 이력'
        verbose_name_plural = '포인트 이력들'
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.customer.get_display_name()} - {self.points}P ({self.get_point_type_display()})"
