from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('api/events/', views.get_events, name='api_events'),
    path('add/', views.add_schedule_view, name='add_schedule_view'),
    path('api/add/', views.add_schedule_api, name='add_schedule'),
    path('appointments/', views.appointment_list, name='appointment_list'),
]