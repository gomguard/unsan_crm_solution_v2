#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unsan_crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from scheduling.models import Department, Schedule

User = get_user_model()

def add_early_schedule():
    """7시 시작하는 일찍 일정 추가"""
    
    # 보험영업팀 직원 중 한 명 선택
    user = User.objects.filter(department='insurance').first()
    if not user:
        print("보험영업팀 직원을 찾을 수 없습니다.")
        return
        
    department = Department.objects.get(name='insurance')
    
    # 내일 오전 7시 일정 생성
    tomorrow = datetime.now().date() + timedelta(days=1)
    start_datetime = datetime.combine(tomorrow, datetime.min.time().replace(hour=7, minute=0))
    end_datetime = start_datetime + timedelta(hours=2)  # 2시간 일정
    
    schedule = Schedule.objects.create(
        title='조기 고객 미팅',
        description='VIP 고객과의 조기 상담 약속',
        start_datetime=timezone.make_aware(start_datetime),
        end_datetime=timezone.make_aware(end_datetime),
        location='고객 사무실',
        creator=user,
        department=department,
        assignee=user,
        status='confirmed',
        priority='high'
    )
    
    print(f"7시 일정이 추가되었습니다: {schedule.title}")
    print(f"시간: {schedule.start_datetime} ~ {schedule.end_datetime}")
    print(f"담당자: {user.last_name}{user.first_name}")
    
    # 늦은 시간 일정도 추가 (23시)
    late_start = datetime.combine(tomorrow, datetime.min.time().replace(hour=23, minute=0))
    late_end = late_start + timedelta(hours=1)
    
    late_schedule = Schedule.objects.create(
        title='긴급 보험 처리',
        description='긴급한 보험금 처리 업무',
        start_datetime=timezone.make_aware(late_start),
        end_datetime=timezone.make_aware(late_end),
        location='본사 사무실',
        creator=user,
        department=department,
        assignee=user,
        status='pending',
        priority='urgent'
    )
    
    print(f"23시 일정도 추가되었습니다: {late_schedule.title}")

if __name__ == '__main__':
    add_early_schedule()