from django.urls import path
from . import views

app_name = 'happycall'

urlpatterns = [
    path('', views.happycall_list, name='happycall_list'),
]