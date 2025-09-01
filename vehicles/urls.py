from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
]