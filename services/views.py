from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
import re
from .models import ServiceType, ServiceRequest, ServiceHistory
from scheduling.models import Department
from happycall.models import HappyCall
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@login_required
def service_list(request):
    """서비스 요청 목록"""
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    service_type_filter = request.GET.get('service_type', 'all')
    search_query = request.GET.get('search', '').strip()
    page = request.GET.get('page', 1)
    
    # ServiceHistory와 함께 조회 (LEFT JOIN으로 없어도 가져옴)
    services = ServiceRequest.objects.select_related(
        'service_type', 'assigned_employee', 'created_by', 'servicehistory', 'customer', 'vehicle'
    ).all()
    
    # 검색 기능 추가
    if search_query:
        search_conditions = Q()
        
        # SR 코드로 검색 (SR12345, 12345 둘다 지원)
        if search_query.upper().startswith('SR'):
            # SR 제거 후 숫자 추출
            sr_number = re.sub(r'[^\d]', '', search_query)
            if sr_number:
                try:
                    service_id = int(sr_number)
                    search_conditions |= Q(id=service_id)
                except ValueError:
                    pass
        elif search_query.isdigit():
            # 숫자만 입력한 경우 (예: 12345)
            try:
                service_id = int(search_query)
                search_conditions |= Q(id=service_id)
            except ValueError:
                pass
        
        # 고객명, 전화번호, 차량번호로도 검색 (빈 값 제외)
        if search_query:  # 추가 보안: 빈 검색어 방지
            # 연결된 고객/차량 정보에서 검색
            search_conditions |= Q(customer__name__icontains=search_query)
            search_conditions |= Q(customer__phone__icontains=search_query) 
            search_conditions |= Q(vehicle__vehicle_number__icontains=search_query)
            # 임시 정보에서도 검색
            search_conditions |= Q(temp_customer_name__icontains=search_query)
            search_conditions |= Q(temp_customer_phone__icontains=search_query)
            search_conditions |= Q(temp_vehicle_number__icontains=search_query)
        
        services = services.filter(search_conditions)
    
    # 필터 적용
    if status_filter and status_filter != 'all':
        services = services.filter(status=status_filter)
        
    if priority_filter and priority_filter != 'all':
        services = services.filter(priority=priority_filter)
        
    if service_type_filter and service_type_filter != 'all':
        services = services.filter(service_type__category=service_type_filter)
    
    # 사용자별 권한 필터링
    if not request.user.is_superuser:
        # 본인이 생성했거나 담당인 서비스만
        services = services.filter(
            Q(created_by=request.user) | Q(assigned_employee=request.user)
        )
    
    # 최신순 정렬
    services = services.order_by('-created_at')
    
    # 통계 계산 (페이지네이션 전 전체 데이터) - 성능 최적화
    from django.db.models import Count, Case, When, IntegerField
    
    stats = services.aggregate(
        total_count=Count('id'),
        pending_count=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
        scheduled_count=Count(Case(When(status='scheduled', then=1), output_field=IntegerField())),
        completed_count=Count(Case(When(status='completed', then=1), output_field=IntegerField()))
    )
    
    total_count = stats['total_count']
    pending_count = stats['pending_count']
    scheduled_count = stats['scheduled_count']
    completed_count = stats['completed_count']
    
    # 페이지네이션
    paginator = Paginator(services, 10)  # 한 페이지에 10개씩
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    return render(request, 'services/service_list.html', {
        'services': page_obj,
        'status_choices': ServiceRequest.STATUS_CHOICES,
        'priority_choices': ServiceRequest.PRIORITY_CHOICES,
        'current_status': status_filter,
        'current_priority': priority_filter,
        'current_service_type': service_type_filter,
        'search_query': search_query,
        'page_obj': page_obj,
        'total_count': total_count,
        'pending_count': pending_count,
        'scheduled_count': scheduled_count,
        'completed_count': completed_count
    })

@login_required
def service_detail(request, service_id):
    """서비스 요청 상세"""
    service = get_object_or_404(ServiceRequest, id=service_id)
    
    # 권한 검증
    if not request.user.is_superuser and service.created_by != request.user and service.assigned_employee != request.user:
        messages.error(request, '이 서비스 요청을 볼 권한이 없습니다.')
        return redirect('services:service_list')
    
    # 서비스 히스토리 조회
    try:
        history = ServiceHistory.objects.get(service_request=service)
    except ServiceHistory.DoesNotExist:
        history = None
    
    return render(request, 'services/service_detail.html', {
        'service': service,
        'history': history
    })

