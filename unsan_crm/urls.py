"""
URL configuration for unsan_crm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.conf import settings

def redirect_to_login(request):
    return HttpResponseRedirect('/accounts/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('customers/', include('customers.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('services/', include('services.urls')),
    path('scheduling/', include('scheduling.urls')),
    path('inventory/', include('inventory.urls')),
    path('accounting/', include('accounting.urls')),
    path('employees/', include('employees.urls')),
    path('happycall/', include('happycall.urls')),
    path('dashboard/', include('core.urls')),
    path('', redirect_to_login),  # 루트 URL을 로그인으로 리다이렉트
]

# Django browser reload (개발 환경에서만)
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
