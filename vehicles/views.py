from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from customers.models import Vehicle, CustomerVehicle, Customer

@login_required
def vehicle_list(request):
    """차량 목록"""
    # 검색 기능
    search_query = request.GET.get('search', '').strip()
    vehicle_type_filter = request.GET.get('vehicle_type', 'all')
    owner_filter = request.GET.get('owner', 'all')
    page = request.GET.get('page', 1)
    
    # 차량 기본 쿼리셋
    vehicles = Vehicle.objects.select_related().prefetch_related('ownerships__customer').all()
    
    # 검색 조건 적용
    if search_query:
        vehicles = vehicles.filter(
            Q(vehicle_number__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(ownerships__customer__name__icontains=search_query)
        ).distinct()
    
    # 소유자 필터
    if owner_filter == 'with_owner':
        vehicles = vehicles.filter(ownerships__end_date__isnull=True)
    elif owner_filter == 'without_owner':
        vehicles = vehicles.filter(ownerships__isnull=True)
    
    # 정렬
    vehicles = vehicles.order_by('-created_at')
    
    # 통계 계산
    total_vehicles = Vehicle.objects.count()
    vehicles_with_owners = Vehicle.objects.filter(ownerships__end_date__isnull=True).distinct().count()
    vehicles_without_owners = total_vehicles - vehicles_with_owners
    
    # 페이지네이션
    paginator = Paginator(vehicles, 20)  # 한 페이지에 20개씩
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    context = {
        'vehicles': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'search_query': search_query,
        'vehicle_type_filter': vehicle_type_filter,
        'owner_filter': owner_filter,
        'total_vehicles': total_vehicles,
        'vehicles_with_owners': vehicles_with_owners,
        'vehicles_without_owners': vehicles_without_owners,
    }
    
    return render(request, 'vehicles/vehicle_list.html', context)

@login_required
def vehicle_detail(request, pk):
    """차량 상세"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    # 현재 소유자
    current_ownership = vehicle.ownerships.filter(end_date__isnull=True).first()
    
    # 소유 이력
    ownership_history = vehicle.ownerships.all().order_by('-start_date')
    
    # 서비스 이력 (서비스 요청과 연결된 것들)
    service_history = []
    try:
        from services.models import ServiceRequest
        service_history = ServiceRequest.objects.filter(vehicle=vehicle).order_by('-created_at')[:10]
    except:
        pass
    
    context = {
        'vehicle': vehicle,
        'current_ownership': current_ownership,
        'ownership_history': ownership_history,
        'service_history': service_history,
    }
    
    return render(request, 'vehicles/vehicle_detail.html', context)
