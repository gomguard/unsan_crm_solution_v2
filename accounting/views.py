from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    AccountingCategory, Supplier, PurchaseVoucher, PurchaseVoucherItem,
    SalesVoucher, SalesVoucherItem, JournalEntry, JournalEntryLine
)

class AccountingDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounting/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 이번 달 매입/매출 요약
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        
        # 디버그 로그
        print(f"Debug - Today: {today}")
        print(f"Debug - Current month start: {current_month_start}")
        
        current_month_purchases = PurchaseVoucher.objects.filter(
            purchase_date__gte=current_month_start
        )
        print(f"Debug - Purchase vouchers count: {current_month_purchases.count()}")
        
        context['current_month_purchases'] = current_month_purchases.aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
            unpaid_total=Sum('total_amount', filter=Q(is_paid=False))
        )
        print(f"Debug - Purchases aggregate: {context['current_month_purchases']}")
        
        current_month_sales = SalesVoucher.objects.filter(
            sales_date__gte=current_month_start
        )
        print(f"Debug - Sales vouchers count: {current_month_sales.count()}")
        
        context['current_month_sales'] = current_month_sales.aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
            unreceived_total=Sum('total_amount', filter=Q(is_received=False))
        )
        print(f"Debug - Sales aggregate: {context['current_month_sales']}")
        
        # 최근 전표들
        context['recent_purchases'] = PurchaseVoucher.objects.select_related('supplier').order_by('-created_at')[:5]
        context['recent_sales'] = SalesVoucher.objects.order_by('-created_at')[:5]
        
        # 이번 달 순이익 계산
        sales_total = context['current_month_sales']['total'] or 0
        purchase_total = context['current_month_purchases']['total'] or 0
        context['current_month_profit'] = sales_total - purchase_total
        
        print(f"Debug - Sales total: {sales_total}, Purchase total: {purchase_total}, Profit: {context['current_month_profit']}")
        
        return context

