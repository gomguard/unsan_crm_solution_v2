from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class AccountingCategory(models.Model):
    """회계 계정과목"""
    CATEGORY_TYPES = [
        ('asset', '자산'),
        ('liability', '부채'),
        ('equity', '자본'),
        ('revenue', '수익'),
        ('expense', '비용'),
    ]
    
    code = models.CharField('계정코드', max_length=10, unique=True)
    name = models.CharField('계정명', max_length=100)
    category_type = models.CharField('계정구분', max_length=10, choices=CATEGORY_TYPES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='상위계정')
    is_active = models.BooleanField('사용여부', default=True)
    description = models.TextField('설명', blank=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    
    class Meta:
        verbose_name = '계정과목'
        verbose_name_plural = '계정과목들'
        ordering = ['code']
    
    def __str__(self):
        return f"[{self.code}] {self.name}"

class Supplier(models.Model):
    """공급업체 (매입처)"""
    name = models.CharField('업체명', max_length=100)
    business_number = models.CharField('사업자번호', max_length=12, unique=True, null=True, blank=True)
    representative = models.CharField('대표자명', max_length=50, blank=True)
    phone = models.CharField('전화번호', max_length=20, blank=True)
    email = models.EmailField('이메일', blank=True)
    address = models.TextField('주소', blank=True)
    bank_account = models.CharField('계좌번호', max_length=50, blank=True)
    bank_name = models.CharField('은행명', max_length=50, blank=True)
    is_active = models.BooleanField('활성상태', default=True)
    notes = models.TextField('비고', blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '공급업체'
        verbose_name_plural = '공급업체들'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class PurchaseVoucher(models.Model):
    """매입전표"""
    voucher_number = models.CharField('전표번호', max_length=20, unique=True)
    purchase_date = models.DateField('매입일자')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name='공급업체')
    total_amount = models.DecimalField('총금액', max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField('부가세', max_digits=12, decimal_places=0, default=0)
    description = models.CharField('적요', max_length=200, blank=True)
    
    # 결제 정보
    payment_method = models.CharField('결제방법', max_length=20, choices=[
        ('cash', '현금'),
        ('card', '카드'),
        ('transfer', '계좌이체'),
        ('check', '수표'),
        ('credit', '외상'),
    ], default='transfer')
    payment_date = models.DateField('결제일자', null=True, blank=True)
    is_paid = models.BooleanField('결제완료', default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='등록자')
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '매입전표'
        verbose_name_plural = '매입전표들'
        ordering = ['-purchase_date', '-created_at']
    
    def __str__(self):
        return f"{self.voucher_number} - {self.supplier.name} ({self.total_amount:,}원)"
    
    def save(self, *args, **kwargs):
        if not self.voucher_number:
            # 전표번호 자동 생성: P240315001 (P+YYMMDD+순번)
            today = timezone.now().date()
            date_str = today.strftime('%y%m%d')
            last_voucher = PurchaseVoucher.objects.filter(
                voucher_number__startswith=f'P{date_str}'
            ).order_by('voucher_number').last()
            
            if last_voucher:
                last_number = int(last_voucher.voucher_number[-3:])
                new_number = f'P{date_str}{(last_number + 1):03d}'
            else:
                new_number = f'P{date_str}001'
            
            self.voucher_number = new_number
        
        super().save(*args, **kwargs)

class PurchaseVoucherItem(models.Model):
    """매입전표 상세항목"""
    voucher = models.ForeignKey(PurchaseVoucher, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField('품목명', max_length=100)
    specification = models.CharField('규격', max_length=100, blank=True)
    quantity = models.DecimalField('수량', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField('단위', max_length=10, default='개')
    unit_price = models.DecimalField('단가', max_digits=10, decimal_places=0, validators=[MinValueValidator(0)])
    amount = models.DecimalField('금액', max_digits=12, decimal_places=0)
    account = models.ForeignKey(AccountingCategory, on_delete=models.CASCADE, verbose_name='계정과목', null=True, blank=True)
    
    class Meta:
        verbose_name = '매입전표 항목'
        verbose_name_plural = '매입전표 항목들'
    
    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class SalesVoucher(models.Model):
    """매출전표"""
    voucher_number = models.CharField('전표번호', max_length=20, unique=True)
    sales_date = models.DateField('매출일자')
    customer_name = models.CharField('고객명', max_length=100)
    customer_phone = models.CharField('연락처', max_length=20, blank=True)
    total_amount = models.DecimalField('총금액', max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField('부가세', max_digits=12, decimal_places=0, default=0)
    description = models.CharField('적요', max_length=200, blank=True)
    
    # 결제 정보
    payment_method = models.CharField('결제방법', max_length=20, choices=[
        ('cash', '현금'),
        ('card', '카드'),
        ('transfer', '계좌이체'),
        ('check', '수표'),
        ('credit', '외상'),
    ], default='card')
    payment_date = models.DateField('입금일자', null=True, blank=True)
    is_received = models.BooleanField('입금완료', default=False)
    
    # 서비스 연결
    service_request = models.ForeignKey('services.ServiceRequest', on_delete=models.SET_NULL, 
                                      null=True, blank=True, verbose_name='서비스 요청')
    
    # 해피콜 연동 필드 추가
    happy_call_revenue = models.OneToOneField('happycall.HappyCallRevenue', 
                                            on_delete=models.SET_NULL, null=True, blank=True,
                                            verbose_name='해피콜 매출 기록')
    revenue_source = models.CharField('매출 출처', max_length=30, choices=[
        ('direct', '직접 서비스'),
        ('happy_call_1st', '1차 해피콜'),
        ('happy_call_2nd', '2차 해피콜'),
        ('happy_call_3rd', '3차 해피콜'),
        ('happy_call_4th', '4차 해피콜'),
        ('other', '기타'),
    ], default='direct')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='등록자')
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '매출전표'
        verbose_name_plural = '매출전표들'
        ordering = ['-sales_date', '-created_at']
    
    def __str__(self):
        return f"{self.voucher_number} - {self.customer_name} ({self.total_amount:,}원)"
    
    def save(self, *args, **kwargs):
        if not self.voucher_number:
            # 전표번호 자동 생성: S240315001 (S+YYMMDD+순번)
            today = timezone.now().date()
            date_str = today.strftime('%y%m%d')
            last_voucher = SalesVoucher.objects.filter(
                voucher_number__startswith=f'S{date_str}'
            ).order_by('voucher_number').last()
            
            if last_voucher:
                last_number = int(last_voucher.voucher_number[-3:])
                new_number = f'S{date_str}{(last_number + 1):03d}'
            else:
                new_number = f'S{date_str}001'
            
            self.voucher_number = new_number
        
        super().save(*args, **kwargs)
        
        # 해피콜 매출 기록과 연동 처리
        if self.happy_call_revenue and self.happy_call_revenue.status != 'completed':
            self.happy_call_revenue.actual_amount = self.total_amount
            self.happy_call_revenue.status = 'voucher_created'
            self.happy_call_revenue.save()
    
    def complete_happy_call_revenue(self):
        """해피콜 매출 기록을 완료로 처리"""
        if self.happy_call_revenue:
            self.happy_call_revenue.mark_as_completed()
    
    @property
    def is_from_happy_call(self):
        """해피콜 기원 매출전표인지 확인"""
        return self.revenue_source.startswith('happy_call_')
    
    @property
    def happy_call_stage(self):
        """해피콜 단계 반환 (1st, 2nd, 3rd, 4th)"""
        if self.is_from_happy_call:
            return self.revenue_source.replace('happy_call_', '')
        return None

class SalesVoucherItem(models.Model):
    """매출전표 상세항목"""
    voucher = models.ForeignKey(SalesVoucher, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField('품목명', max_length=100)
    specification = models.CharField('규격', max_length=100, blank=True)
    quantity = models.DecimalField('수량', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField('단위', max_length=10, default='건')
    unit_price = models.DecimalField('단가', max_digits=10, decimal_places=0, validators=[MinValueValidator(0)])
    amount = models.DecimalField('금액', max_digits=12, decimal_places=0)
    account = models.ForeignKey(AccountingCategory, on_delete=models.CASCADE, verbose_name='계정과목', null=True, blank=True)
    
    class Meta:
        verbose_name = '매출전표 항목'
        verbose_name_plural = '매출전표 항목들'
    
    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class JournalEntry(models.Model):
    """분개장"""
    entry_number = models.CharField('분개번호', max_length=20, unique=True)
    entry_date = models.DateField('분개일자')
    description = models.CharField('적요', max_length=200)
    
    # 연결 정보
    purchase_voucher = models.ForeignKey(PurchaseVoucher, on_delete=models.CASCADE, 
                                       null=True, blank=True, verbose_name='매입전표')
    sales_voucher = models.ForeignKey(SalesVoucher, on_delete=models.CASCADE, 
                                    null=True, blank=True, verbose_name='매출전표')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='등록자')
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    
    class Meta:
        verbose_name = '분개장'
        verbose_name_plural = '분개장들'
        ordering = ['-entry_date', '-created_at']
    
    def __str__(self):
        return f"{self.entry_number} - {self.description}"

class JournalEntryLine(models.Model):
    """분개장 세부항목"""
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(AccountingCategory, on_delete=models.CASCADE, verbose_name='계정과목')
    debit_amount = models.DecimalField('차변금액', max_digits=12, decimal_places=0, default=0)
    credit_amount = models.DecimalField('대변금액', max_digits=12, decimal_places=0, default=0)
    description = models.CharField('적요', max_length=100, blank=True)
    
    class Meta:
        verbose_name = '분개 세부항목'
        verbose_name_plural = '분개 세부항목들'