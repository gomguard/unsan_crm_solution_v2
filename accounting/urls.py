from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    # 회계 메인 대시보드
    path('', views.AccountingDashboardView.as_view(), name='dashboard'),
    
    # 매입 관리
    path('purchases/', views.PurchaseVoucherListView.as_view(), name='purchase_list'),
    path('purchases/create/', views.PurchaseVoucherCreateView.as_view(), name='purchase_create'),
    path('purchases/<int:pk>/', views.PurchaseVoucherDetailView.as_view(), name='purchase_detail'),
    path('purchases/<int:pk>/edit/', views.PurchaseVoucherUpdateView.as_view(), name='purchase_edit'),
    
    # 매출 관리
    path('sales/', views.SalesVoucherListView.as_view(), name='sales_list'),
    path('sales/create/', views.SalesVoucherCreateView.as_view(), name='sales_create'),
    path('sales/<int:pk>/', views.SalesVoucherDetailView.as_view(), name='sales_detail'),
    path('sales/<int:pk>/edit/', views.SalesVoucherUpdateView.as_view(), name='sales_edit'),
    
    # 공급업체 관리
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
    
    # 재무제표
    path('reports/income-statement/', views.IncomeStatementView.as_view(), name='income_statement'),
    path('reports/balance-sheet/', views.BalanceSheetView.as_view(), name='balance_sheet'),
    
    # 계정과목 관리
    path('accounts/', views.AccountingCategoryListView.as_view(), name='account_list'),
    path('accounts/create/', views.AccountingCategoryCreateView.as_view(), name='account_create'),
]