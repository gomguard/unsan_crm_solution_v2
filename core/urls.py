from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.data_upload, name='data_upload'),
    path('upload/start/', views.start_upload, name='start_upload'),
    path('template/<str:template_type>/', views.download_template, name='download_template'),
    path('upload/progress/<str:progress_key>/', views.upload_progress, name='upload_progress'),
]