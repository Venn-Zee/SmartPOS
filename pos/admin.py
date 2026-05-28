from django.contrib import admin
from .models import Product, Customer, Transaction, TransactionItem, Employee


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name']
    list_editable = ['stock', 'is_available']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'loyalty_points']
    search_fields = ['name', 'email']


class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ['unit_price', 'subtotal']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'cashier', 'total_amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method']
    inlines = [TransactionItemInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'salary', 'employee_status']
    list_filter = ['position', 'employee_status']
    search_fields = ['full_name']
