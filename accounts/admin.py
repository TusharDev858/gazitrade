from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    list_display   = ['phone','name','email','is_active','is_staff','date_joined']
    list_filter    = ['is_active','is_staff']
    search_fields  = ['phone','name','email']
    ordering       = ['-date_joined']
    fieldsets = (
        (None,            {'fields': ('phone','password')}),
        ('Personal Info', {'fields': ('name','email','address','area')}),
        ('Permissions',   {'fields': ('is_active','is_staff','is_superuser','groups','user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes':('wide',), 'fields':('phone','name','password1','password2')}),
    )
