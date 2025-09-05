from django.shortcuts import render, get_object_or_404, redirect
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
    from employees.models import Employee
    
    departments = Department.objects.all()
    # Employee 모델을 통해 활성 직원들을 조회
    employees = Employee.objects.filter(status='active').select_related('user', 'department').order_by('department', 'position')
    
    # superuser들을 별도로 조회하여 포함 (Employee 모델에 없는 관리자들)
    superusers = User.objects.filter(is_superuser=True).exclude(
        id__in=Employee.objects.values_list('user_id', flat=True)
    )
    
    # Employee 객체와 같은 형태로 사용할 수 있도록 가상 객체 생성
    class VirtualEmployee:
        def __init__(self, user):
            self.user = user
            self.department = None
            self.position = 'admin'
            
        def get_position_display(self):
            return '관리자'
    
    # superuser들을 가상 직원으로 변환
    virtual_admins = [VirtualEmployee(user) for user in superusers]
    
    # 실제 직원들과 관리자들을 합쳐서 전달
    all_employees = list(employees) + virtual_admins
    
    return render(request, 'scheduling/calendar.html', {
        'departments': departments,
        'employees': all_employees
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
                'creator_username': schedule.creator.username,
                'department_manager_username': schedule.department.manager.username if schedule.department.manager else None,
            }
        })
    
    return JsonResponse(events, safe=False)

@login_required
def add_schedule_view(request):
    """일정 추가/수정 페이지"""
    current_user = request.user
    departments = Department.objects.all()
    
    # 수정 모드 확인
    edit_schedule_id = request.GET.get('edit')
    edit_schedule = None
    if edit_schedule_id:
        try:
            edit_schedule = get_object_or_404(Schedule, id=edit_schedule_id)
            # 수정 권한 검증
            if not edit_schedule.can_be_edited_by(current_user):
                from django.contrib import messages
                messages.error(request, '이 일정을 수정할 권한이 없습니다.')
                return redirect('scheduling:calendar')
        except:
            from django.contrib import messages
            messages.error(request, '존재하지 않는 일정입니다.')
            return redirect('scheduling:calendar')
    
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
        'managed_departments': managed_departments,
        'edit_schedule': edit_schedule
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
        
        # 부서와 담당자 일관성 검증 (최고관리자는 제외)
        if not request.user.is_superuser and assignee.department != department:
            return JsonResponse({'success': False, 'message': '선택한 담당자가 해당 부서에 속하지 않습니다.'})
        
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

@login_required
@csrf_exempt 
def update_schedule_api(request, schedule_id):
    """일정 수정 API"""
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'message': 'PUT 메서드만 허용됩니다.'})
    
    try:
        # 일정 조회
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 검증
        if not schedule.can_be_edited_by(request.user):
            return JsonResponse({'success': False, 'message': '이 일정을 수정할 권한이 없습니다.'})
        
        # 요청 데이터 파싱
        data = json.loads(request.body)
        
        # 필수 필드 검증
        required_fields = ['title', 'start_datetime', 'end_datetime']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field} 필드가 필요합니다.'})
        
        # 일시 파싱
        try:
            start_datetime = datetime.fromisoformat(data['start_datetime'])
            end_datetime = datetime.fromisoformat(data['end_datetime'])
            
            # timezone aware로 변경
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        except ValueError:
            return JsonResponse({'success': False, 'message': '잘못된 일시 형식입니다.'})
        
        # 일시 검증
        if end_datetime <= start_datetime:
            return JsonResponse({'success': False, 'message': '종료 일시는 시작 일시보다 늦어야 합니다.'})
        
        # 일정 수정
        schedule.title = data['title']
        schedule.description = data.get('description', '')
        schedule.location = data.get('location', '')
        schedule.start_datetime = start_datetime
        schedule.end_datetime = end_datetime
        schedule.priority = data.get('priority', 'normal')
        schedule.status = data.get('status', 'pending')
        schedule.updated_by = request.user
        schedule.save()
        
        return JsonResponse({
            'success': True,
            'message': '일정이 성공적으로 수정되었습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '잘못된 JSON 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'})

@login_required
@csrf_exempt
def delete_schedule_api(request, schedule_id):
    """일정 삭제 API"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'message': 'DELETE 메서드만 허용됩니다.'})
    
    try:
        # 일정 조회
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 검증
        if not schedule.can_be_deleted_by(request.user):
            return JsonResponse({'success': False, 'message': '이 일정을 삭제할 권한이 없습니다.'})
        
        # 일정 삭제
        schedule_title = schedule.title
        schedule.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'"{schedule_title}" 일정이 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'})

@login_required
def schedule_detail(request, schedule_id):
    """스케줄 상세 페이지"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    context = {
        'schedule': schedule,
    }
    return render(request, 'scheduling/schedule_detail.html', context)

def appointment_list(request):
    return render(request, 'scheduling/appointment_list.html')
