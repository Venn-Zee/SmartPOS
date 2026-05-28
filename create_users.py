"""
Script untuk membuat superuser SmartPOS secara otomatis
"""
import os
import sys
import django

# Fix encoding untuk Windows
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartpos.settings')
django.setup()

from django.contrib.auth.models import User
from pos.models import Employee
from decimal import Decimal

# Buat superuser admin
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@smartpos.com',
        password='admin123',
        first_name='Admin',
        last_name='SmartPOS'
    )
    print('OK: Superuser "admin" dibuat. Password: admin123')
    Employee.objects.create(
        user=admin,
        full_name='Admin SmartPOS',
        position='manager',
        salary=Decimal('8000000'),
        employee_status='active'
    )
    print('OK: Profil karyawan Manager dibuat untuk admin')
else:
    print('INFO: User "admin" sudah ada, skip.')

# Buat kasir demo
if not User.objects.filter(username='kasir1').exists():
    kasir = User.objects.create_user(
        username='kasir1',
        email='kasir1@smartpos.com',
        password='kasir123',
        first_name='Budi',
        last_name='Santoso'
    )
    Employee.objects.create(
        user=kasir,
        full_name='Budi Santoso',
        position='cashier',
        salary=Decimal('3500000'),
        employee_status='active'
    )
    print('OK: User kasir "kasir1" dibuat. Password: kasir123')
else:
    print('INFO: User "kasir1" sudah ada, skip.')

print('')
print('=== AKUN LOGIN SmartPOS ===')
print('  Manager  -> username: admin   | password: admin123')
print('  Kasir    -> username: kasir1  | password: kasir123')
print('')
print('Buka browser: http://127.0.0.1:8000/login/')
