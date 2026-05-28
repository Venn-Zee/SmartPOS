from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

# BASE CLASS — Abstraction & Inheritance
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # tidak membuat tabel sendiri

    def get_info(self): # Polymorphism: method ini di-override oleh setiap subclass dengan output yang berbeda-beda.
        return f"[{self.__class__.__name__}] objek"

# PRODUCT — Produk / Menu
class Product(BaseModel):
    CATEGORY_CHOICES = [
        ('food',        'Makanan'),
        ('beverage',    'Minuman'),
        ('snack',       'Snack'),
        ('merchandise', 'Merchandise'),
        ('other',       'Lainnya'),
    ]

    name         = models.CharField(max_length=100, verbose_name="Nama Produk")
    category     = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Kategori")
    price        = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Harga (Rp)")
    stock        = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Stok")
    is_available = models.BooleanField(default=True, verbose_name="Tersedia")

    class Meta:
        verbose_name        = "Produk"
        verbose_name_plural = "Produk"
        ordering            = ['category', 'name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__discount = 0  # ENCAPSULATION: private, tidak bisa diakses dari luar

    # Getter & Setter (Encapsulation)

    def get_discount(self): # Getter: baca nilai diskon yang disembunyikan.
        return self.__discount

    def set_discount(self, persen): # Setter: ubah diskon dengan validasi (0–100%).
        if not (0 <= persen <= 100):
            raise ValueError("Diskon harus antara 0 hingga 100 persen.")
        self.__discount = persen

    def get_harga_akhir(self):
        return float(self.price) * (1 - self.__discount / 100)

    def is_in_stock(self):
        return self.stock > 0

    def reduce_stock(self, quantity):
        if quantity > self.stock:
            raise ValueError(f"Stok tidak cukup. Tersedia: {self.stock}, diminta: {quantity}")
        self.stock -= quantity
        self.save()

    def add_stock(self, quantity):
        self.stock += quantity
        self.save()

    #Polymorphism

    def get_info(self): # Override get_info() jadi menampilkan info produk.
        return f"[Produk] {self.name} | Rp {self.price:,.0f} | Stok: {self.stock}"

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name,
            'category': self.category, 'category_display': self.get_category_display(),
            'price': float(self.price), 'stock': self.stock,
            'is_available': self.is_available,
        }

# CUSTOMER — Pelanggan
class Customer(BaseModel):
    name           = models.CharField(max_length=100, verbose_name="Nama Pelanggan")
    email          = models.EmailField(unique=True, verbose_name="Email")
    phone          = models.CharField(max_length=15, verbose_name="No. Telepon")
    loyalty_points = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Poin Loyalitas")
    address        = models.TextField(blank=True, null=True, verbose_name="Alamat")

    class Meta:
        verbose_name        = "Pelanggan"
        verbose_name_plural = "Pelanggan"
        ordering            = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__poin_pending = 0  # ENCAPSULATION: poin belum dikonfirmasi, disembunyikan

    def get_poin_pending(self):
        return self.__poin_pending

    def set_poin_pending(self, poin):
        if poin < 0:
            raise ValueError("Poin tidak boleh negatif.")
        self.__poin_pending = poin

    def add_points(self, amount):
        earned = int(amount / 10000)
        self.loyalty_points += earned
        self.save()
        return earned

    def redeem_points(self, points):
        if points > self.loyalty_points:
            raise ValueError("Poin tidak mencukupi.")
        if points < 100:
            raise ValueError("Minimal penukaran 100 poin.")
        self.loyalty_points -= points
        self.save()
        return points * 100

    def get_tier(self):
        if self.loyalty_points >= 5000:
            return 'Gold'
        elif self.loyalty_points >= 1000:
            return 'Silver'
        return 'Bronze'

    def get_info(self):
        return f"[Pelanggan] {self.name} | Tier: {self.get_tier()} | Poin: {self.loyalty_points}"

    def __str__(self):
        return f"{self.name} ({self.email})"

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'email': self.email,
            'phone': self.phone, 'loyalty_points': self.loyalty_points, 'tier': self.get_tier(),
        }

