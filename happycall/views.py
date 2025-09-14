from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Max, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
from customers.models import Customer, CustomerVehicle
from services.models import ServiceRequest
from employees.models import Employee
from .models import HappyCall, HappyCallRevenue

@login_required
def my_happycalls(request):
    """내 할일 - 현재 사용자에게 배정된 진행중/대기중 해피콜들"""
    # 기본 쿼리: 현재 사용자가 담당하는 진행중/대기중 해피콜들만
    happycalls = HappyCall.objects.select_related(
        'service_request__customer',
        'service_request__service_type',
        'first_call_caller',
        'second_call_caller',
        'third_call_caller',
        'fourth_call_caller'
    ).filter(
        Q(first_call_caller=request.user) |
        Q(second_call_caller=request.user) |
        Q(third_call_caller=request.user) |
        Q(fourth_call_caller=request.user)
    ).filter(
        # 진행중이거나 대기중인 것만
        Q(call_stage__endswith='_pending') |
        Q(call_stage__endswith='_in_progress')
    )
    
    # 우선순위별 정렬 (1차 -> 2차 -> 3차 -> 4차 순)
    happycalls = happycalls.order_by('call_stage', '-created_at')
    
    # 페이지네이션
    paginator = Paginator(happycalls, 20)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    return render(request, 'happycall/my_happycalls.html', {
        'happycalls': page_obj,
        'page_obj': page_obj,
        'page_title': '내 할일',
    })

@login_required
def happycall_list(request):
    """전체 해피콜 목록 (이력 포함)"""
    # 필터 파라미터
    search = request.GET.get('search', '')
    stage = request.GET.get('stage', '')
    status = request.GET.get('status', '')
    
    # 기본 쿼리: 모든 해피콜
    happycalls = HappyCall.objects.select_related(
        'service_request__customer',
        'service_request__service_type',
        'first_call_caller',
        'second_call_caller',
        'third_call_caller',
        'fourth_call_caller'
    )
    
    # 관리자가 아니면 자신이 담당한 것만
    if not request.user.is_superuser:
        happycalls = happycalls.filter(
            Q(first_call_caller=request.user) |
            Q(second_call_caller=request.user) |
            Q(third_call_caller=request.user) |
            Q(fourth_call_caller=request.user)
        )
    
    # 검색 필터
    if search:
        happycalls = happycalls.filter(
            Q(service_request__customer__name__icontains=search) |
            Q(service_request__customer__phone__icontains=search) |
            Q(first_call_notes__icontains=search) |
            Q(second_call_notes__icontains=search) |
            Q(third_call_notes__icontains=search) |
            Q(fourth_call_notes__icontains=search)
        )
    
    # 콜 단계 필터
    if stage:
        happycalls = happycalls.filter(call_stage__startswith=stage)
    
    # 상태 필터 - call_stage 기반으로 매핑
    if status:
        if status == 'scheduled':
            happycalls = happycalls.filter(call_stage__endswith='_pending')
        elif status == 'in_progress':
            happycalls = happycalls.filter(call_stage__endswith='_in_progress')
        elif status == 'completed':
            happycalls = happycalls.filter(call_stage__endswith='_completed')
        elif status == 'no_answer':
            happycalls = happycalls.filter(call_stage__endswith='_failed')
        elif status == 'refused':
            happycalls = happycalls.filter(call_stage='rejected')
    
    # 최신순 정렬
    happycalls = happycalls.order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(happycalls, 20)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    return render(request, 'happycall/happycall_list.html', {
        'happycalls': page_obj,
        'page_obj': page_obj,
        'search': search,
        'stage': stage,
        'status': status,
        'page_title': '전체 목록',
    })

