import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Product, Customer, Transaction, TransactionItem, Employee
from .forms import (
    CustomLoginForm, ProductForm, CustomerForm,
    TransactionForm, TransactionItemForm, EmployeeForm, UserCreateForm
)
from .utils import DashboardStats, SalesReportGenerator, StockReportGenerator, CustomerReportGenerator, RoleHelper

# ROLE-BASED ACCESS
class RoleRequiredMixin(LoginRequiredMixin):
    allowed_positions = ()   # override di subclass
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        # Superuser selalu punya akses penuh
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        position = RoleHelper.get_position(request.user)
        if self.allowed_positions and position not in self.allowed_positions:
            messages.error(request, '⛔ Akses ditolak. Anda tidak memiliki izin untuk halaman ini.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

# AUTH VIEWS
class LoginView(View):
    template_name = 'pos/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = CustomLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Selamat datang, {user.get_full_name() or user.username}! ☕')
            return redirect('dashboard')
        messages.error(request, 'Username atau password salah.')
        return render(request, self.template_name, {'form': form})


class LogoutView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        logout(request)
        messages.info(request, 'Anda telah keluar. Sampai jumpa! 👋')
        return redirect('login')

# DASHBOARD VIEW
class DashboardView(LoginRequiredMixin, View):
    """Dashboard utama SmartPOS"""
    login_url = '/login/'
    template_name = 'pos/dashboard.html'

    def get(self, request):
        stats = DashboardStats.get_today_stats()
        chart_data = DashboardStats.get_weekly_chart_data()
        recent_transactions = DashboardStats.get_recent_transactions()
        top_products = DashboardStats.get_top_products()

        context = {
            'stats': stats,
            'chart_labels': json.dumps(chart_data['labels']),
            'chart_data': json.dumps(chart_data['data']),
            'recent_transactions': recent_transactions,
            'top_products': top_products,
            'page_title': 'Dashboard',
        }
        return render(request, self.template_name, context)