# TRANSACTION — Transaksi Penjualan
class Transaction(BaseModel):
    STATUS_CHOICES = [
        ('pending',   'Menunggu'),
        ('completed', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ]
    PAYMENT_CHOICES = [
        ('cash',     'Tunai'),
        ('debit',    'Kartu Debit'),
        ('transfer', 'Transfer Bank'),
        ('qris',     'QRIS'),
    ]

    customer       = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name="Pelanggan")
    cashier        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transactions', verbose_name="Kasir")
    total_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total (Rp)")
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed', verbose_name="Status")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash', verbose_name="Metode Pembayaran")

    class Meta:
        verbose_name        = "Transaksi"
        verbose_name_plural = "Transaksi"
        ordering            = ['-created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__catatan = ""

    def get_catatan(self):
        return self.__catatan

    def set_catatan(self, teks):
        self.__catatan = str(teks)

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save()
        return total

    def complete_transaction(self):
        self.status = 'completed'
        self.save()
        if self.customer:
            self.customer.add_points(self.total_amount)

    def cancel_transaction(self):
        self.status = 'cancelled'
        self.save()
        for item in self.items.all():
            item.product.add_stock(item.quantity)

    def get_info(self):
        pelanggan = self.customer.name if self.customer else 'Umum'
        return f"[Transaksi] TRX-{self.id:04d} | {pelanggan} | Rp {self.total_amount:,.0f} | {self.get_status_display()}"

    def __str__(self):
        return f"TRX-{self.id:04d} | {self.created_at.strftime('%d/%m/%Y')} | Rp {self.total_amount:,.0f}"

    def to_dict(self):
        return {
            'id': self.id,
            'customer': self.customer.name if self.customer else 'Umum',
            'cashier': self.cashier.get_full_name() if self.cashier else '-',
            'total_amount': float(self.total_amount),
            'status': self.status,
            'payment_method': self.payment_method,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
        }

# TRANSACTION ITEM — Detail item per transaksi
class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items', verbose_name="Transaksi")
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transaction_items', verbose_name="Produk")
    quantity    = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Jumlah")
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Harga Satuan")
    subtotal    = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Subtotal")

    class Meta:
        verbose_name        = "Item Transaksi"
        verbose_name_plural = "Item Transaksi"

    def save(self, *args, **kwargs):
        self.unit_price = self.product.price
        self.subtotal   = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} = Rp {self.subtotal:,.0f}"

# EMPLOYEE — Karyawan
class Employee(BaseModel):
    POSITION_CHOICES = [
        ('manager',    'Manager'),
        ('cashier',    'Kasir'),
        ('barista',    'Barista'),
        ('waiter',     'Pelayan'),
        ('supervisor', 'Supervisor'),
    ]
    STATUS_CHOICES = [
        ('active',   'Aktif'),
        ('inactive', 'Tidak Aktif'),
        ('on_leave', 'Cuti'),
    ]

    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee', verbose_name="Akun Login")
    full_name       = models.CharField(max_length=150, verbose_name="Nama Lengkap")
    position        = models.CharField(max_length=50, choices=POSITION_CHOICES, default='cashier', verbose_name="Jabatan")
    salary          = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))], verbose_name="Gaji (Rp)")
    employee_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Status Karyawan")

    class Meta:
        verbose_name        = "Karyawan"
        verbose_name_plural = "Karyawan"
        ordering            = ['position', 'full_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__bonus_persen = 0 

    def get_bonus(self):
        return self.__bonus_persen

    def set_bonus(self, persen):
        if not (0 <= persen <= 50):
            raise ValueError("Bonus maksimal 50%.")
        self.__bonus_persen = persen

    def get_gaji_bonus(self):
        return float(self.salary) * (1 + self.__bonus_persen / 100)

    def get_gaji_tahunan(self):
        return self.salary * 12

    def is_manager(self):
        return self.position == 'manager'

    def get_info(self):
        return f"[Karyawan] {self.full_name} | {self.get_position_display()} | Gaji: Rp {self.salary:,.0f}"

    def __str__(self):
        return f"{self.full_name} — {self.get_position_display()}"

    def to_dict(self):
        return {
            'id': self.id, 'user_id': self.user.id,
            'full_name': self.full_name, 'position': self.position,
            'position_display': self.get_position_display(),
            'salary': float(self.salary), 'status': self.employee_status,
        }