@login_required
def manager_dashboard(request):
    """팀장 대시보드 - 팀원들의 해피콜 현황"""
    # 권한 체크 (관리자 또는 팀장만)
    if not (request.user.is_superuser or hasattr(request.user, 'managed_departments')):
        messages.error(request, '팀장 권한이 필요합니다.')
        return redirect('happycall:my_happycalls')
    
    # 통계 데이터
    from django.db.models import Count, Q
    from datetime import date, timedelta
    
    # 기간 필터 처리
    today = date.today()
    period = request.GET.get('period')
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    if period:
        # 빠른 기간 선택
        days = int(period)
        if days == 0:
            # 당일
            date_from = today
            date_to = today
        else:
            date_from = today - timedelta(days=days)
            date_to = today
    elif date_from_str and date_to_str:
        # 직접 입력된 날짜
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    else:
        # 기본값: 최근 30일
        date_from = today - timedelta(days=30)
        date_to = today
    
    # 기본 쿼리셋에 날짜 필터 적용
    base_queryset = HappyCall.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    # 전체 해피콜 통계
    total_stats = base_queryset.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(call_stage__endswith='_pending')),
        in_progress=Count('id', filter=Q(call_stage__endswith='_in_progress')),
        completed=Count('id', filter=Q(call_stage__endswith='_completed')),
        failed=Count('id', filter=Q(call_stage__endswith='_failed'))
    )
    
    # 담당자별 통계
    staff_stats = []
    
    # 활성 직원 목록
    employees = Employee.objects.filter(status='active').select_related('user')
    
    for employee in employees:
        user = employee.user
        stats = base_queryset.filter(
            Q(first_call_caller=user) |
            Q(second_call_caller=user) |
            Q(third_call_caller=user) |
            Q(fourth_call_caller=user)
        ).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(call_stage__endswith='_pending')),
            in_progress=Count('id', filter=Q(call_stage__endswith='_in_progress')), 
            completed=Count('id', filter=Q(call_stage__endswith='_completed')),
            failed=Count('id', filter=Q(call_stage__endswith='_failed'))
        )
        
        if stats['total'] > 0:
            stats['completion_rate'] = round((stats['completed'] / stats['total']) * 100, 1)
            staff_stats.append({
                'employee': employee,
                'user': user,
                **stats
            })
    
    # 완료율 기준으로 정렬
    staff_stats.sort(key=lambda x: x['completion_rate'], reverse=True)
    
    return render(request, 'happycall/manager_dashboard.html', {
        'total_stats': total_stats,
        'staff_stats': staff_stats,
        'page_title': '팀장 대시보드',
        'default_date_from': date_from.strftime('%Y-%m-%d'),
        'default_date_to': date_to.strftime('%Y-%m-%d'),
        'date_range_display': f"{date_from.strftime('%Y년 %m월 %d일')} ~ {date_to.strftime('%Y년 %m월 %d일')}",
    })

@login_required
def staff_detail(request, user_id):
    """담당자별 상세 통계"""
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q, Avg
    from datetime import date, timedelta
    from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
    
    User = get_user_model()
    staff_user = get_object_or_404(User, id=user_id)
    
    # 권한 체크 (관리자 또는 팀장만, 또는 본인)
    if not (request.user.is_superuser or hasattr(request.user, 'managed_departments') or request.user == staff_user):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('happycall:my_happycalls')
    
    # 기간 필터 처리
    today = date.today()
    period = request.GET.get('period')
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    if period:
        days = int(period)
        if days == 0:
            # 당일
            date_from = today
            date_to = today
        else:
            date_from = today - timedelta(days=days)
            date_to = today
    elif date_from_str and date_to_str:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    else:
        # 기본값: 최근 30일
        date_from = today - timedelta(days=30)
        date_to = today
    
    # 해당 담당자의 해피콜 쿼리
    staff_happycalls = HappyCall.objects.filter(
        Q(first_call_caller=staff_user) |
        Q(second_call_caller=staff_user) |
        Q(third_call_caller=staff_user) |
        Q(fourth_call_caller=staff_user),
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).select_related(
        'service_request__customer',
        'service_request__service_type',
    ).order_by('-created_at')
    
    # 전체 통계
    total_stats = staff_happycalls.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(call_stage__endswith='_pending')),
        in_progress=Count('id', filter=Q(call_stage__endswith='_in_progress')),
        completed=Count('id', filter=Q(call_stage__endswith='_completed')),
        failed=Count('id', filter=Q(call_stage__endswith='_failed'))
    )
    
    # 완료율 계산
    if total_stats['total'] > 0:
        total_stats['completion_rate'] = round((total_stats['completed'] / total_stats['total']) * 100, 1)
        total_stats['success_rate'] = round(((total_stats['completed'] + total_stats['in_progress']) / total_stats['total']) * 100, 1)
    else:
        total_stats['completion_rate'] = 0
        total_stats['success_rate'] = 0
    
    # 콜 단계별 통계
    stage_stats = []
    for stage_num, stage_name in [('1st', '1차콜'), ('2nd', '2차콜'), ('3rd', '3차콜'), ('4th', '4차콜')]:
        stage_calls = staff_happycalls.filter(call_stage__startswith=stage_num)
        stage_total = stage_calls.count()
        
        if stage_total > 0:
            stage_data = stage_calls.aggregate(
                pending=Count('id', filter=Q(call_stage__endswith='_pending')),
                in_progress=Count('id', filter=Q(call_stage__endswith='_in_progress')),
                completed=Count('id', filter=Q(call_stage__endswith='_completed')),
                failed=Count('id', filter=Q(call_stage__endswith='_failed'))
            )
            
            stage_data.update({
                'stage': stage_name,
                'stage_code': stage_num,
                'total': stage_total,
                'completion_rate': round((stage_data['completed'] / stage_total) * 100, 1) if stage_total > 0 else 0
            })
            
            stage_stats.append(stage_data)
    
    # 최근 해피콜 활동 (페이지네이션)
    paginator = Paginator(staff_happycalls, 20)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    # 직원 정보
    try:
        employee = Employee.objects.get(user=staff_user)
    except Employee.DoesNotExist:
        employee = None
    
    return render(request, 'happycall/staff_detail.html', {
        'staff_user': staff_user,
        'employee': employee,
        'total_stats': total_stats,
        'stage_stats': stage_stats,
        'happycalls': page_obj,
        'page_obj': page_obj,
        'default_date_from': date_from.strftime('%Y-%m-%d'),
        'default_date_to': date_to.strftime('%Y-%m-%d'),
        'date_range_display': f"{date_from.strftime('%Y년 %m월 %d일')} ~ {date_to.strftime('%Y년 %m월 %d일')}",
        'page_title': f'{staff_user.get_full_name() or staff_user.username} 상세 통계',
    })