# PRODUCT VIEWS — INHERITANCE dari LoginRequiredMixin + generic views
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'pos/products/list.html'
    context_object_name = 'products'
    login_url = '/login/'

    def get_queryset(self):
        queryset = Product.objects.all()
        search = self.request.GET.get('search', '')
        category = self.request.GET.get('category', '')
        if search:
            queryset = queryset.filter(name__icontains=search)
        if category:
            queryset = queryset.filter(category=category)
        return queryset.order_by('category', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Manajemen Produk'
        context['categories'] = Product.CATEGORY_CHOICES
        context['search'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class ProductCreateView(RoleRequiredMixin, CreateView):
    allowed_positions = ('manager', 'supervisor')
    model = Product
    form_class = ProductForm
    template_name = 'pos/products/form.html'
    success_url = reverse_lazy('product_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tambah Produk'
        context['form_title'] = 'Tambah Produk Baru'
        context['submit_label'] = 'Simpan Produk'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Produk "{form.instance.name}" berhasil ditambahkan! ✅')
        return super().form_valid(form)


class ProductUpdateView(RoleRequiredMixin, UpdateView):
    allowed_positions = ('manager', 'supervisor')
    model = Product
    form_class = ProductForm
    template_name = 'pos/products/form.html'
    success_url = reverse_lazy('product_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Produk'
        context['form_title'] = f'Edit: {self.object.name}'
        context['submit_label'] = 'Perbarui Produk'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Produk "{form.instance.name}" berhasil diperbarui! ✅')
        return super().form_valid(form)


class ProductDeleteView(RoleRequiredMixin, DeleteView):
    allowed_positions = ('manager', 'supervisor')
    model = Product
    template_name = 'pos/confirm_delete.html'
    success_url = reverse_lazy('product_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Hapus Produk'
        context['object_type'] = 'Produk'
        context['object_name'] = self.object.name
        context['cancel_url'] = reverse_lazy('product_list')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Produk "{self.object.name}" berhasil dihapus.')
        return super().form_valid(form)

# CUSTOMER VIEWS
class CustomerListView(RoleRequiredMixin, ListView):
    allowed_positions = ('manager', 'supervisor', 'cashier')
    model = Customer
    template_name = 'pos/customers/list.html'
    context_object_name = 'customers'
    login_url = '/login/'

    def get_queryset(self):
        queryset = Customer.objects.all()
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(email__icontains=search)
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Manajemen Pelanggan'
        context['search'] = self.request.GET.get('search', '')
        return context


class CustomerCreateView(RoleRequiredMixin, CreateView):
    allowed_positions = ('manager', 'supervisor', 'cashier')
    model = Customer
    form_class = CustomerForm
    template_name = 'pos/customers/form.html'
    success_url = reverse_lazy('customer_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tambah Pelanggan'
        context['form_title'] = 'Daftarkan Pelanggan Baru'
        context['submit_label'] = 'Simpan Pelanggan'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Pelanggan "{form.instance.name}" berhasil didaftarkan! ☕')
        return super().form_valid(form)


class CustomerUpdateView(RoleRequiredMixin, UpdateView):
    allowed_positions = ('manager', 'supervisor', 'cashier')
    model = Customer
    form_class = CustomerForm
    template_name = 'pos/customers/form.html'
    success_url = reverse_lazy('customer_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Pelanggan'
        context['form_title'] = f'Edit: {self.object.name}'
        context['submit_label'] = 'Perbarui Pelanggan'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Data pelanggan "{form.instance.name}" berhasil diperbarui!')
        return super().form_valid(form)


class CustomerDeleteView(RoleRequiredMixin, DeleteView):
    allowed_positions = ('manager', 'supervisor')
    model = Customer
    template_name = 'pos/confirm_delete.html'
    success_url = reverse_lazy('customer_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Hapus Pelanggan'
        context['object_type'] = 'Pelanggan'
        context['object_name'] = self.object.name
        context['cancel_url'] = reverse_lazy('customer_list')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Pelanggan "{self.object.name}" berhasil dihapus.')
        return super().form_valid(form)

# TRANSACTION VIEWS
class TransactionListView(RoleRequiredMixin, ListView):
    allowed_positions = ('manager', 'supervisor', 'cashier', 'waiter')
    model = Transaction
    template_name = 'pos/transactions/list.html'
    context_object_name = 'transactions'
    login_url = '/login/'

    def get_queryset(self):
        queryset = Transaction.objects.select_related('customer', 'cashier').all()
        status = self.request.GET.get('status', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Manajemen Transaksi'
        context['status_choices'] = Transaction.STATUS_CHOICES
        return context


class TransactionCreateView(RoleRequiredMixin, View):
    allowed_positions = ('manager', 'supervisor', 'cashier', 'waiter')
    template_name = 'pos/transactions/form.html'
    login_url = '/login/'

    def get(self, request):
        form = TransactionForm()
        item_form = TransactionItemForm()
        products = Product.objects.filter(is_available=True, stock__gt=0)
        context = {
            'form': form,
            'item_form': item_form,
            'products': products,
            'page_title': 'Transaksi Baru',
            'products_json': json.dumps([p.to_dict() for p in products]),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = TransactionForm(request.POST)
        if form.is_valid():
            with db_transaction.atomic():
                trx = form.save(commit=False)
                trx.cashier = request.user
                trx.total_amount = 0
                trx.save()

                # Proses item
                product_ids = request.POST.getlist('product_id')
                quantities = request.POST.getlist('quantity')
                total = 0

                for pid, qty in zip(product_ids, quantities):
                    try:
                        product = Product.objects.get(id=pid)
                        quantity = int(qty)
                        if quantity > 0 and quantity <= product.stock:
                            item = TransactionItem(
                                transaction=trx,
                                product=product,
                                quantity=quantity
                            )
                            item.save()
                            product.reduce_stock(quantity)
                            total += float(item.subtotal)
                    except (Product.DoesNotExist, ValueError):
                        continue

                trx.total_amount = total
                trx.save()

                if trx.customer and trx.status == 'completed':
                    trx.customer.add_points(trx.total_amount)

            messages.success(request, f'Transaksi TRX-{trx.id:04d} berhasil dibuat! 🎉')
            return redirect('transaction_detail', pk=trx.id)

        messages.error(request, 'Terjadi kesalahan. Periksa kembali form.')
        return redirect('transaction_create')


class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = 'pos/transactions/detail.html'
    context_object_name = 'transaction'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Detail Transaksi TRX-{self.object.id:04d}'
        context['items'] = self.object.items.select_related('product').all()
        return context


class TransactionUpdateView(RoleRequiredMixin, UpdateView):
    allowed_positions = ('manager', 'supervisor')
    model = Transaction
    form_class = TransactionForm
    template_name = 'pos/transactions/edit_form.html'
    success_url = reverse_lazy('transaction_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Transaksi TRX-{self.object.id:04d}'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Transaksi TRX-{form.instance.id:04d} berhasil diperbarui!')
        return super().form_valid(form)


class TransactionDeleteView(RoleRequiredMixin, DeleteView):
    allowed_positions = ('manager', 'supervisor')
    model = Transaction
    template_name = 'pos/confirm_delete.html'
    success_url = reverse_lazy('transaction_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Hapus Transaksi'
        context['object_type'] = 'Transaksi'
        context['object_name'] = f'TRX-{self.object.id:04d}'
        context['cancel_url'] = reverse_lazy('transaction_list')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Transaksi TRX-{self.object.id:04d} berhasil dihapus.')
        return super().form_valid(form)

# EMPLOYEE VIEWS
class EmployeeListView(RoleRequiredMixin, ListView):
    allowed_positions = ('manager', 'supervisor')
    model = Employee
    template_name = 'pos/employees/list.html'
    context_object_name = 'employees'
    login_url = '/login/'

    def get_queryset(self):
        queryset = Employee.objects.select_related('user').all()
        search = self.request.GET.get('search', '')
        position = self.request.GET.get('position', '')
        if search:
            queryset = queryset.filter(full_name__icontains=search)
        if position:
            queryset = queryset.filter(position=position)
        return queryset.order_by('position', 'full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Manajemen Karyawan'
        context['positions'] = Employee.POSITION_CHOICES
        return context


class EmployeeCreateView(RoleRequiredMixin, View):
    allowed_positions = ('manager', 'supervisor')
    template_name = 'pos/employees/form.html'
    login_url = '/login/'

    def get(self, request):
        user_form = UserCreateForm()
        emp_form = EmployeeForm()
        return render(request, self.template_name, {
            'user_form': user_form,
            'form': emp_form,
            'page_title': 'Tambah Karyawan',
            'form_title': 'Daftarkan Karyawan Baru',
            'submit_label': 'Simpan Karyawan',
        })

    def post(self, request):
        user_form = UserCreateForm(request.POST)
        emp_form = EmployeeForm(request.POST)
        if user_form.is_valid() and emp_form.is_valid():
            with db_transaction.atomic():
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                emp = emp_form.save(commit=False)
                emp.user = user
                emp.save()
            messages.success(request, f'Karyawan "{emp.full_name}" berhasil didaftarkan! ✅')
            return redirect('employee_list')
        return render(request, self.template_name, {
            'user_form': user_form,
            'form': emp_form,
            'page_title': 'Tambah Karyawan',
        })


class EmployeeUpdateView(RoleRequiredMixin, UpdateView):
    allowed_positions = ('manager', 'supervisor')
    model = Employee
    form_class = EmployeeForm
    template_name = 'pos/employees/form.html'
    success_url = reverse_lazy('employee_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Karyawan'
        context['form_title'] = f'Edit: {self.object.full_name}'
        context['submit_label'] = 'Perbarui Karyawan'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Data karyawan "{form.instance.full_name}" berhasil diperbarui!')
        return super().form_valid(form)


class EmployeeDeleteView(RoleRequiredMixin, DeleteView):
    allowed_positions = ('manager', 'supervisor')
    model = Employee
    template_name = 'pos/confirm_delete.html'
    success_url = reverse_lazy('employee_list')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Hapus Karyawan'
        context['object_type'] = 'Karyawan'
        context['object_name'] = self.object.full_name
        context['cancel_url'] = reverse_lazy('employee_list')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Karyawan "{self.object.full_name}" berhasil dihapus.')
        return super().form_valid(form)

# REPORTING VIEWS
class ReportView(LoginRequiredMixin, View):
    """Base class untuk semua halaman report"""
    login_url = '/login/'

    def get_date_range(self, request):
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        try:
            start = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
            end = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
        except ValueError:
            start = end = None
        return start, end


class SalesReportView(ReportView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            if not RoleHelper.is_full_access(request.user):
                messages.error(request, 'Akses ditolak. Laporan hanya untuk Manager dan Supervisor.')
                return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        start, end = self.get_date_range(request)
        generator = SalesReportGenerator(start, end)
        report_data = generator.generate()
        return render(request, 'pos/reports/sales.html', {
            'report': report_data,
            'page_title': 'Laporan Penjualan',
            'date_from': start or (timezone.now() - timedelta(days=30)).date(),
            'date_to': end or timezone.now().date(),
        })


class StockReportView(ReportView):
    """Laporan Stok — Manager, Supervisor & Barista"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            if not RoleHelper.can_view_stock_report(request.user):
                messages.error(request, 'Akses ditolak. Laporan stok hanya untuk Manager, Supervisor, dan Barista.')
                return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        start, end = self.get_date_range(request)
        generator = StockReportGenerator(start, end)
        report_data = generator.generate()
        return render(request, 'pos/reports/stock.html', {
            'report': report_data,
            'page_title': 'Laporan Stok Produk',
        })


class CustomerReportView(ReportView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            if not RoleHelper.is_full_access(request.user):
                messages.error(request, 'Akses ditolak. Laporan hanya untuk Manager dan Supervisor.')
                return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        start, end = self.get_date_range(request)
        generator = CustomerReportGenerator(start, end)
        report_data = generator.generate()
        return render(request, 'pos/reports/customers.html', {
            'report': report_data,
            'page_title': 'Laporan Pelanggan',
            'date_from': start or (timezone.now() - timedelta(days=30)).date(),
            'date_to': end or timezone.now().date(),
        })

# API VIEWS (JSON)
@login_required
def product_api(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return JsonResponse(product.to_dict())


@login_required
def dashboard_chart_api(request):
    data = DashboardStats.get_weekly_chart_data()
    return JsonResponse(data)