@login_required
def service_create(request):
    """서비스 요청 생성"""
    service_types = ServiceType.objects.filter(is_active=True).select_related('department')
    employees = User.objects.filter(user_type__in=['employee', 'admin']).select_related('department')
    
    # customer_id가 파라미터로 전달된 경우 해당 고객 정보를 가져와서 초기값으로 설정
    preselected_customer = None
    customer_id = request.GET.get('customer_id')
    if customer_id:
        try:
            from customers.models import Customer
            preselected_customer = Customer.objects.get(id=customer_id)
        except (Customer.DoesNotExist, ValueError):
            preselected_customer = None
    
    return render(request, 'services/service_create.html', {
        'service_types': service_types,
        'employees': employees,
        'status_choices': ServiceRequest.STATUS_CHOICES,
        'priority_choices': ServiceRequest.PRIORITY_CHOICES,
        'preselected_customer': preselected_customer,
    })

@login_required
def service_edit(request, service_id):
    """서비스 요청 수정"""
    service = get_object_or_404(ServiceRequest, id=service_id)
    
    if request.method == 'POST':
        try:
            # POST 데이터 처리
            service_type_id = request.POST.get('service_type')
            if service_type_id:
                service.service_type = get_object_or_404(ServiceType, id=service_type_id)
            
            service.service_detail = request.POST.get('service_detail', '')
            service.description = request.POST.get('description', '')
            service.status = request.POST.get('status', service.status)
            service.priority = request.POST.get('priority', service.priority)
            
            # 예상 가격
            estimated_price = request.POST.get('estimated_price')
            if estimated_price:
                try:
                    service.estimated_price = float(estimated_price)
                except ValueError:
                    service.estimated_price = None
            
            # 희망 일시
            requested_date = request.POST.get('requested_date')
            if requested_date:
                try:
                    from datetime import datetime
                    service.requested_date = datetime.fromisoformat(requested_date)
                except ValueError:
                    pass
            
            # 확정 일시
            scheduled_date = request.POST.get('scheduled_date')
            if scheduled_date:
                try:
                    from datetime import datetime
                    service.scheduled_date = datetime.fromisoformat(scheduled_date)
                except ValueError:
                    pass
            
            # 담당자
            assigned_employee_id = request.POST.get('assigned_employee')
            if assigned_employee_id:
                try:
                    service.assigned_employee = User.objects.get(id=assigned_employee_id)
                except User.DoesNotExist:
                    pass
            elif assigned_employee_id == '':
                service.assigned_employee = None
            
            service.save()
            messages.success(request, '서비스 요청이 성공적으로 수정되었습니다.')
            return redirect('services:service_detail', service_id=service.id)
            
        except Exception as e:
            messages.error(request, f'서비스 수정 중 오류가 발생했습니다: {str(e)}')
    
    # GET 요청 시 수정 폼 표시
    service_types = ServiceType.objects.filter(is_active=True).select_related('department')
    
    # 부서 목록
    from scheduling.models import Department
    departments = Department.objects.filter(is_active=True).order_by('display_name')
    
    # 활성 직원 목록 (Employee 모델 사용)
    try:
        from employees.models import Employee
        employees = Employee.objects.filter(status='active').select_related('user', 'department')
    except ImportError:
        # Employee 모델이 없는 경우 fallback
        employees = []
    
    # 빠른 입력 버튼 조회
    from .models import ServiceQuickButton
    quick_buttons = ServiceQuickButton.objects.filter(
        service_type=service.service_type,
        is_active=True
    ).order_by('display_order', 'button_text')
    
    return render(request, 'services/service_edit.html', {
        'service': service,
        'service_types': service_types,
        'departments': departments,
        'employees': employees,
        'quick_buttons': quick_buttons,
        'status_choices': ServiceRequest.STATUS_CHOICES,
        'priority_choices': ServiceRequest.PRIORITY_CHOICES,
    })