@login_required
def happycall_assign(request):
    """해피콜 일괄 생성 페이지 (검사 완료 고객 대상)"""
    if request.method == 'POST':
        return handle_assign_request(request)
    
    # 필터 파라미터 받기
    filter_type = request.GET.get('filter_type', 'inspected_1week')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search', '')
    
    # 기본 날짜 범위 설정
    today = timezone.now().date()
    
    if filter_type == 'inspected_today':
        # 오늘 검사 받은 고객
        date_from = today
        date_to = today
    elif filter_type == 'inspected_1week':
        # 검사 후 1주일 (7일 ± 2일)
        target_date = today - timedelta(days=7)
        date_from = target_date - timedelta(days=2)
        date_to = target_date + timedelta(days=2)
    elif filter_type == 'inspected_3month':
        # 검사 후 3개월 (90일 ± 2일)
        target_date = today - timedelta(days=90)
        date_from = target_date - timedelta(days=2)
        date_to = target_date + timedelta(days=2)
    elif filter_type == 'inspected_6month':
        # 검사 후 6개월 (180일 ± 2일)
        target_date = today - timedelta(days=180)
        date_from = target_date - timedelta(days=2)
        date_to = target_date + timedelta(days=2)
    elif filter_type == 'inspected_12month':
        # 검사 후 12개월 (365일 ± 2일)
        target_date = today - timedelta(days=365)
        date_from = target_date - timedelta(days=2)
        date_to = target_date + timedelta(days=2)
    elif filter_type == 'custom' and start_date and end_date:
        # 직접 입력
        date_from = datetime.strptime(start_date, '%Y-%m-%d').date()
        date_to = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # 검사 안 받은 고객
        date_from = None
        date_to = None
    
    # 고객 쿼리 구성
    customers_query = Customer.objects.filter(
        is_active=True
    ).select_related().prefetch_related(
        'vehicle_ownerships__vehicle',
        'happy_calls'
    )
    
    # 검색 필터
    if search:
        customers_query = customers_query.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(vehicle_ownerships__vehicle__vehicle_number__icontains=search)
        )
    
    # 날짜 필터
    if filter_type == 'no_inspection':
        # 검사 기록이 없는 고객 (여러 검사 관련 키워드 포함)
        inspection_customer_ids = ServiceRequest.objects.filter(
            Q(service_type__name__icontains='검사') |
            Q(service_type__name__icontains='검') |
            Q(service_type__name__icontains='자동차검사') |
            Q(service_type__name__icontains='차량검사') |
            Q(service_type__name__icontains='종합검사') |
            Q(service_type__name__icontains='inspection') |
            Q(service_detail__icontains='검사') |
            Q(description__icontains='검사')
        ).values_list('customer_id', flat=True)
        customers_query = customers_query.exclude(id__in=inspection_customer_ids)
    elif date_from and date_to:
        # 특정 기간에 검사받은 고객 (접수일시 기준, 검사는 당일 처리)
        inspection_customer_ids = ServiceRequest.objects.filter(
            Q(service_type__name__icontains='검사') |
            Q(service_type__name__icontains='검') |
            Q(service_type__name__icontains='자동차검사') |
            Q(service_type__name__icontains='차량검사') |
            Q(service_type__name__icontains='종합검사') |
            Q(service_type__name__icontains='inspection') |
            Q(service_detail__icontains='검사') |
            Q(description__icontains='검사'),
            service_date__date__range=[date_from, date_to]
        ).values_list('customer_id', flat=True)
        customers_query = customers_query.filter(id__in=inspection_customer_ids)
    
    # 배정 상태에 따른 필터링
    show_assigned = request.GET.get('show_assigned', 'false') == 'true'
    
    if show_assigned:
        # 배정된 고객: 진행 중인 해피콜이 있는 고객
        assigned_customer_ids = HappyCall.objects.filter(
            # 완료되지 않은 상태들
            Q(call_stage__endswith='_pending') |
            Q(call_stage__endswith='_pending_approval') |
            Q(call_stage__endswith='_in_progress') |
            Q(call_stage__endswith='_failed')
        ).exclude(
            # 완전 완료된 상태들 제외
            Q(call_stage__endswith='_completed') |
            Q(call_stage='rejected') |
            Q(call_stage='skip')
        ).values_list('service_request__customer_id', flat=True).distinct()
        
        customers_query = customers_query.filter(id__in=assigned_customer_ids)
    else:
        # 미배정 고객: 진행 중인 해피콜이 없는 고객
        assigned_customer_ids = HappyCall.objects.filter(
            # 완료되지 않은 상태들
            Q(call_stage__endswith='_pending') |
            Q(call_stage__endswith='_pending_approval') |
            Q(call_stage__endswith='_in_progress') |
            Q(call_stage__endswith='_failed')
        ).exclude(
            # 완전 완료된 상태들 제외
            Q(call_stage__endswith='_completed') |
            Q(call_stage='rejected') |
            Q(call_stage='skip')
        ).values_list('service_request__customer_id', flat=True).distinct()
        
        customers_query = customers_query.exclude(id__in=assigned_customer_ids)

    # 최근 서비스 날짜 기준으로 정렬 (annotation 사용)
    from django.db.models import Max
    customers = customers_query.annotate(
        latest_service_date=Max('servicerequest__service_date')
    ).order_by('-latest_service_date', '-id').distinct()
    
    # 페이지네이션 적용
    paginator = Paginator(customers, 50)  # 50명씩
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 로깅 설정 (먼저 정의)
    import logging
    logger = logging.getLogger(__name__)
    
    # 고객별 상세 정보 구성
    customer_data = []
    for customer in page_obj:
        # 차량 정보 및 필터 매칭 차량 식별
        vehicles = [ov.vehicle for ov in customer.vehicle_ownerships.filter(end_date__isnull=True)]
        vehicle_info = []
        matching_vehicle_numbers = []
        
        for vehicle in vehicles:
            vehicle_number = vehicle.vehicle_number
            
            # 이 특정 차량이 필터 조건에 맞는 검사를 받았는지 확인
            is_matching = False
            if date_from and date_to:
                # 해당 특정 차량의 검사 기록 확인
                vehicle_inspections = ServiceRequest.objects.filter(
                    customer=customer,
                    vehicle=vehicle,  # 특정 차량으로 제한
                    service_type__name__icontains='검사',
                    service_date__date__range=[date_from, date_to]
                )
                
                # 디버깅용 로깅
                logger.info(f"Customer: {customer.name}, Vehicle: {vehicle_number}")
                logger.info(f"Date range: {date_from} ~ {date_to}")
                logger.info(f"Vehicle inspections found: {vehicle_inspections.count()}")
                for inspection in vehicle_inspections:
                    logger.info(f"  - Service: {inspection.service_type.name}, Date: {inspection.service_date.date()}")
                
                if vehicle_inspections.exists():
                    is_matching = True
                    matching_vehicle_numbers.append(vehicle_number)
                    logger.info(f"  -> MATCHING: {vehicle_number}")
                    
                    # 해당 차량의 가장 최근 검사일 가져오기
                    latest_vehicle_inspection = vehicle_inspections.order_by('-service_date').first()
                    vehicle_inspection_date = latest_vehicle_inspection.service_date.date()
                else:
                    logger.info(f"  -> NOT MATCHING: {vehicle_number}")
                    vehicle_inspection_date = None
            else:
                vehicle_inspection_date = None
            
            vehicle_info.append({
                'number': vehicle_number,
                'is_matching': is_matching,
                'inspection_date': vehicle_inspection_date  # 검사일 추가
            })
        
        vehicle_numbers = [v.vehicle_number for v in vehicles]
        
        # 최근 검사일 
        latest_inspection = ServiceRequest.objects.filter(
            customer=customer,
            service_type__name__icontains='검사'
        ).select_related('service_type').order_by('-service_date').first()
        
        # 최근 서비스일
        latest_service = ServiceRequest.objects.filter(
            customer=customer
        ).select_related('service_type').order_by('-service_date').first()
        
        # 최근 해피콜일 (happycall 앱의 HappyCall 사용)
        latest_happycall = HappyCall.objects.filter(
            service_request__customer=customer
        ).order_by('-created_at').first()
        
        # 배정된 고객인 경우 진행중인 해피콜 정보 추가 (happycall 앱의 HappyCall 사용)
        assigned_happycall = None
        if show_assigned:
            assigned_happycall = HappyCall.objects.filter(
                Q(service_request__customer=customer) &
                (Q(call_stage__endswith='_pending') |
                Q(call_stage__endswith='_pending_approval') |
                Q(call_stage__endswith='_in_progress') |
                Q(call_stage__endswith='_failed'))
            ).exclude(
                Q(call_stage__endswith='_completed') |
                Q(call_stage='rejected') |
                Q(call_stage='skip')
            ).select_related(
                'first_call_caller', 'second_call_caller', 
                'third_call_caller', 'fourth_call_caller'
            ).first()
        
        customer_data.append({
            'customer': customer,
            'vehicle_numbers': vehicle_numbers,
            'vehicle_info': vehicle_info,  # 차량별 매칭 정보
            'matching_vehicle_numbers': matching_vehicle_numbers,  # 조건에 맞는 차량번호들
            'latest_inspection_date': latest_inspection.service_date.date() if latest_inspection and latest_inspection.service_date else None,
            'latest_service_date': latest_service.service_date.date() if latest_service and latest_service.service_date else None,
            'latest_service_type': latest_service.service_type.name if latest_service else None,
            'latest_happycall_date': latest_happycall.created_at.date() if latest_happycall else None,
            'assigned_happycall': assigned_happycall,  # 배정된 해피콜 정보 추가
        })
    
    # 활성 직원 목록
    employees = Employee.objects.filter(status='active').select_related('user')
    
    # 현재 필터 조건 설명 생성 (실제 적용된 날짜 기준)
    filter_description = ""
    
    # 로깅으로 디버깅 정보 추가
    logger.info(f"Filter debug - filter_type: {filter_type}, start_date: {start_date}, end_date: {end_date}")
    logger.info(f"Calculated date_from: {date_from}, date_to: {date_to}")
    
    if filter_type == 'inspected_today':
        filter_description = f"오늘({today.strftime('%Y년 %m월 %d일')}) 검사 받은 고객"
    elif filter_type == 'inspected_1week':
        desc_date = today - timedelta(days=7)
        filter_description = f"{desc_date.strftime('%Y년 %m월 %d일')} 전후 (±2일) 검사 받은 고객"
    elif filter_type == 'inspected_3month':
        desc_date = today - timedelta(days=90)
        filter_description = f"{desc_date.strftime('%Y년 %m월 %d일')} 전후 (±2일) 검사 받은 고객"
    elif filter_type == 'inspected_6month':
        desc_date = today - timedelta(days=180)
        filter_description = f"{desc_date.strftime('%Y년 %m월 %d일')} 전후 (±2일) 검사 받은 고객"
    elif filter_type == 'inspected_12month':
        desc_date = today - timedelta(days=365)
        filter_description = f"{desc_date.strftime('%Y년 %m월 %d일')} 전후 (±2일) 검사 받은 고객"
    elif filter_type == 'custom' and date_from and date_to:
        filter_description = f"{date_from.strftime('%Y년 %m월 %d일')} ~ {date_to.strftime('%Y년 %m월 %d일')} 기간 검사 받은 고객"
    elif filter_type == 'no_inspection':
        filter_description = "검사 기록이 없는 고객"
    else:
        # 실제 적용된 날짜가 있으면 그것을 표시
        if date_from and date_to:
            filter_description = f"{date_from.strftime('%Y년 %m월 %d일')} ~ {date_to.strftime('%Y년 %m월 %d일')} 기간 검사 받은 고객"
        else:
            filter_description = "모든 고객"
    
    # 검색 조건 추가
    if search:
        filter_description += f" ('{search}' 검색)"
    
    context = {
        'customer_data': customer_data,
        'employees': employees,
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
        'search': search,
        'today': today,
        'page_obj': page_obj,
        'paginator': paginator,
        'show_assigned': show_assigned,  # 배정 상태 표시용
        'filter_description': filter_description,  # 필터 조건 설명
        'date_from': date_from,  # 실제 날짜 범위
        'date_to': date_to,
    }
    
    return render(request, 'happycall/happycall_assign.html', context)





