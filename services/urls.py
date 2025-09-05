from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_list, name='service_list'),
    path('create/', views.service_create, name='service_create'),
    path('create/api/', views.service_create_api, name='service_create_api'),
    path('customer-search/', views.customer_search_api, name='customer_search_api'),
    path('quick-buttons/', views.get_quick_buttons_api, name='get_quick_buttons_api'),
    path('<int:service_id>/', views.service_detail, name='service_detail'),
    path('<int:service_id>/edit/', views.service_edit, name='service_edit'),
    path('<int:service_id>/update-status/', views.update_service_status, name='update_service_status'),
    path('<int:service_id>/complete/', views.complete_service, name='complete_service'),
]