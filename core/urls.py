from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.data_upload, name='data_upload'),
    path('template/<str:template_type>/', views.download_template, name='download_template'),
]