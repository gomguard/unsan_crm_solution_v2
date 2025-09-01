from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Customer


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Customer.objects.filter(is_active=True)
        
        # 검색 기능
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(company_name__icontains=search_query)
            )
        
        # 고객 구분 필터
        customer_type = self.request.GET.get('customer_type')
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)
        
        # VIP 레벨 필터
        vip_level = self.request.GET.get('vip_level')
        if vip_level:
            queryset = queryset.filter(vip_level=vip_level)
        
        # 성별 필터
        gender = self.request.GET.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
        
        # 정렬
        ordering = self.request.GET.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('search', ''),
            'customer_type_filter': self.request.GET.get('customer_type', ''),
            'vip_level_filter': self.request.GET.get('vip_level', ''),
            'gender_filter': self.request.GET.get('gender', ''),
            'ordering': self.request.GET.get('ordering', '-created_at'),
            'total_customers': Customer.objects.filter(is_active=True).count(),
            'vip_customers': Customer.objects.filter(is_active=True, vip_level__gt=0).count(),
            'corporate_customers': Customer.objects.filter(is_active=True, customer_type='corporate').count(),
        })
        return context


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        
        # 관련 차량 정보 (추후 구현)
        # context['vehicles'] = customer.vehicles.all()
        
        # 서비스 이력 (추후 구현)
        # context['service_history'] = customer.service_records.all()[:10]
        
        # 해피콜 이력 (추후 구현)
        # context['happycall_history'] = customer.happycalls.all()[:5]
        
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    template_name = 'customers/customer_form.html'
    fields = [
        'customer_type', 'name', 'gender', 'birth_date',
        'phone', 'phone_secondary', 'email',
        'address_postal_code', 'address_main', 'address_detail',
        'business_number', 'company_name',
        'vip_level', 'notes'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, f'{form.instance.name} 고객이 성공적으로 등록되었습니다.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '고객 등록'
        context['form_action'] = 'create'
        return context


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    template_name = 'customers/customer_form.html'
    fields = [
        'customer_type', 'name', 'gender', 'birth_date',
        'phone', 'phone_secondary', 'email',
        'address_postal_code', 'address_main', 'address_detail',
        'business_number', 'company_name',
        'vip_level', 'notes'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, f'{form.instance.name} 고객 정보가 성공적으로 수정되었습니다.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '고객 정보 수정'
        context['form_action'] = 'edit'
        return context


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customers:customer_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # 실제로는 삭제하지 않고 비활성화
        self.object.is_active = False
        self.object.save()
        
        messages.success(request, f'{self.object.name} 고객이 비활성화되었습니다.')
        return HttpResponseRedirect(success_url)


@login_required
def customer_search(request):
    """AJAX 고객 검색"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'customers': []})
    
    customers = Customer.objects.filter(
        Q(name__icontains=query) |
        Q(phone__icontains=query),
        is_active=True
    )[:10]
    
    customer_data = []
    for customer in customers:
        customer_data.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'customer_type': customer.get_customer_type_display(),
            'vip_level': customer.get_vip_level_display_korean(),
            'url': customer.get_absolute_url(),
        })
    
    return JsonResponse({'customers': customer_data})


@login_required
def toggle_customer_active(request, pk):
    """고객 활성화/비활성화 토글"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.is_active = not customer.is_active
        customer.save()
        
        status = '활성화' if customer.is_active else '비활성화'
        messages.success(request, f'{customer.name} 고객이 {status}되었습니다.')
    
    return redirect('customers:customer_detail', pk=pk)
