from django.urls import path
from . import views

app_name = 'happycall'

urlpatterns = [
    path('', views.my_happycalls, name='my_happycalls'),  # 내 할일
    path('list/', views.happycall_list, name='list'),  # 전체 목록
    path('dashboard/', views.my_happycalls, name='dashboard'),  # dashboard alias
    path('manager/', views.manager_dashboard, name='manager_dashboard'),  # 팀장 대시보드
    path('staff/<int:user_id>/', views.staff_detail, name='staff_detail'),  # 담당자별 상세 통계
    path('assign/', views.happycall_assign, name='assign'),  # 해피콜 일괄 생성
    path('<int:pk>/', views.happycall_detail, name='detail'),  # 해피콜 상세보기
    path('<int:pk>/execute/', views.happycall_execute, name='execute'),  # 해피콜 수행
    path('<int:pk>/update/', views.happycall_update, name='update'),  # 해피콜 수정
    path('<int:pk>/callback/', views.happycall_create_callback, name='create_callback'),  # 재연락 생성
    path('<int:pk>/revenue/', views.happycall_revenue_create, name='revenue_create'),  # 매출 등록
    path('<int:pk>/unified-call/', views.happycall_unified_call, name='unified_call'),  # 통합 해피콜 수행
]