def handle_assign_request(request):
    """해피콜 일괄 생성 처리"""
    selected_customers = request.POST.getlist('selected_customers')
    assignee_id = request.POST.get('assignee')
    call_stage = request.POST.get('call_stage', '1st_pending')
    
    # 필터 조건 보존을 위한 파라미터 수집
    filter_params = {}
    if request.GET.get('filter_type'):
        filter_params['filter_type'] = request.GET.get('filter_type')
    if request.GET.get('start_date'):
        filter_params['start_date'] = request.GET.get('start_date')
    if request.GET.get('end_date'):
        filter_params['end_date'] = request.GET.get('end_date')
    if request.GET.get('search'):
        filter_params['search'] = request.GET.get('search')
    if request.GET.get('show_assigned'):
        filter_params['show_assigned'] = request.GET.get('show_assigned')
    
    if not selected_customers:
        messages.error(request, '선택된 고객이 없습니다.')
        return redirect('happycall:assign', **filter_params) if filter_params else redirect('happycall:assign')
    
    if not assignee_id:
        messages.error(request, '담당자를 선택해주세요.')
        return redirect('happycall:assign', **filter_params) if filter_params else redirect('happycall:assign')
    
    try:
        assignee = Employee.objects.get(id=assignee_id, status='active')
    except Employee.DoesNotExist:
        messages.error(request, '유효하지 않은 담당자입니다.')
        return redirect('happycall:assign', **filter_params) if filter_params else redirect('happycall:assign')
    
    # 대량 생성
    created_count = 0
    for customer_id in selected_customers:
        try:
            customer = Customer.objects.get(id=customer_id)
            
            # 해당 고객의 최근 서비스 요청 찾기
            latest_service = ServiceRequest.objects.filter(customer=customer).order_by('-service_date').first()
            
            if not latest_service:
                continue  # 서비스 요청이 없는 고객은 건너뛰기
            
            # 이미 해당 서비스 요청에 대한 해피콜이 있는지 확인
            existing = HappyCall.objects.filter(
                service_request=latest_service
            ).exists()
            
            if not existing:
                # 해피콜 생성
                HappyCall.objects.create(
                    service_request=latest_service,
                    call_stage=call_stage,
                    first_call_caller=assignee.user if call_stage.startswith('1st') else None,
                    second_call_caller=assignee.user if call_stage.startswith('2nd') else None,
                    third_call_caller=assignee.user if call_stage.startswith('3rd') else None,
                    fourth_call_caller=assignee.user if call_stage.startswith('4th') else None
                )
                created_count += 1
                
        except Customer.DoesNotExist:
            continue
    
    messages.success(request, f'{created_count}건의 해피콜이 생성되었습니다.')
    
    # 필터 조건을 유지하면서 리다이렉트
    if filter_params:
        from urllib.parse import urlencode
        redirect_url = f"/happycall/assign/?{urlencode(filter_params)}"
        return redirect(redirect_url)
    else:
        return redirect('happycall:assign')


