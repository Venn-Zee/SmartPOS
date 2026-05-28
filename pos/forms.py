from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Customer, Transaction, TransactionItem, Employee

# LOGIN FORM
class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
            'id': 'id_username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'id_password',
        })

# PRODUCT FORMS
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'stock', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama produk',
                'id': 'product_name',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'product_category',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '100',
                'id': 'product_price',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'id': 'product_stock',
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'product_available',
            }),
        }
        labels = {
            'name': 'Nama Produk',
            'category': 'Kategori',
            'price': 'Harga (Rp)',
            'stock': 'Stok',
            'is_available': 'Tersedia untuk Dijual',
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError("Harga harus lebih dari 0.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError("Stok tidak boleh negatif.")
        return stock

# CUSTOMER FORMS
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'loyalty_points', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap pelanggan',
                'id': 'customer_name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@contoh.com',
                'id': 'customer_email',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '08xxxxxxxxxx',
                'id': 'customer_phone',
            }),
            'loyalty_points': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'customer_points',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Alamat pelanggan (opsional)',
                'id': 'customer_address',
            }),
        }
        labels = {
            'name': 'Nama Pelanggan',
            'email': 'Email',
            'phone': 'No. Telepon',
            'loyalty_points': 'Poin Loyalitas',
            'address': 'Alamat',
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError("Nomor telepon hanya boleh berisi angka.")
        return phone

# TRANSACTION FORMS
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['customer', 'status', 'payment_method']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-control',
                'id': 'transaction_customer',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'id': 'transaction_status',
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'id': 'transaction_payment',
            }),
        }
        labels = {
            'customer': 'Pelanggan',
            'status': 'Status Transaksi',
            'payment_method': 'Metode Pembayaran',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all()
        self.fields['customer'].empty_label = "-- Pelanggan Umum (Walk-in) --"
        self.fields['customer'].required = False


class TransactionItemForm(forms.ModelForm):
    class Meta:
        model = TransactionItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control',
                'id': 'item_product',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1',
                'id': 'item_quantity',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(
            is_available=True, stock__gt=0
        )

# EMPLOYEE FORMS
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['full_name', 'position', 'salary', 'employee_status']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap karyawan',
                'id': 'employee_fullname',
            }),
            'position': forms.Select(attrs={
                'class': 'form-control',
                'id': 'employee_position',
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '100000',
                'id': 'employee_salary',
            }),
            'employee_status': forms.Select(attrs={
                'class': 'form-control',
                'id': 'employee_status',
            }),
        }
        labels = {
            'full_name': 'Nama Lengkap',
            'position': 'Jabatan',
            'salary': 'Gaji (Rp/bulan)',
            'employee_status': 'Status',
        }


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'user_password',
        }),
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Konfirmasi password',
            'id': 'user_confirm_password',
        }),
        label='Konfirmasi Password'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username unik',
                'id': 'user_username',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email akun',
                'id': 'user_email',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama depan',
                'id': 'user_firstname',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama belakang',
                'id': 'user_lastname',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError("Password tidak cocok.")
        return cleaned_data
