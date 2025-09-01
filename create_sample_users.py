#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta
from django.utils import timezone

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unsan_crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from scheduling.models import Department

User = get_user_model()

def create_sample_users():
    """샘플 사용자와 부서 데이터 생성"""
    
    # 기존 부서 데이터 생성
    departments = [
        {'name': 'admin', 'display_name': '관리부서'},
        {'name': 'engine_oil', 'display_name': '엔진오일팀'},
        {'name': 'happycall', 'display_name': '해피콜팀'},
        {'name': 'insurance', 'display_name': '보험영업팀'},
    ]
    
    for dept_data in departments:
        department, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults={'display_name': dept_data['display_name']}
        )
        if created:
            print(f"부서 생성: {department.display_name}")
    
    # 샘플 사용자 데이터
    users_data = [
        # 관리부서 (2명)
        {'username': 'ceo', 'first_name': '김', 'last_name': '대표', 'department': 'admin', 'position': '대표이사', 'is_superuser': True},
        {'username': 'manager', 'first_name': '이', 'last_name': '관리', 'department': 'admin', 'position': '관리팀장'},
        
        # 엔진오일팀 (3명)
        {'username': 'oil_manager', 'first_name': '박', 'last_name': '오일', 'department': 'engine_oil', 'position': '엔진오일팀장'},
        {'username': 'oil_tech1', 'first_name': '최', 'last_name': '기술', 'department': 'engine_oil', 'position': '정비기사'},
        {'username': 'oil_tech2', 'first_name': '장', 'last_name': '숙련', 'department': 'engine_oil', 'position': '정비기사'},
        
        # 해피콜팀 (6명)
        {'username': 'call_manager', 'first_name': '정', 'last_name': '콜센터', 'department': 'happycall', 'position': '해피콜팀장'},
        {'username': 'call_staff1', 'first_name': '강', 'last_name': '친절', 'department': 'happycall', 'position': '상담원'},
        {'username': 'call_staff2', 'first_name': '윤', 'last_name': '상담', 'department': 'happycall', 'position': '상담원'},
        {'username': 'call_staff3', 'first_name': '임', 'last_name': '안내', 'department': 'happycall', 'position': '상담원'},
        {'username': 'call_staff4', 'first_name': '한', 'last_name': '응대', 'department': 'happycall', 'position': '상담원'},
        {'username': 'call_staff5', 'first_name': '오', 'last_name': '서비스', 'department': 'happycall', 'position': '상담원'},
        
        # 보험영업팀 (9명)
        {'username': 'ins_manager', 'first_name': '송', 'last_name': '영업', 'department': 'insurance', 'position': '보험영업팀장'},
        {'username': 'ins_sales1', 'first_name': '문', 'last_name': '성과', 'department': 'insurance', 'position': '영업팀원'},
        {'username': 'ins_sales2', 'first_name': '신', 'last_name': '실적', 'department': 'insurance', 'position': '영업팀원'},
        {'username': 'ins_sales3', 'first_name': '조', 'last_name': '달성', 'department': 'insurance', 'position': '영업팀원'},
        {'username': 'ins_sales4', 'first_name': '허', 'last_name': '계약', 'department': 'insurance', 'position': '영업팀원'},
        {'username': 'ins_sales5', 'first_name': '남', 'last_name': '신규', 'department': 'insurance', 'position': '영업팀원'},
        {'username': 'ins_sales6', 'first_name': '고', 'last_name': '확장', 'department': 'insurance', 'position': '영업팀원'},
        {'username': 'ins_sales7', 'first_name': '배', 'last_name': '개발', 'department': 'insurance', 'position': '영업팀원'},
        {'username': 'ins_sales8', 'first_name': '서', 'last_name': '마케팅', 'department': 'insurance', 'position': '영업팀원'},
    ]
    
    created_count = 0
    
    for user_data in users_data:
        username = user_data['username']
        
        # 이미 존재하는 사용자인지 확인
        if User.objects.filter(username=username).exists():
            print(f"사용자 {username}는 이미 존재합니다.")
            continue
            
        # 입사일을 랜덤하게 설정 (최근 2년 내)
        hire_date = date.today() - timedelta(days=timezone.now().day % 730)
        
        # 부서 객체 찾기
        try:
            department_obj = Department.objects.get(name=user_data['department'])
        except Department.DoesNotExist:
            print(f"부서 '{user_data['department']}'를 찾을 수 없습니다. 사용자 {username} 생성을 건너뜁니다.")
            continue
        
        user = User.objects.create_user(
            username=username,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=f"{username}@unsan.co.kr",
            password='unsan1234',  # 임시 비밀번호
            user_type='admin' if user_data.get('is_superuser') else 'employee',
            department=department_obj,  # Department 객체로 할당
            position=user_data['position'],
            hire_date=hire_date,
            phone=f"010-{1000 + created_count:04d}-{5678}",
            is_superuser=user_data.get('is_superuser', False),
            is_staff=user_data.get('is_superuser', False),
        )
        
        # 부서 관리자 설정
        if 'manager' in user_data['position'] or '팀장' in user_data['position'] or '대표' in user_data['position']:
            try:
                department = Department.objects.get(name=user_data['department'])
                if not department.manager:  # 이미 관리자가 설정되지 않은 경우만
                    department.manager = user
                    department.save()
                    print(f"{department.display_name} 관리자로 {user.last_name}{user.first_name} 설정")
            except Department.DoesNotExist:
                pass
        
        created_count += 1
        print(f"사용자 생성: {user.last_name}{user.first_name} ({user.username}) - {user.position}")
    
    print(f"\n총 {created_count}명의 사용자가 생성되었습니다.")
    print("\n부서별 인원:")
    for dept in Department.objects.all():
        count = User.objects.filter(department=dept).count()
        manager_name = f" (관리자: {dept.manager.last_name}{dept.manager.first_name})" if dept.manager else ""
        print(f"- {dept.display_name}: {count}명{manager_name}")
    
    print("\n로그인 정보:")
    print("- 사용자명: 위에서 생성된 username")
    print("- 비밀번호: unsan1234")
    print("- 예시: ceo / unsan1234")

if __name__ == '__main__':
    create_sample_users()