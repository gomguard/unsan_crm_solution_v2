#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unsan_crm.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def update_admin_user():
    """admin 사용자 정보 업데이트"""
    
    try:
        user = User.objects.get(username='admin')
        user.first_name = '관리'
        user.last_name = '시스템'
        user.position = '시스템관리자'
        user.department = 'admin'
        user.email = 'admin@unsan.co.kr'
        user.save()
        
        print(f"admin 사용자 정보 업데이트 완료: {user.last_name}{user.first_name} ({user.username})")
        print(f"부서: {user.department}, 직책: {user.position}")
        
    except User.DoesNotExist:
        print("admin 사용자가 존재하지 않습니다.")

if __name__ == '__main__':
    update_admin_user()