@login_required
def happycall_detail(request, pk):
    """해피콜 상세보기 (수행/수정 기능 통합)"""
    happycall = get_object_or_404(HappyCall, pk=pk)
    
    # POST 요청 처리 (해피콜 수행/수정)
    if request.method == 'POST':
        # 해피콜 수행 처리
        contact_result = request.POST.get('contact_result')
        satisfaction_score = request.POST.get('satisfaction_score')
        feedback = request.POST.get('feedback')
        follow_up_needed = request.POST.get('follow_up_needed') == 'on'
        additional_service_interest = request.POST.get('additional_service_interest') == 'on'
        interested_service_notes = request.POST.get('interested_service_notes', '')
        no_call_request = request.POST.get('no_call_request') == 'on'
        notes = request.POST.get('notes')
        
        # 해피콜 업데이트
        if contact_result == 'connected':
            if satisfaction_score:
                happycall.overall_satisfaction = int(satisfaction_score)
            happycall.customer_feedback = feedback
            happycall.follow_up_needed = follow_up_needed
            happycall.additional_service_interest = additional_service_interest
            happycall.interested_service_notes = interested_service_notes
        
        # 통화 금지 요청은 연결 여부와 상관없이 적용
        happycall.no_call_request = no_call_request
        
        if contact_result == 'connected':
            # 1차콜 완료 처리
            if happycall.call_stage.startswith('1st'):
                happycall.call_stage = '1st_completed'
                happycall.first_call_success = True
                happycall.first_call_date = timezone.now()
                happycall.first_call_caller = request.user
                happycall.first_call_notes = notes
            # 2차콜 완료 처리  
            elif happycall.call_stage.startswith('2nd'):
                happycall.call_stage = '2nd_completed'
                happycall.second_call_success = True
                happycall.second_call_date = timezone.now()
                happycall.second_call_caller = request.user
                happycall.second_call_notes = notes
            # 3차콜 완료 처리
            elif happycall.call_stage.startswith('3rd'):
                happycall.call_stage = '3rd_completed'
                happycall.third_call_success = True
                happycall.third_call_date = timezone.now()
                happycall.third_call_caller = request.user
                happycall.third_call_notes = notes
        else:
            # 통화 실패 처리
            if happycall.call_stage.startswith('1st'):
                happycall.call_stage = '1st_failed'
                happycall.first_call_success = False
                happycall.first_call_notes = f"연락실패: {contact_result}"
            elif happycall.call_stage.startswith('2nd'):
                happycall.call_stage = '2nd_failed'
                happycall.second_call_success = False
                happycall.second_call_notes = f"연락실패: {contact_result}"
            elif happycall.call_stage.startswith('3rd'):
                happycall.call_stage = '3rd_failed'
                happycall.third_call_success = False
                happycall.third_call_notes = f"연락실패: {contact_result}"
        
        happycall.save()
        messages.success(request, '해피콜이 완료되었습니다.')
        return redirect('happycall:detail', pk=pk)
    
    # GET 요청 처리
    # 해피콜 결과가 있는지 확인 (완료된 경우)
    result = None
    if (happycall.call_stage.endswith('_completed') and 
        (happycall.overall_satisfaction or happycall.customer_feedback)):
        result = happycall  # happycall 자체를 result로 사용
    
    # 매출 기록 조회
    revenue_records = HappyCallRevenue.objects.filter(happy_call=happycall)
    
    # 고객의 서비스 이력 조회
    customer = happycall.service_request.customer
    service_history = ServiceRequest.objects.filter(
        customer=customer
    ).select_related(
        'service_type', 'vehicle'
    ).order_by('-service_date')[:10]  # 최근 10건
    
    # 고객의 차량 정보
    customer_vehicles = [ov.vehicle for ov in customer.vehicle_ownerships.filter(end_date__isnull=True)]
    
    # 수행/수정 모드 판단
    edit_mode = request.GET.get('edit') == 'true'
    is_pending = (happycall.call_stage.endswith('_pending') or 
                  happycall.call_stage.endswith('_in_progress'))
    
    context = {
        'happycall': happycall,
        'result': result,
        'revenue_records': revenue_records,
        'service_history': service_history,
        'customer_vehicles': customer_vehicles,
        'edit_mode': edit_mode,
        'is_pending': is_pending,
        'title': '해피콜 상세보기'
    }
    return render(request, 'happycall/happycall_detail.html', context)



