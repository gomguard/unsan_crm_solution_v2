from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import Schedule, Department

@login_required
def calendar_view(request):
    """캘린더 메인 페이지"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    departments = Department.objects.all()
    employees = User.objects.filter(user_type='employee').select_related().order_by('department', 'position')
    
    return render(request, 'scheduling/calendar.html', {
        'departments': departments,
        'employees': employees
    })

@login_required
def get_events(request):
    """FullCalendar용 이벤트 데이터 API"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    department = request.GET.get('department')
    assignee = request.GET.get('assignee')
    
    schedules = Schedule.objects.select_related('department', 'assignee', 'creator').all()
    
    if start and end:
        schedules = schedules.filter(
            start_datetime__gte=start,
            end_datetime__lte=end
        )
    
    # 부서별 필터 (display_name으로 필터링)
    if department and department != 'all':
        schedules = schedules.filter(department__display_name=department)
    
    # 담당자별 필터
    if assignee and assignee != 'all':
        schedules = schedules.filter(assignee__username=assignee)
    
    events = []
    for schedule in schedules:
        # 부서별 색상 설정
        color_map = {
            'engine_oil': '#3B82F6',  # 파랑
            'insurance': '#10B981',   # 초록
            'happycall': '#F59E0B',   # 주황
            'admin': '#8B5CF6',       # 보라
        }
        
        events.append({
            'id': schedule.id,
            'title': schedule.title,
            'start': schedule.start_datetime.isoformat(),
            'end': schedule.end_datetime.isoformat(),
            'backgroundColor': color_map.get(schedule.department.name, '#6B7280'),
            'extendedProps': {
                'description': schedule.description,
                'location': schedule.location,
                'status': schedule.status,
                'priority': schedule.priority,
                'assignee': f"{schedule.assignee.last_name}{schedule.assignee.first_name}",
                'assignee_username': schedule.assignee.username,
                'department': schedule.department.display_name,
            }
        })
    
    return JsonResponse(events, safe=False)

def appointment_list(request):
    return render(request, 'scheduling/appointment_list.html')
