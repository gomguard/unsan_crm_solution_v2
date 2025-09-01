#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unsan_crm.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin_user():
    """admin 사용자 생성"""
    
    username = 'admin'
    
    # 이미 존재하는 사용자인지 확인
    if User.objects.filter(username=username).exists():
        print(f"사용자 {username}는 이미 존재합니다.")
        return
    
    user = User.objects.create_user(
        username=username,
        first_name='관리',
        last_name='시스템',
        email='admin@unsan.co.kr',
        password='admin123',
        user_type='admin',
        department='admin',
        position='시스템관리자',
        hire_date=date.today(),
        phone='010-0000-0000',
        is_superuser=True,
        is_staff=True,
    )
    
    print(f"관리자 사용자 생성 완료: {user.last_name}{user.first_name} ({user.username})")
    print("로그인 정보:")
    print(f"- 사용자명: {username}")
    print("- 비밀번호: admin123")

if __name__ == '__main__':
    create_admin_user()