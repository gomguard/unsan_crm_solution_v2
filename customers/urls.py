from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # 고객 목록
    path('', views.CustomerListView.as_view(), name='customer_list'),
    
    # 고객 상세
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    
    # 고객 생성
    path('create/', views.CustomerCreateView.as_view(), name='customer_create'),
    
    # 고객 수정
    path('<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    
    # 고객 삭제
    path('<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    
    # 고객 검색 (AJAX)
    path('search/', views.customer_search, name='customer_search'),
    
    # 고객 상태 토글
    path('<int:pk>/toggle-active/', views.toggle_customer_active, name='toggle_customer_active'),
]