@login_required
def get_quick_buttons_api(request):
    """서비스 유형별 빠른 입력 버튼 API"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'GET 메서드만 허용됩니다.'})
    
    service_type_id = request.GET.get('service_type_id')
    if not service_type_id:
        return JsonResponse({'success': False, 'message': '서비스 유형 ID가 필요합니다.'})
    
    try:
        from .models import ServiceQuickButton
        quick_buttons = ServiceQuickButton.objects.filter(
            service_type_id=service_type_id,
            is_active=True
        ).order_by('display_order', 'button_text')
        
        buttons_data = [{
            'id': btn.id,
            'button_text': btn.button_text,
            'service_content': btn.service_content
        } for btn in quick_buttons]
        
        return JsonResponse({
            'success': True,
            'buttons': buttons_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        })

@login_required
def customer_search_api(request):
    """고객 검색 API"""
    print(f"DEBUG: customer_search_api 호출됨 - query: {request.GET.get('q')}, method: {request.method}")
    
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'GET 메서드만 허용됩니다.'})
    
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # phone, vehicle, name, all
    
    print(f"DEBUG: 검색어='{query}', 타입='{search_type}', 길이={len(query)}")
    
    if len(query) < 2:
        print("DEBUG: 검색어가 2글자 미만이라 빈 결과 반환")
        return JsonResponse({'success': True, 'customers': []})
    
    try:
        from customers.models import Customer, Vehicle
        from django.db.models import Q
        
        results = []
        
        # 실제 고객 DB에서 검색
        customer_query = Q()
        vehicle_query = Q()
        
        # 이름으로 검색
        if search_type in ['name', 'all']:
            customer_query |= Q(name__icontains=query)
        
        # 전화번호로 검색
        if search_type in ['phone', 'all']:
            normalized_query = query.replace('-', '').replace(' ', '')
            if len(normalized_query) >= 4:  # 최소 4자리
                customer_query |= Q(phone__icontains=normalized_query)
        
        # 차량번호로 검색
        if search_type in ['vehicle', 'all']:
            vehicle_query |= Q(vehicle_number__icontains=query)
        
        # 고객 검색 결과
        if customer_query:
            customers = Customer.objects.filter(customer_query).prefetch_related('vehicle_ownerships__vehicle')[:10]
            for customer in customers:
                vehicles = [ownership.vehicle for ownership in customer.vehicle_ownerships.all()]
                for vehicle in vehicles[:3]:  # 고객당 최대 3대 차량
                    results.append({
                        'customer_id': customer.id,
                        'customer_name': customer.name,
                        'customer_phone': customer.phone,
                        'customer_city': customer.address_main.split()[0] if customer.address_main else '',
                        'customer_district': customer.address_main.split()[1] if customer.address_main and len(customer.address_main.split()) > 1 else '',
                        'customer_dong': '',
                        'vehicle_id': vehicle.id if vehicle else None,
                        'vehicle_number': vehicle.vehicle_number if vehicle else '',
                        'vehicle_model': vehicle.model if vehicle else '',
                        'vehicle_year': vehicle.year if vehicle else None,
                    })
                if not vehicles:  # 차량이 없는 고객
                    results.append({
                        'customer_id': customer.id,
                        'customer_name': customer.name,
                        'customer_phone': customer.phone,
                        'customer_city': customer.address_main.split()[0] if customer.address_main else '',
                        'customer_district': customer.address_main.split()[1] if customer.address_main and len(customer.address_main.split()) > 1 else '',
                        'customer_dong': '',
                        'vehicle_id': None,
                        'vehicle_number': '',
                        'vehicle_model': '',
                        'vehicle_year': None,
                    })
        
        # 차량 검색 결과 (고객 정보 포함)
        if vehicle_query:
            vehicles = Vehicle.objects.filter(vehicle_query).prefetch_related('ownerships__customer')[:10]
            for vehicle in vehicles:
                current_ownership = vehicle.ownerships.filter(end_date__isnull=True).first()
                customer = current_ownership.customer if current_ownership else None
                
                # 이미 추가된 결과가 아닌 경우에만 추가
                if not any(r['vehicle_id'] == vehicle.id for r in results):
                    results.append({
                        'customer_id': customer.id if customer else None,
                        'customer_name': customer.name if customer else '미확인',
                        'customer_phone': customer.phone if customer else '',
                        'customer_city': customer.address_main.split()[0] if customer and customer.address_main else '',
                        'customer_district': customer.address_main.split()[1] if customer and customer.address_main and len(customer.address_main.split()) > 1 else '',
                        'customer_dong': customer.address_main.split()[2] if customer and customer.address_main and len(customer.address_main.split()) > 2 else '',
                        'vehicle_id': vehicle.id,
                        'vehicle_number': vehicle.vehicle_number,
                        'vehicle_model': vehicle.model,
                        'vehicle_year': vehicle.year,
                    })
        
        print(f"DEBUG: 검색 결과 {len(results)}개")
        return JsonResponse({'success': True, 'customers': results})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'검색 중 오류가 발생했습니다: {str(e)}'})

@login_required
@csrf_exempt
def update_service_status(request, service_id):
    """서비스 상태 업데이트 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST 메서드만 허용됩니다.'})
    
    try:
        service = get_object_or_404(ServiceRequest, id=service_id)
        
        # 권한 검증
        if not request.user.is_superuser and service.created_by != request.user and service.assigned_employee != request.user:
            return JsonResponse({'success': False, 'message': '이 서비스를 수정할 권한이 없습니다.'})
        
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in [choice[0] for choice in ServiceRequest.STATUS_CHOICES]:
            return JsonResponse({'success': False, 'message': '잘못된 상태값입니다.'})
        
        service.status = new_status
        service.save()
        
        return JsonResponse({
            'success': True,
            'message': f'상태가 {service.get_status_display()}으로 변경되었습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '잘못된 JSON 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

@login_required
@csrf_exempt  
def complete_service(request, service_id):
    """서비스 완료 처리 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST 메서드만 허용됩니다.'})
    
    try:
        service = get_object_or_404(ServiceRequest, id=service_id)
        
        # 권한 검증
        if not request.user.is_superuser and service.created_by != request.user and service.assigned_employee != request.user:
            return JsonResponse({'success': False, 'message': '이 서비스를 완료 처리할 권한이 없습니다.'})
        
        data = json.loads(request.body)
        
        # 서비스 상태를 완료로 변경
        service.status = 'completed'
        
        # 새 주행거리가 있으면 차량 정보 업데이트
        new_mileage = data.get('new_mileage')
        if new_mileage:
            try:
                service.vehicle_mileage = int(new_mileage)
            except (ValueError, TypeError):
                pass
        
        service.save()
        
        # ServiceHistory 생성 또는 업데이트
        history, created = ServiceHistory.objects.get_or_create(
            service_request=service,
            defaults={}
        )
        
        # 작업 시간 처리
        if data.get('actual_start_time'):
            from datetime import datetime
            try:
                history.actual_start_time = datetime.fromisoformat(data['actual_start_time'].replace('T', ' '))
            except ValueError:
                pass
                
        if data.get('actual_end_time'):
            try:
                history.actual_end_time = datetime.fromisoformat(data['actual_end_time'].replace('T', ' '))
            except ValueError:
                pass
        
        # 기타 정보 업데이트
        if data.get('actual_price'):
            try:
                history.actual_price = int(data['actual_price'])
            except (ValueError, TypeError):
                pass
        
        if data.get('work_summary'):
            history.work_summary = data['work_summary']
            
        if data.get('parts_used'):
            history.parts_used = data['parts_used']
            
        if data.get('satisfaction_score'):
            try:
                score = int(data['satisfaction_score'])
                if 1 <= score <= 5:
                    history.satisfaction_score = score
            except (ValueError, TypeError):
                pass
        
        if data.get('customer_feedback'):
            history.customer_feedback = data['customer_feedback']
            
        if data.get('next_service_date'):
            try:
                from datetime import datetime
                history.next_service_date = datetime.strptime(data['next_service_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if data.get('next_service_notes'):
            history.next_service_notes = data['next_service_notes']
        
        history.save()
        
        # Task 3.2: 서비스 완료 시 해피콜 1차 생성 → 팀장 승인 대기 상태로 생성
        try:
            # 이미 해피콜이 생성되었는지 확인
            existing_happycall = HappyCall.objects.filter(service_request=service).first()
            
            if not existing_happycall:
                # 해피콜 생성 (1차콜 승인 대기 상태)
                happycall = HappyCall.objects.create(
                    service_request=service,
                    call_stage='1st_pending_approval',  # 팀장 승인 대기 상태
                    status='pending_approval',
                    first_call_scheduled_date=timezone.now().date() + timedelta(days=7),  # 7일 후 예정
                    created_by=request.user,
                    notes=f'서비스 완료 ({service.get_status_display()})에 따른 자동 생성',
                    # 매출 관련 기본 정보 설정
                    total_revenue_generated=0,
                    revenue_count=0
                )
                
                messages.success(request, 
                    f'서비스가 완료되었습니다. 해피콜이 생성되어 팀장 승인을 기다리고 있습니다. (해피콜 ID: {happycall.id})')
            
        except Exception as happycall_error:
            # 해피콜 생성 실패해도 서비스 완료는 처리됨
            messages.warning(request, 
                f'서비스는 완료되었지만 해피콜 생성 중 오류가 발생했습니다: {str(happycall_error)}')
        
        return JsonResponse({
            'success': True,
            'message': '서비스가 성공적으로 완료 처리되었습니다. 해피콜이 생성되어 승인을 기다리고 있습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '잘못된 JSON 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'완료 처리 중 오류가 발생했습니다: {str(e)}'})

@login_required
@csrf_exempt
def service_create_api(request):
    """서비스 요청 생성 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST 메서드만 허용됩니다.'})
    
    try:
        data = json.loads(request.body)
        
        # 필수 필드 검증
        required_fields = ['customer_phone', 'service_category']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field} 필드가 필요합니다.'})
        
        # 서비스 카테고리에 맞는 기본 서비스 타입 찾기 또는 생성
        service_category = data['service_category']
        try:
            service_type = ServiceType.objects.filter(category=service_category).first()
            if not service_type:
                # 기본 서비스 타입이 없으면 생성
                from scheduling.models import Department
                default_dept = Department.objects.first()  # 기본 부서
                service_type = ServiceType.objects.create(
                    name=dict(ServiceType.SERVICE_CATEGORIES)[service_category],
                    category=service_category,
                    department=default_dept
                )
        except Exception:
            return JsonResponse({'success': False, 'message': '서비스 타입 처리 중 오류가 발생했습니다.'})
        
        # 담당자 조회 (선택사항)
        assigned_employee = None
        if data.get('assigned_employee'):
            try:
                assigned_employee = User.objects.get(id=data['assigned_employee'])
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': '존재하지 않는 담당자입니다.'})
        
        # 예약 일시 처리
        requested_date = None
        if data.get('requested_date'):
            try:
                from datetime import datetime
                requested_date = datetime.fromisoformat(data['requested_date'].replace('T', ' '))
            except ValueError:
                pass
        
        # 서비스 요청 생성
        service_request = ServiceRequest.objects.create(
            temp_customer_name=data.get('customer_name') or '미확인',
            temp_customer_phone=data['customer_phone'],
            temp_customer_city=data.get('customer_city', ''),
            temp_customer_district=data.get('customer_district', ''),
            temp_customer_dong=data.get('customer_dong', ''),
            temp_vehicle_number=data.get('vehicle_number', ''),
            temp_vehicle_model=data.get('vehicle_model', ''),
            temp_vehicle_year=data.get('vehicle_year') if data.get('vehicle_year') else None,
            temp_vehicle_mileage=data.get('vehicle_mileage') if data.get('vehicle_mileage') else None,
            last_inspection_date=data.get('last_inspection_date') if data.get('last_inspection_date') else None,
            next_inspection_date=data.get('next_inspection_date') if data.get('next_inspection_date') else None,
            inspection_notes=data.get('inspection_notes', ''),
            service_type=service_type,
            service_detail=data.get('service_detail', ''),
            description=data.get('description', ''),
            estimated_price=data.get('estimated_price') if data.get('estimated_price') else None,
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'normal'),
            requested_date=requested_date,
            assigned_employee=assigned_employee,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': '서비스 요청이 성공적으로 생성되었습니다.',
            'service_id': service_request.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '잘못된 JSON 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'})
