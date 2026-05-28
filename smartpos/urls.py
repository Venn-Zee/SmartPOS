"""
URL configuration for smartpos project.
SmartPOS Cafe & Retail Management System
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pos.urls')),
]