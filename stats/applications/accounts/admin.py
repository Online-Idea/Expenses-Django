from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Client, Account, AccountClient


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


class AccountAdmin(UserAdmin):
    list_display = ('id', 'name', 'email', 'username', 'is_staff', 'is_active')
    list_display_links = ('id', 'name', 'email', 'username')
    search_fields = ('name', 'email', 'username')
    readonly_fields = ('id', 'date_joined')
    save_on_top = True
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('id', 'name', 'email', 'password', 'username')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )


class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'manager', 'active', 'charge_type', 'commission_size', 'teleph_id', 'autoru_id',
                    'autoru_name', 'avito_id', 'drom_id')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'manager', 'teleph_id', 'autoru_id', 'autoru_name', 'avito_id', 'drom_id')
    fields = ('id', 'name', 'slug', 'manager', 'active', 'charge_type', 'commission_size', 'teleph_id', 'autoru_id',
              'autoru_name', 'avito_id', 'drom_id')
    list_editable = ('active',)
    list_filter = ('manager', 'active', 'charge_type')

    readonly_fields = ('id',)
    save_on_top = True


class AccountClientAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "account":
            kwargs["queryset"] = Account.objects.all()
        elif db_field.name == "client":
            kwargs["queryset"] = Client.objects.all()
        return super(AccountClientAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Account, AccountAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(AccountClient, AccountClientAdmin)