@login_required
def happycall_update(request, pk):
    """해피콜 수정"""
    happycall = get_object_or_404(HappyCall, pk=pk)
    
    context = {
        'happycall': happycall,
        'title': '해피콜 수정'
    }
    return render(request, 'happycall/happycall_form.html', context)


@login_required  
def happycall_create_callback(request, pk):
    """해피콜 재연락 생성"""
    happycall = get_object_or_404(HappyCall, pk=pk)
    
    context = {
        'happycall': happycall,
        'title': '재연락 생성'
    }
    return render(request, 'happycall/happycall_form.html', context)


@login_required
def happycall_revenue_create(request, pk):
    """해피콜 매출 생성"""
    happycall = get_object_or_404(HappyCall, pk=pk)
    
    context = {
        'happycall': happycall,
        'title': '매출 등록'
    }
    return render(request, 'happycall/happycall_form.html', context)


@login_required
def happycall_unified_call(request, pk):
    """해피콜 통합 수행"""
    happycall = get_object_or_404(HappyCall, pk=pk)
    
    context = {
        'happycall': happycall,
        'title': '통합 해피콜 수행'
    }
    return render(request, 'happycall/unified_call_perform.html', context)


@login_required
def cancel_assignment(request, pk):
    """해피콜 배정 해제"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})
    
    try:
        happycall = get_object_or_404(HappyCall, pk=pk)
        
        # 권한 체크 (관리자 또는 담당자만)
        current_callers = [
            happycall.first_call_caller,
            happycall.second_call_caller,
            happycall.third_call_caller,
            happycall.fourth_call_caller
        ]
        
        if not (request.user.is_superuser or request.user in current_callers):
            return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
        
        # 진행중인 상태인지 확인
        if happycall.call_stage.endswith('_completed') or happycall.call_stage in ['rejected', 'skip']:
            return JsonResponse({'success': False, 'message': '이미 완료된 해피콜은 배정 해제할 수 없습니다.'})
        
        # 배정 해제 - 해피콜 삭제
        customer_name = happycall.service_request.customer.name
        happycall.delete()
        
        messages.success(request, f'{customer_name} 고객의 해피콜 배정이 해제되었습니다.')
        return JsonResponse({'success': True, 'message': '배정이 해제되었습니다.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})


@login_required
def bulk_cancel_assignment(request):
    """해피콜 일괄 배정 해제"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})
    
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Bulk cancel request from user: {request.user}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Content type: {request.content_type}")
        logger.info(f"Request body: {request.body}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        if not request.body:
            return JsonResponse({'success': False, 'message': '요청 데이터가 없습니다.'})
        
        try:
            data = json.loads(request.body)
            logger.info(f"Parsed JSON data: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'success': False, 'message': f'잘못된 JSON 형식입니다: {str(e)}'})
            
        happycall_ids = data.get('happycall_ids', [])
        
        logger.info(f"Parsed happycall_ids: {happycall_ids}")
        
        if not happycall_ids:
            return JsonResponse({'success': False, 'message': '선택된 해피콜이 없습니다.'})
        
        # 해피콜 조회 및 권한 확인
        happycalls = HappyCall.objects.filter(id__in=happycall_ids)
        logger.info(f"Found {happycalls.count()} happycalls to process")
        
        deleted_count = 0
        error_messages = []
        
        for happycall in happycalls:
            try:
                customer_name = happycall.service_request.customer.name
                logger.info(f"Processing happycall for {customer_name} (ID: {happycall.id}, Stage: {happycall.call_stage})")
                
                # 권한 체크 (관리자 또는 담당자만)
                current_callers = [
                    happycall.first_call_caller,
                    happycall.second_call_caller,
                    happycall.third_call_caller,
                    happycall.fourth_call_caller
                ]
                
                logger.info(f"Current user: {request.user}, Is superuser: {request.user.is_superuser}")
                logger.info(f"Current callers: {[str(caller) for caller in current_callers if caller]}")
                
                if not (request.user.is_superuser or request.user in current_callers):
                    error_msg = f'{customer_name}: 권한이 없습니다.'
                    error_messages.append(error_msg)
                    logger.warning(error_msg)
                    continue
                
                # 진행중인 상태인지 확인
                if happycall.call_stage.endswith('_completed') or happycall.call_stage in ['rejected', 'skip']:
                    error_msg = f'{customer_name}: 이미 완료된 해피콜입니다.'
                    error_messages.append(error_msg)
                    logger.warning(error_msg)
                    continue
                
                # 해피콜 삭제
                logger.info(f"Deleting happycall ID: {happycall.id} for {customer_name}")
                happycall.delete()
                deleted_count += 1
                logger.info(f"Successfully deleted happycall for {customer_name}")
                
            except Exception as e:
                error_msg = f'{customer_name}: {str(e)}'
                error_messages.append(error_msg)
                logger.error(f"Error processing happycall for {customer_name}: {e}")
                continue
        
        # 결과 메시지 생성
        result_message = f'{deleted_count}건의 배정이 해제되었습니다.'
        if error_messages:
            result_message += f' (오류: {len(error_messages)}건)'
        
        return JsonResponse({
            'success': True, 
            'message': result_message,
            'deleted_count': deleted_count,
            'error_count': len(error_messages),
            'errors': error_messages
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})