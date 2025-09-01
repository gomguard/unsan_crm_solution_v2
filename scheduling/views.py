from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
import json
from datetime import datetime
from .models import Schedule, Department

User = get_user_model()

@login_required
def calendar_view(request):
    """캘린더 메인 페이지"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    departments = Department.objects.all()
    employees = User.objects.filter(user_type__in=['employee', 'admin']).select_related().order_by('department', 'position')
    
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
    assignees = request.GET.get('assignees')  # 여러 직원 지원
    
    schedules = Schedule.objects.select_related('department', 'assignee', 'creator').all()
    
    if start and end:
        schedules = schedules.filter(
            start_datetime__gte=start,
            end_datetime__lte=end
        )
    
    # 부서별 필터 (display_name으로 필터링)
    if department and department != 'all':
        schedules = schedules.filter(department__display_name=department)
    
    # 담당자별 필터 (여러 직원 지원)
    if assignees and assignees != 'all':
        assignee_list = [username.strip() for username in assignees.split(',') if username.strip()]
        if assignee_list:
            schedules = schedules.filter(assignee__username__in=assignee_list)
        else:
            # 담당자가 하나도 선택되지 않았으면 아무것도 보여주지 않음
            schedules = schedules.none()
    elif assignees == '':
        # 빈 문자열이면 아무것도 보여주지 않음  
        schedules = schedules.none()
    
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

@login_required
def add_schedule_view(request):
    """일정 추가 페이지"""
    current_user = request.user
    departments = Department.objects.all()
    
    # 사용자 권한에 따른 직원 목록 필터링
    if current_user.is_superuser:
        # 최고 관리자: 모든 직원 (시스템 관리자 포함)
        employees = User.objects.filter(
            models.Q(user_type__in=['employee', 'admin']) | models.Q(is_superuser=True)
        ).select_related().order_by('department', 'position')
    else:
        # 현재 사용자가 관리하는 부서들 찾기
        managed_departments = Department.objects.filter(manager=current_user)
        
        if managed_departments.exists():
            # 부서 관리자: 자신이 관리하는 부서의 직원들 + 본인
            managed_dept_ids = list(managed_departments.values_list('id', flat=True))
            employees = User.objects.filter(
                models.Q(department_id__in=managed_dept_ids) | models.Q(id=current_user.id)
            ).select_related('department').order_by('department', 'position')
        else:
            # 일반 직원: 본인만
            employees = User.objects.filter(id=current_user.id)
    
    # 현재 사용자가 관리하는 부서들
    managed_departments = Department.objects.filter(manager=current_user)
    
    return render(request, 'scheduling/add_schedule.html', {
        'departments': departments,
        'employees': employees,
        'current_user': current_user,
        'managed_departments': managed_departments
    })

@login_required 
@csrf_exempt
def add_schedule_api(request):
    """일정 추가 API"""
    print(f"API 호출됨 - 메서드: {request.method}, 사용자: {request.user}")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST 메서드만 허용됩니다.'})
    
    try:
        data = json.loads(request.body)
        print(f"받은 데이터: {data}")
        
        # 필수 필드 검증
        required_fields = ['title', 'start_datetime', 'end_datetime', 'department', 'assignee']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field} 필드가 필요합니다.'})
        
        # 부서 객체 찾기
        try:
            department = Department.objects.get(name=data['department'])
        except Department.DoesNotExist:
            return JsonResponse({'success': False, 'message': '존재하지 않는 부서입니다.'})
        
        # 담당자 객체 찾기
        try:
            assignee = User.objects.get(username=data['assignee'])
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '존재하지 않는 담당자입니다.'})
        
        # 권한 검증: 세분화된 권한 체크
        def can_assign_to_user(current_user, target_user):
            # 최고 관리자는 모든 사용자에게 할당 가능
            if current_user.is_superuser:
                return True
            
            # 본인에게는 항상 할당 가능
            if current_user == target_user:
                return True
            
            # 부서 관리자는 자신이 관리하는 부서의 직원에게만 할당 가능
            managed_departments = Department.objects.filter(manager=current_user)
            if managed_departments.exists():
                managed_dept_ids = list(managed_departments.values_list('id', flat=True))
                if target_user.department_id in managed_dept_ids:
                    return True
            
            return False
        
        if not can_assign_to_user(request.user, assignee):
            return JsonResponse({'success': False, 'message': '해당 사용자에게 일정을 추가할 권한이 없습니다.'})
        
        # 일시 파싱
        try:
            start_datetime = datetime.fromisoformat(data['start_datetime'])
            end_datetime = datetime.fromisoformat(data['end_datetime'])
            
            # timezone aware로 변경
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        except ValueError as e:
            return JsonResponse({'success': False, 'message': '잘못된 일시 형식입니다.'})
        
        # 일시 검증
        if end_datetime <= start_datetime:
            return JsonResponse({'success': False, 'message': '종료 일시는 시작 일시보다 늦어야 합니다.'})
        
        # 일정 생성
        schedule = Schedule.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            location=data.get('location', ''),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            department=department,
            assignee=assignee,
            creator=request.user,
            priority=data.get('priority', 'normal'),
            status=data.get('status', 'pending'),
            is_confirmed_by_assignee=(data.get('status') in ['confirmed', 'completed'])
        )
        
        print(f"일정 생성 완료: ID={schedule.id}, 제목={schedule.title}")
        return JsonResponse({
            'success': True, 
            'message': '일정이 성공적으로 추가되었습니다.',
            'schedule_id': schedule.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '잘못된 JSON 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'})

def appointment_list(request):
    return render(request, 'scheduling/appointment_list.html')
