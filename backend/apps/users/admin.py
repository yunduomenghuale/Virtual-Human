from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('role', 'real_name', 'lab_name')}),
    )
    list_display = ('username', 'real_name', 'role', 'lab_name', 'is_active')
    list_filter = ('role', 'is_active')