class PurchaseVoucherListView(LoginRequiredMixin, ListView):
    model = PurchaseVoucher
    template_name = 'accounting/purchase_list.html'
    context_object_name = 'vouchers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PurchaseVoucher.objects.select_related('supplier', 'created_by').order_by('-purchase_date')
        
        # 검색 필터
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(voucher_number__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # 결제 상태 필터
        payment_status = self.request.GET.get('payment_status')
        if payment_status == 'paid':
            queryset = queryset.filter(is_paid=True)
        elif payment_status == 'unpaid':
            queryset = queryset.filter(is_paid=False)
            
        return queryset

class PurchaseVoucherCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseVoucher
    template_name = 'accounting/purchase_form.html'
    fields = ['supplier', 'purchase_date', 'description', 'payment_method', 'payment_date']
    success_url = reverse_lazy('accounting:purchase_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class PurchaseVoucherDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseVoucher
    template_name = 'accounting/purchase_detail.html'
    context_object_name = 'voucher'

class PurchaseVoucherUpdateView(LoginRequiredMixin, UpdateView):
    model = PurchaseVoucher
    template_name = 'accounting/purchase_form.html'
    fields = ['supplier', 'purchase_date', 'description', 'payment_method', 'payment_date', 'is_paid']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['purchase_items'] = self.object.items.all()
        return context
    
    def get_success_url(self):
        return reverse_lazy('accounting:purchase_edit', kwargs={'pk': self.object.pk})

class SalesVoucherListView(LoginRequiredMixin, ListView):
    model = SalesVoucher
    template_name = 'accounting/sales_list.html'
    context_object_name = 'vouchers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SalesVoucher.objects.select_related('created_by', 'service_request__customer').order_by('-sales_date')
        
        # 검색 필터
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(voucher_number__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # 결제 상태 필터
        payment_status = self.request.GET.get('payment_status')
        if payment_status == 'received':
            queryset = queryset.filter(is_received=True)
        elif payment_status == 'unreceived':
            queryset = queryset.filter(is_received=False)
            
        return queryset

class SalesVoucherCreateView(LoginRequiredMixin, CreateView):
    model = SalesVoucher
    template_name = 'accounting/sales_form.html'
    fields = ['customer_name', 'customer_phone', 'sales_date', 'description', 'payment_method', 'payment_date', 'service_request']
    success_url = reverse_lazy('accounting:sales_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class SalesVoucherDetailView(LoginRequiredMixin, DetailView):
    model = SalesVoucher
    template_name = 'accounting/sales_detail.html'
    context_object_name = 'voucher'

class SalesVoucherUpdateView(LoginRequiredMixin, UpdateView):
    model = SalesVoucher
    template_name = 'accounting/sales_form.html'
    fields = ['customer_name', 'customer_phone', 'sales_date', 'description', 'payment_method', 'payment_date', 'is_received']
    
    def get_success_url(self):
        return reverse_lazy('accounting:sales_detail', kwargs={'pk': self.object.pk})

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'accounting/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Supplier.objects.filter(is_active=True).order_by('name')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(business_number__icontains=search) |
                Q(representative__icontains=search)
            )
        return queryset

class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    template_name = 'accounting/supplier_form.html'
    fields = ['name', 'business_number', 'representative', 'phone', 'email', 'address', 'bank_account', 'bank_name', 'notes']
    success_url = reverse_lazy('accounting:supplier_list')

class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'accounting/supplier_detail.html'
    context_object_name = 'supplier'

class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    template_name = 'accounting/supplier_form.html'
    fields = ['name', 'business_number', 'representative', 'phone', 'email', 'address', 'bank_account', 'bank_name', 'notes', 'is_active']
    
    def get_success_url(self):
        return reverse_lazy('accounting:supplier_detail', kwargs={'pk': self.object.pk})

class IncomeStatementView(LoginRequiredMixin, TemplateView):
    template_name = 'accounting/income_statement.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 기간 설정 (기본값: 이번 년도)
        year = int(self.request.GET.get('year', timezone.now().year))
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        
        # 매출액 (수익)
        revenue_accounts = AccountingCategory.objects.filter(category_type='revenue')
        total_revenue = SalesVoucher.objects.filter(
            sales_date__range=[start_date, end_date]
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # 매출원가 및 비용
        expense_accounts = AccountingCategory.objects.filter(category_type='expense')
        total_expenses = PurchaseVoucher.objects.filter(
            purchase_date__range=[start_date, end_date]
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # 순이익 계산
        net_income = total_revenue - total_expenses
        
        # 월별 추이 데이터
        monthly_data = []
        for month in range(1, 13):
            month_start = datetime(year, month, 1).date()
            if month == 12:
                month_end = datetime(year, 12, 31).date()
            else:
                month_end = (datetime(year, month + 1, 1) - timedelta(days=1)).date()
            
            month_revenue = SalesVoucher.objects.filter(
                sales_date__range=[month_start, month_end]
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            month_expenses = PurchaseVoucher.objects.filter(
                purchase_date__range=[month_start, month_end]
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            monthly_data.append({
                'month': month,
                'month_name': f'{month}월',
                'revenue': month_revenue,
                'expenses': month_expenses,
                'profit': month_revenue - month_expenses
            })
        
        context.update({
            'year': year,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': net_income,
            'monthly_data': monthly_data,
        })
        
        return context

class BalanceSheetView(LoginRequiredMixin, TemplateView):
    template_name = 'accounting/balance_sheet.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 기준일 설정 (기본값: 오늘)
        as_of_date = self.request.GET.get('date', timezone.now().date())
        if isinstance(as_of_date, str):
            as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
        
        # 자산 계산
        asset_accounts = AccountingCategory.objects.filter(category_type='asset')
        # 간단한 자산 계산 (실제로는 분개장에서 계산해야 함)
        total_assets = 0  # 실제 구현 시 분개장 기반으로 계산
        
        # 부채 계산
        liability_accounts = AccountingCategory.objects.filter(category_type='liability')
        total_liabilities = PurchaseVoucher.objects.filter(
            purchase_date__lte=as_of_date,
            is_paid=False
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # 자본 계산
        equity_accounts = AccountingCategory.objects.filter(category_type='equity')
        total_equity = 0  # 실제 구현 시 분개장 기반으로 계산
        
        # 미수금 (매출전표 중 미수)
        accounts_receivable = SalesVoucher.objects.filter(
            sales_date__lte=as_of_date,
            is_received=False
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        context.update({
            'as_of_date': as_of_date,
            'accounts_receivable': accounts_receivable,
            'total_assets': accounts_receivable,  # 간단히 미수금만 자산으로 계산
            'total_liabilities': total_liabilities,
            'total_equity': accounts_receivable - total_liabilities,  # 자산 - 부채
        })
        
        return context

class AccountingCategoryListView(LoginRequiredMixin, ListView):
    model = AccountingCategory
    template_name = 'accounting/account_list.html'
    context_object_name = 'accounts'
    
    def get_queryset(self):
        return AccountingCategory.objects.filter(is_active=True).order_by('code')

class AccountingCategoryCreateView(LoginRequiredMixin, CreateView):
    model = AccountingCategory
    template_name = 'accounting/account_form.html'
    fields = ['code', 'name', 'category_type', 'parent', 'description']
    success_url = reverse_lazy('accounting:account_list')


# ===================== 해피콜 매출전표 연동 뷰들 =====================

class HappyCallSalesVoucherCreateView(LoginRequiredMixin, CreateView):
    """해피콜 매출 기록 기반 매출전표 생성"""
    model = SalesVoucher
    template_name = 'accounting/happycall_sales_voucher_form.html'
    fields = [
        'sales_date', 'customer_name', 'customer_phone', 
        'total_amount', 'tax_amount', 'description',
        'payment_method', 'payment_date', 'is_received'
    ]
    
    def dispatch(self, request, *args, **kwargs):
        # HappyCallRevenue 객체 확인
        from happycall.models import HappyCallRevenue
        self.revenue_record = get_object_or_404(
            HappyCallRevenue, 
            id=kwargs['revenue_id'],
            status__in=['accepted', 'proposed']
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """해피콜 매출 기록으로부터 초기값 설정"""
        initial = super().get_initial()
        
        # 해피콜 매출 기록에서 매출전표 기본값 가져오기
        voucher_data = self.revenue_record.create_sales_voucher_data()
        initial.update(voucher_data)
        initial['sales_date'] = timezone.now().date()
        
        return initial
    
    def form_valid(self, form):
        # 해피콜 연동 필드 설정
        form.instance.happy_call_revenue = self.revenue_record
        form.instance.revenue_source = f'happy_call_{self.revenue_record.call_stage}'
        form.instance.created_by = self.request.user
        
        # 서비스 요청과도 연결
        form.instance.service_request = self.revenue_record.happy_call.service_request
        
        response = super().form_valid(form)
        
        # HappyCallRevenue 상태 업데이트
        self.revenue_record.sales_voucher = self.object
        self.revenue_record.actual_amount = self.object.total_amount
        self.revenue_record.status = 'voucher_created'
        self.revenue_record.save()
        
        # 해피콜 매출 통계 업데이트
        self.revenue_record.happy_call.update_revenue_stats()
        
        from django.contrib import messages
        messages.success(
            self.request,
            f'해피콜 매출전표가 생성되었습니다. (전표번호: {self.object.voucher_number})'
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['revenue_record'] = self.revenue_record
        context['happy_call'] = self.revenue_record.happy_call
        context['customer'] = self.revenue_record.happy_call.service_request.customer
        return context
    
    def get_success_url(self):
        return reverse_lazy('accounting:sales_detail', kwargs={'pk': self.object.pk})


def complete_happycall_revenue(request, voucher_id):
    """매출전표 입금 완료 시 해피콜 매출 기록도 완료 처리"""
    voucher = get_object_or_404(SalesVoucher, pk=voucher_id)
    
    if voucher.happy_call_revenue and not voucher.is_received:
        voucher.is_received = True
        voucher.payment_date = timezone.now().date()
        voucher.save()
        
        # 해피콜 매출 기록 완료 처리
        voucher.complete_happy_call_revenue()
        
        from django.contrib import messages
        messages.success(request, '입금 처리 및 해피콜 매출 기록이 완료되었습니다.')
    
    return redirect('accounting:sales_detail', pk=voucher_id)


class HappyCallRevenueAnalysisView(LoginRequiredMixin, TemplateView):
    """해피콜 매출 분석 대시보드"""
    template_name = 'accounting/happycall_revenue_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 날짜 범위 설정
        today = timezone.now().date()
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if not start_date:
            start_date = today.replace(day=1)  # 이번 달 시작
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
        if not end_date:
            end_date = today
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 해피콜 기원 매출전표 필터링
        happycall_vouchers = SalesVoucher.objects.filter(
            revenue_source__startswith='happy_call_',
            sales_date__range=[start_date, end_date]
        ).select_related('happy_call_revenue__happy_call')
        
        # 전체 매출 vs 해피콜 매출 비교
        total_sales = SalesVoucher.objects.filter(
            sales_date__range=[start_date, end_date]
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        happycall_sales = happycall_vouchers.aggregate(
            total=Sum('total_amount'))['total'] or 0
        
        happycall_percentage = (happycall_sales / total_sales * 100) if total_sales > 0 else 0
        
        # 콜 단계별 매출 분석
        stage_analysis = happycall_vouchers.values('revenue_source').annotate(
            total_amount=Sum('total_amount'),
            count=Count('id'),
            avg_amount=Avg('total_amount')
        ).order_by('revenue_source')
        
        # 매출 유형별 분석 (HappyCallRevenue를 통해)
        from happycall.models import HappyCallRevenue
        revenue_type_analysis = HappyCallRevenue.objects.filter(
            proposed_at__date__range=[start_date, end_date],
            status='completed'
        ).values('revenue_type').annotate(
            total_amount=Sum('actual_amount'),
            count=Count('id'),
            avg_amount=Avg('actual_amount')
        ).order_by('-total_amount')
        
        # 월별 추세 (최근 12개월)
        from dateutil.relativedelta import relativedelta
        monthly_trends = []
        current_date = end_date.replace(day=1)
        
        for i in range(12):
            month_start = current_date - relativedelta(months=i)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
            
            month_sales = SalesVoucher.objects.filter(
                revenue_source__startswith='happy_call_',
                sales_date__range=[month_start, month_end]
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            monthly_trends.insert(0, {
                'month': month_start.strftime('%Y-%m'),
                'amount': month_sales
            })
        
        # 상위 해피콜 성과자 (매출 기준)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        top_performers = HappyCallRevenue.objects.filter(
            proposed_at__date__range=[start_date, end_date],
            status='completed'
        ).values('proposed_by__username').annotate(
            total_revenue=Sum('actual_amount'),
            call_count=Count('id'),
            avg_revenue=Avg('actual_amount')
        ).order_by('-total_revenue')[:10]
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'total_sales': total_sales,
            'happycall_sales': happycall_sales,
            'happycall_percentage': round(happycall_percentage, 2),
            'happycall_voucher_count': happycall_vouchers.count(),
            'stage_analysis': stage_analysis,
            'revenue_type_analysis': revenue_type_analysis,
            'monthly_trends': monthly_trends,
            'top_performers': top_performers,
        })
        
        return context


def ajax_happycall_revenue_stats(request):
    """해피콜 매출 통계 AJAX 응답"""
    if not request.user.is_authenticated:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # 기간 파라미터
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # 해피콜 매출 집계
    from happycall.models import HappyCallRevenue
    
    revenues = HappyCallRevenue.objects.filter(
        proposed_at__date__range=[start_date, end_date]
    )
    
    # 상태별 집계
    status_stats = revenues.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('actual_amount')
    )
    
    # 일별 추세
    daily_stats = []
    current_date = start_date
    while current_date <= end_date:
        day_revenues = revenues.filter(proposed_at__date=current_date)
        daily_stats.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': day_revenues.count(),
            'amount': day_revenues.aggregate(total=Sum('actual_amount'))['total'] or 0
        })
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'status_stats': list(status_stats),
        'daily_stats': daily_stats,
        'total_revenue': revenues.filter(status='completed').aggregate(
            total=Sum('actual_amount'))['total'] or 0,
        'total_count': revenues.count()
    })
