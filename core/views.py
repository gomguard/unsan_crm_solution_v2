from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    """
    메인 대시보드 페이지
    향후 사용자 역할에 따라 다른 대시보드를 보여줄 예정:
    - 총관리자: 전체 현황 대시보드
    - 콜직원: 해피콜 및 고객 상담 대시보드  
    - 검사접수직원: 차량 검사 및 접수 대시보드
    - 일반직원: 기본 업무 대시보드
    """
    user = request.user
    
    context = {
        'user': user,
        'is_superuser': user.is_superuser,
        'user_groups': user.groups.all(),
    }
    
    return render(request, 'core/dashboard.html', context)
