from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Client


#
# class ClientAdmin(UserAdmin):
#     model = Client
#     list_display = ('email', 'name', 'active', 'is_staff', 'is_superuser')
#     list_filter = ('active', 'is_staff', 'is_superuser')
#     fieldsets = (
#         (None, {'fields': ('email', 'password', 'name', 'slug')}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login', 'date_joined')}),
#         ('Additional Info', {'fields': (
#         'charge_type', 'commission_size', 'teleph_id', 'autoru_id', 'autoru_name', 'avito_id', 'drom_id')}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'name', 'password1', 'password2', 'active', 'is_staff', 'is_superuser'),
#         }),
#     )
#     search_fields = ('email', 'name')
#     ordering = ('email',)

class ClientAdmin(UserAdmin):
    model = Client
    list_display = (
        'id', 'name', 'manager', 'active', 'charge_type', 'commission_size', 'teleph_id', 'autoru_id', 'autoru_name',
        'avito_id', 'drom_id')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'manager', 'teleph_id', 'autoru_id', 'autoru_name', 'avito_id', 'drom_id')
    list_editable = ('active',)
    list_filter = ('manager', 'active', 'charge_type', 'is_staff', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('name', 'email', 'password', 'username', 'slug')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Additional Info', {'fields': (
            'charge_type', 'commission_size', 'teleph_id', 'autoru_id', 'autoru_name', 'avito_id', 'drom_id')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'active', 'is_staff', 'is_superuser'),
        }),
    )
    readonly_fields = ('id',)
    ordering = ('email',)
    save_on_top = True


admin.site.register(Client, ClientAdmin)
