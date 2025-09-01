#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unsan_crm.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def check_users():
    """모든 사용자 확인"""
    
    print("=== 전체 사용자 목록 ===")
    users = User.objects.all().order_by('department', 'position')
    
    for user in users:
        print(f"사용자명: {user.username:15} | 이름: {user.last_name}{user.first_name:8} | 부서: {user.department:12} | 직책: {user.position:12} | 관리자: {'Yes' if user.is_superuser else 'No'}")
    
    print(f"\n총 {users.count()}명")
    
    # 부서별 통계
    print("\n=== 부서별 인원 ===")
    departments = ['admin', 'engine_oil', 'happycall', 'insurance']
    for dept in departments:
        count = User.objects.filter(department=dept).count()
        dept_users = User.objects.filter(department=dept)
        if dept_users.exists():
            print(f"{dept}: {count}명")
            for user in dept_users:
                print(f"  - {user.username} ({user.last_name}{user.first_name}, {user.position})")

if __name__ == '__main__':
    check_users()