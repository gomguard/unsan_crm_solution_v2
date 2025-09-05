from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Employee
from scheduling.models import Department

User = get_user_model()

@login_required
def employee_list(request):
    """직원 목록"""
    employees = Employee.objects.select_related('user', 'department').all()
    
    # 검색 필터
    search = request.GET.get('search')
    if search:
        employees = employees.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(employee_id__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # 부서 필터
    department = request.GET.get('department')
    if department:
        employees = employees.filter(department_id=department)
    
    # 상태 필터
    status = request.GET.get('status')
    if status:
        employees = employees.filter(status=status)
    
    # 정렬
    sort_by = request.GET.get('sort', 'position')
    sort_order = request.GET.get('order', 'asc')
    
    # 정렬 옵션 매핑
    sort_options = {
        'position': 'position',
        'hire_date': 'hire_date', 
        'name': 'user__username',
        'department': 'department__name',
        'employee_id': 'employee_id'
    }
    
    if sort_by in sort_options:
        order_field = sort_options[sort_by]
        if sort_order == 'desc':
            order_field = f'-{order_field}'
        
        # 직급별 정렬을 위한 특별 처리
        if sort_by == 'position':
            # 직급 우선순위: ceo > director > manager > staff
            position_order = ['ceo', 'director', 'manager', 'staff']
            case_conditions = []
            for i, pos in enumerate(position_order):
                case_conditions.append(f"WHEN '{pos}' THEN {i}")
            case_sql = f"CASE employees_employee.position {' '.join(case_conditions)} END"
            employees = employees.extra(
                select={'position_order': case_sql},
                order_by=['position_order' if sort_order == 'asc' else '-position_order']
            )
        elif sort_by == 'hire_date':
            # 입사일 정렬 (최신입사자 우선 또는 선임 우선)
            employees = employees.order_by(order_field)
        else:
            employees = employees.order_by(order_field)
    else:
        employees = employees.order_by('position', 'hire_date')
    
    # 페이지네이션
    paginator = Paginator(employees, 20)
    page = request.GET.get('page')
    employees = paginator.get_page(page)
    
    departments = Department.objects.all()
    
    context = {
        'employees': employees,
        'departments': departments,
        'search': search,
        'selected_department': department,
        'selected_status': status,
        'sort_by': sort_by,
        'sort_order': sort_order,
    }
    return render(request, 'employees/employee_list.html', context)

@login_required
def employee_detail(request, employee_id):
    """직원 상세 - 통계 및 활동 이력 포함"""
    from django.db.models import Count, Sum, Avg
    from django.utils import timezone
    from datetime import timedelta
    from happycall.models import HappyCall
    from services.models import ServiceRequest
    from scheduling.models import Schedule
    from happycall.models import HappyCallRevenue
    
    employee = get_object_or_404(Employee, id=employee_id)
    user = employee.user
    
    # 기본 날짜 설정
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    quarter_ago = today - timedelta(days=90)
    year_ago = today - timedelta(days=365)
    
    # 해피콜 통계
    happycall_stats = {}
    
    # 전체 담당 해피콜
    total_happycalls = HappyCall.objects.filter(
        Q(first_call_caller=user) |
        Q(second_call_caller=user) |
        Q(third_call_caller=user) |
        Q(fourth_call_caller=user)
    ).distinct()
    
    happycall_stats['total'] = total_happycalls.count()
    
    # 기간별 완료 콜
    for period, start_date, label in [
        ('week', week_ago, '이번 주'),
        ('month', month_ago, '이번 달'),
        ('quarter', quarter_ago, '분기'),
        ('year', year_ago, '올해')
    ]:
        completed_calls = HappyCall.objects.filter(
            Q(first_call_caller=user, first_call_success=True, first_call_date__gte=start_date) |
            Q(second_call_caller=user, second_call_success=True, second_call_date__gte=start_date) |
            Q(third_call_caller=user, third_call_success=True, third_call_date__gte=start_date) |
            Q(fourth_call_caller=user, fourth_call_success=True, fourth_call_date__gte=start_date)
        ).distinct().count()
        
        happycall_stats[f'{period}_completed'] = completed_calls
    
    # 성공률 및 만족도
    first_calls = HappyCall.objects.filter(first_call_caller=user, first_call_date__isnull=False)
    if first_calls.exists():
        successful_calls = first_calls.filter(first_call_success=True).count()
        happycall_stats['success_rate'] = round((successful_calls / first_calls.count() * 100), 1)
        
        # 평균 만족도
        avg_satisfaction = first_calls.filter(
            overall_satisfaction__isnull=False
        ).aggregate(avg=Avg('overall_satisfaction'))['avg']
        happycall_stats['avg_satisfaction'] = round(avg_satisfaction, 1) if avg_satisfaction else 0
    else:
        happycall_stats['success_rate'] = 0
        happycall_stats['avg_satisfaction'] = 0
    
    # 진행중인 콜
    pending_calls = HappyCall.objects.filter(
        Q(first_call_caller=user, call_stage__in=['1st_pending', '1st_in_progress']) |
        Q(second_call_caller=user, call_stage__in=['2nd_pending', '2nd_in_progress']) |
        Q(third_call_caller=user, call_stage__in=['3rd_pending', '3rd_in_progress']) |
        Q(fourth_call_caller=user, call_stage__in=['4th_pending', '4th_in_progress'])
    ).distinct()
    happycall_stats['pending'] = pending_calls.count()
    
    # 매출 통계 (해피콜 관련 매출)
    revenue_stats = {}
    
    # 해피콜로 인한 매출
    happycall_revenues = HappyCallRevenue.objects.filter(
        happy_call__in=total_happycalls
    )
    
    total_revenue = happycall_revenues.aggregate(
        total=Sum('actual_amount')
    )['total'] or 0
    
    month_revenue = happycall_revenues.filter(
        proposed_at__gte=month_ago
    ).aggregate(
        total=Sum('actual_amount')
    )['total'] or 0
    
    revenue_stats = {
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'revenue_count': happycall_revenues.count(),
    }
    
    # 서비스 요청 통계 (생성자 기준)
    service_stats = {}
    
    created_services = ServiceRequest.objects.filter(created_by=user)
    service_stats['total_created'] = created_services.count()
    service_stats['month_created'] = created_services.filter(created_at__gte=month_ago).count()
    
    # 서비스 타입별 분포
    service_types = created_services.values(
        'service_type__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    service_stats['types'] = service_types
    
    # 일정 관리 통계
    schedule_stats = {}
    
    # 담당 일정
    assigned_schedules = Schedule.objects.filter(assignee=user)
    schedule_stats['total_assigned'] = assigned_schedules.count()
    schedule_stats['pending'] = assigned_schedules.filter(status='pending').count()
    schedule_stats['completed'] = assigned_schedules.filter(status='completed').count()
    
    # 이번 달 일정
    month_schedules = assigned_schedules.filter(
        start_datetime__gte=month_ago
    )
    schedule_stats['month_schedules'] = month_schedules.count()
    
    # 최근 활동 이력 (시간순)
    activities = []
    
    # 최근 해피콜 활동
    recent_happycalls = HappyCall.objects.filter(
        Q(first_call_caller=user) |
        Q(second_call_caller=user) |
        Q(third_call_caller=user) |
        Q(fourth_call_caller=user)
    ).distinct().order_by('-updated_at')[:10]
    
    for happycall in recent_happycalls:
        activities.append({
            'type': 'happycall',
            'title': f'해피콜: {happycall.service_request.customer.name}',
            'description': f'{happycall.get_call_stage_display()}',
            'date': happycall.updated_at,
            'url': f'/happycall/{happycall.id}/',
            'icon': '📞',
            'color': 'purple'
        })
    
    # 최근 생성한 서비스
    recent_services = created_services.order_by('-created_at')[:10]
    for service in recent_services:
        activities.append({
            'type': 'service',
            'title': f'서비스 생성: {service.customer.name}',
            'description': f'{service.service_type.name} - {service.get_status_display()}',
            'date': service.created_at,
            'url': f'/services/{service.id}/',
            'icon': '🔧',
            'color': 'green'
        })
    
    # 최근 일정
    recent_schedules = assigned_schedules.order_by('-created_at')[:10]
    for schedule in recent_schedules:
        activities.append({
            'type': 'schedule',
            'title': f'일정: {schedule.title}',
            'description': f'{schedule.start_datetime.strftime("%Y-%m-%d %H:%M")}',
            'date': schedule.created_at,
            'url': f'/scheduling/schedule/{schedule.id}/',
            'icon': '📅',
            'color': 'blue'
        })
    
    # 활동을 날짜순 정렬
    activities.sort(key=lambda x: x['date'], reverse=True)
    activities = activities[:20]  # 최근 20개만
    
    # 월별 성과 트렌드 (최근 6개월)
    monthly_performance = []
    for i in range(6):
        month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        
        month_happycalls = HappyCall.objects.filter(
            Q(first_call_caller=user, first_call_success=True, first_call_date__gte=month_start, first_call_date__lt=next_month) |
            Q(second_call_caller=user, second_call_success=True, second_call_date__gte=month_start, second_call_date__lt=next_month) |
            Q(third_call_caller=user, third_call_success=True, third_call_date__gte=month_start, third_call_date__lt=next_month) |
            Q(fourth_call_caller=user, fourth_call_success=True, fourth_call_date__gte=month_start, fourth_call_date__lt=next_month)
        ).distinct().count()
        
        month_services = created_services.filter(
            created_at__gte=month_start,
            created_at__lt=next_month
        ).count()
        
        month_revenue = happycall_revenues.filter(
            proposed_at__gte=month_start,
            proposed_at__lt=next_month
        ).aggregate(total=Sum('actual_amount'))['total'] or 0
        
        monthly_performance.append({
            'month': month_start.strftime('%Y-%m'),
            'happycalls': month_happycalls,
            'services': month_services,
            'revenue': month_revenue
        })
    
    monthly_performance.reverse()  # 시간순 정렬
    
    context = {
        'employee': employee,
        'happycall_stats': happycall_stats,
        'revenue_stats': revenue_stats,
        'service_stats': service_stats,
        'schedule_stats': schedule_stats,
        'activities': activities,
        'monthly_performance': monthly_performance,
        'pending_calls': pending_calls[:5],  # 상세 페이지용 미리보기
    }
    
    return render(request, 'employees/employee_detail_enhanced.html', context)

@login_required
def employee_create(request):
    """직원 생성"""
    if request.method == 'POST':
        # 사용자 정보
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        
        # 직원 정보
        employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department')
        position = request.POST.get('position')
        phone = request.POST.get('phone')
        hire_date = request.POST.get('hire_date') or None
        status = request.POST.get('status')
        notes = request.POST.get('notes')
        
        try:
            # 사용자 생성
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            
            # 직원 프로필 생성
            Employee.objects.create(
                user=user,
                employee_id=employee_id,
                department_id=department_id if department_id else None,
                position=position,
                phone=phone,
                hire_date=hire_date,
                status=status,
                notes=notes
            )
            
            messages.success(request, f'{username} 직원이 성공적으로 등록되었습니다.')
            return redirect('employees:employee_list')
            
        except Exception as e:
            messages.error(request, f'직원 등록 중 오류가 발생했습니다: {str(e)}')
    
    departments = Department.objects.all()
    return render(request, 'employees/employee_form.html', {'departments': departments})

@login_required
def employee_edit(request, employee_id):
    """직원 수정"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        # 사용자 정보 업데이트
        user = employee.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # 직원 정보 업데이트
        employee.employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department')
        employee.department_id = department_id if department_id else None
        employee.position = request.POST.get('position')
        employee.phone = request.POST.get('phone', '')
        hire_date = request.POST.get('hire_date')
        employee.hire_date = hire_date if hire_date else None
        employee.status = request.POST.get('status')
        employee.notes = request.POST.get('notes', '')
        employee.save()
        
        messages.success(request, f'{employee.user.username} 직원 정보가 수정되었습니다.')
        return redirect('employees:employee_detail', employee_id=employee.id)
    
    departments = Department.objects.all()
    return render(request, 'employees/employee_form.html', {
        'employee': employee,
        'departments': departments,
        'is_edit': True
    })

@login_required
def employee_delete(request, employee_id):
    """직원 삭제"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        username = employee.user.username
        user = employee.user
        employee.delete()
        user.delete()  # User 모델도 함께 삭제
        
        messages.success(request, f'{username} 직원이 삭제되었습니다.')
        return redirect('employees:employee_list')
    
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})
