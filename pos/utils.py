from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# RoleHelper — Utility class untuk cek role/jabatan user
class RoleHelper:
    FULL_ACCESS_ROLES = ('manager', 'supervisor')

    @staticmethod
    def get_position(user):
        if user.is_superuser:
            return 'manager'
        try:
            return user.employee.position
        except Exception:
            return 'cashier'  # default fallback

    @staticmethod
    def is_full_access(user):
        return RoleHelper.get_position(user) in RoleHelper.FULL_ACCESS_ROLES

    @staticmethod
    def can_manage_products(user):
        return RoleHelper.is_full_access(user)

    @staticmethod
    def can_manage_employees(user):
        return RoleHelper.is_full_access(user)

    @staticmethod
    def can_view_transactions(user):
        return RoleHelper.get_position(user) in ('manager', 'supervisor', 'cashier', 'waiter')

    @staticmethod
    def can_create_transaction(user):
        return RoleHelper.get_position(user) in ('manager', 'supervisor', 'cashier', 'waiter')

    @staticmethod
    def can_view_customers(user):
        return RoleHelper.get_position(user) in ('manager', 'supervisor', 'cashier')

    @staticmethod
    def can_view_reports(user):
        return RoleHelper.is_full_access(user)

    @staticmethod
    def can_view_stock_report(user):
        return RoleHelper.get_position(user) in ('manager', 'supervisor', 'barista')

# BASE CLASS ReportGenerator — Inheritance & Encapsulation
class ReportGenerator:
    def __init__(self, start_date=None, end_date=None):
        self.__start = start_date or (timezone.now() - timedelta(days=30)).date()
        self.__end   = end_date   or timezone.now().date()

    def get_start(self):
        return self.__start

    def get_end(self):
        return self.__end

    def get_periode(self):
        return f"{self.__start.strftime('%d/%m/%Y')} — {self.__end.strftime('%d/%m/%Y')}"

    def generate(self):
        return {}

# SalesReportGenerator — INHERITANCE + POLYMORPHISM
class SalesReportGenerator(ReportGenerator):
    def generate(self):
        from .models import Transaction

        trx = Transaction.objects.filter(
            created_at__date__range=[self.get_start(), self.get_end()],
            status='completed'
        )

        total_revenue = trx.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        total_count   = trx.count()
        avg           = trx.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0')

        # Data harian untuk grafik
        daily_data, current = [], self.get_start()
        while current <= self.get_end():
            day_total = trx.filter(
                created_at__date=current
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            daily_data.append({'date': current.strftime('%d/%m'), 'total': float(day_total)})
            current += timedelta(days=1)

        return {
            'title': 'Laporan Penjualan',
            'date_range': self.get_periode(),   # diwarisi dari ReportGenerator
            'total_revenue': total_revenue,
            'total_transactions': total_count,
            'avg_transaction': avg,
            'daily_data': daily_data,
            'transactions': trx.order_by('-created_at')[:50],
        }

# StockReportGenerator — INHERITANCE + POLYMORPHISM
class StockReportGenerator(ReportGenerator):
    def generate(self):
        from .models import Product

        products = Product.objects.all()
        return {
            'title': 'Laporan Stok Produk',
            'date_range': self.get_periode(),   # diwarisi dari ReportGenerator
            'products': products.order_by('category', 'stock'),
            'low_stock': products.filter(stock__lte=5, stock__gt=0),
            'out_of_stock': products.filter(stock=0),
            'total_products': products.count(),
            'by_category': list(products.values('category').annotate(
                count=Count('id'), total_stock=Sum('stock')
            )),
        }

# CustomerReportGenerator — INHERITANCE + POLYMORPHISM
class CustomerReportGenerator(ReportGenerator):
    def generate(self):
        from .models import Customer

        customers = Customer.objects.all()
        top = Customer.objects.annotate(
            transaction_count=Count('transactions'),
            total_spent=Sum('transactions__total_amount')
        ).filter(transactions__status='completed').order_by('-total_spent')[:10]

        return {
            'title': 'Laporan Pelanggan',
            'date_range': self.get_periode(),   # diwarisi dari ReportGenerator
            'total_customers': customers.count(),
            'new_customers': customers.filter(
                created_at__date__range=[self.get_start(), self.get_end()]
            ).count(),
            'top_customers': top,
            'customers': customers.order_by('-loyalty_points'),
        }

# DashboardStats — Utility class untuk statistik dashboard
class DashboardStats:

    @staticmethod
    def get_today_stats():
        from .models import Transaction, Product, Customer, Employee
        today = timezone.localdate()   # tanggal lokal (WIB), bukan UTC
        today_trx = Transaction.objects.filter(created_at__date=today, status='completed')
        all_trx   = Transaction.objects.filter(status='completed')
        avg_rev   = all_trx.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0')
        return {
            'today_revenue':        today_trx.aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            'today_transactions':   today_trx.count(),
            'total_products':       Product.objects.count(),
            'total_customers':      Customer.objects.count(),
            'total_employees':      Employee.objects.filter(employee_status='active').count(),
            'low_stock_products':   Product.objects.filter(stock__lte=5, stock__gt=0).count(),
            'out_of_stock':         Product.objects.filter(stock=0).count(),
            'total_revenue_all':    all_trx.aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            'avg_revenue_per_trx':  avg_rev,
        }

    @staticmethod
    def get_weekly_chart_data():
        from .models import Transaction
        data, labels = [], []
        for i in range(6, -1, -1):
            day = timezone.localdate() - timedelta(days=i)  # tanggal lokal (WIB)
            total = Transaction.objects.filter(
                created_at__date=day, status='completed'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            data.append(float(total))
            labels.append(day.strftime('%a, %d %b'))
        return {'labels': labels, 'data': data}

    @staticmethod
    def get_recent_transactions(limit=8):
        from .models import Transaction
        return Transaction.objects.select_related('customer', 'cashier').order_by('-created_at')[:limit]

    @staticmethod
    def get_top_products(limit=5):
        from .models import TransactionItem
        return TransactionItem.objects.values(
            'product__name', 'product__category'
        ).annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum('subtotal')
        ).order_by('-total_qty')[:limit]
