#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone
import random

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unsan_crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from scheduling.models import Department, Schedule

User = get_user_model()

def create_sample_schedules():
    """샘플 일정 데이터 생성 - 9월 전체 월 분량"""
    
    # 모든 부서와 직원 가져오기
    departments = {dept.name: dept for dept in Department.objects.all()}
    users = list(User.objects.filter(user_type__in=['employee', 'admin']))
    
    if not users:
        print("사용자가 없습니다. 먼저 create_sample_users.py를 실행해주세요.")
        return
    
    # 일정 템플릿 데이터
    schedule_templates = {
        'admin': [
            {'title': '월례 경영진 회의', 'description': '월간 실적 검토 및 향후 계획 논의'},
            {'title': '전직원 교육', 'description': '안전교육 및 서비스 품질 향상 교육'},
            {'title': '예산 검토 회의', 'description': '월간 예산 사용 현황 점검'},
        ],
        'engine_oil': [
            {'title': '정기점검 서비스', 'description': '고객 차량 엔진오일 교환'},
            {'title': '긴급 수리', 'description': '엔진 관련 긴급 수리 요청'},
            {'title': '부품 재고 점검', 'description': '오일 필터 및 부품 재고 확인'},
            {'title': '고객 방문 서비스', 'description': '출장 엔진오일 교환'},
        ],
        'happycall': [
            {'title': '고객 만족도 조사', 'description': '서비스 이용 후 만족도 확인'},
            {'title': '신규 고객 상담', 'description': '신규 고객 서비스 안내'},
            {'title': '불만 처리', 'description': '고객 불만사항 접수 및 해결'},
            {'title': '예약 확인 콜', 'description': '서비스 예약 확인'},
            {'title': '이벤트 안내', 'description': '할인 이벤트 안내'},
        ],
        'insurance': [
            {'title': '보험 상품 설명', 'description': '고객 맞춤 보험 상품 상담'},
            {'title': '계약 체결', 'description': '보험 계약 체결'},
            {'title': '고객 방문', 'description': '기존 고객 방문 상담'},
            {'title': '팀 미팅', 'description': '월간 실적 점검'},
        ]
    }
    
    created_count = 0
    target_count = 120  # 9월 전체 월에 120개 일정
    
    # 2025년 9월 전체
    start_date = datetime(2025, 9, 1).date()
    end_date = datetime(2025, 9, 30).date()
    
    print(f"일정 생성 기간: {start_date} ~ {end_date}")
    
    # 120개의 일정을 9월 30일에 고르게 분배
    for i in range(target_count):
        # 랜덤 사용자 선택
        user = random.choice(users)
        user_dept = user.department
        
        if user_dept not in schedule_templates:
            continue
            
        try:
            department_obj = departments[user_dept]
        except KeyError:
            continue
        
        # 랜덤한 일정 템플릿 선택
        template = random.choice(schedule_templates[user_dept])
        
        # 9월 1일부터 30일까지 랜덤하게 분배 (평일에 더 많이)
        days_in_september = (end_date - start_date).days + 1
        random_day_offset = random.randint(0, days_in_september - 1)
        schedule_date = start_date + timedelta(days=random_day_offset)
        
        # 주말인지 평일인지 확인 (월요일=0, 일요일=6)
        weekday = schedule_date.weekday()
        
        # 시간 설정 (9시-17시, 주말은 10시-15시)
        if weekday < 5:  # 평일 (월-금)
            hour = random.randint(9, 17)
        else:  # 주말 (토-일)
            hour = random.randint(10, 15)
        
        minute = random.choice([0, 30])
        
        # 일정 시작 시간
        start_datetime = datetime.combine(schedule_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        # 일정 길이 (30분-3시간)
        duration_hours = random.choice([0.5, 1, 1.5, 2, 3])
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        
        # 상태와 우선순위 설정
        status = random.choices(
            ['pending', 'confirmed', 'completed'],
            weights=[30, 50, 20]
        )[0]
        
        priority = random.choices(
            ['low', 'normal', 'high'],
            weights=[30, 60, 10]
        )[0]
        
        # 장소 설정
        locations = ['본사 회의실', '고객 현장', '서비스센터', '1층 상담실', '정비동', '사무실']
        location = random.choice(locations)
        
        # 일정 생성
        schedule = Schedule.objects.create(
            title=template['title'],
            description=template['description'],
            start_datetime=timezone.make_aware(start_datetime),
            end_datetime=timezone.make_aware(end_datetime),
            location=location,
            creator=user,
            department=department_obj,
            assignee=user,
            status=status,
            priority=priority,
            is_confirmed_by_assignee=(status in ['confirmed', 'completed'])
        )
        
        created_count += 1
    
    print(f"총 {created_count}개의 샘플 일정이 생성되었습니다.")
    
    # 부서별 일정 개수 출력
    print("\n부서별 일정 개수:")
    for dept_name, dept_obj in departments.items():
        count = Schedule.objects.filter(department=dept_obj).count()
        print(f"- {dept_obj.display_name}: {count}개")
    
    print("\n상태별 일정 개수:")
    for status, display in Schedule.STATUS_CHOICES:
        count = Schedule.objects.filter(status=status).count()
        print(f"- {display}: {count}개")

if __name__ == '__main__':
    create_sample_schedules()