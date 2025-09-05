from django.contrib import admin
from .models import (
    AccountingCategory, Supplier, PurchaseVoucher, PurchaseVoucherItem,
    SalesVoucher, SalesVoucherItem, JournalEntry, JournalEntryLine
)

@admin.register(AccountingCategory)
class AccountingCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category_type', 'parent', 'is_active']
    list_filter = ['category_type', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['code']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'business_number', 'representative', 'phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'business_number', 'representative']
    ordering = ['name']

class PurchaseVoucherItemInline(admin.TabularInline):
    model = PurchaseVoucherItem
    extra = 1

@admin.register(PurchaseVoucher)
class PurchaseVoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_number', 'purchase_date', 'supplier', 'total_amount', 'is_paid', 'created_by']
    list_filter = ['purchase_date', 'payment_method', 'is_paid']
    search_fields = ['voucher_number', 'supplier__name']
    readonly_fields = ['voucher_number']
    inlines = [PurchaseVoucherItemInline]
    ordering = ['-purchase_date']

class SalesVoucherItemInline(admin.TabularInline):
    model = SalesVoucherItem
    extra = 1

@admin.register(SalesVoucher)
class SalesVoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_number', 'sales_date', 'customer_name', 'total_amount', 'is_received', 'created_by']
    list_filter = ['sales_date', 'payment_method', 'is_received']
    search_fields = ['voucher_number', 'customer_name']
    readonly_fields = ['voucher_number']
    inlines = [SalesVoucherItemInline]
    ordering = ['-sales_date']

class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_number', 'entry_date', 'description', 'created_by']
    list_filter = ['entry_date']
    search_fields = ['entry_number', 'description']
    inlines = [JournalEntryLineInline]
    ordering = ['-entry_date']
