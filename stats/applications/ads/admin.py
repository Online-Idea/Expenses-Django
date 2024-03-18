from django.contrib import admin

# # Register your models here.
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import Client
#
# class ClientAdmin(UserAdmin):
#     model = Client
#     list_display = ['email', 'name', 'is_active', 'is_staff']
#     fieldsets = (
#         (None, {'fields': ('email', 'password', 'name', 'is_active', 'is_staff')}),
#         ('Permissions', {'fields': ('is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login',)}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'name', 'password1', 'password2', 'is_active', 'is_staff'),
#         }),
#     )
#     search_fields = ('email', 'name')
#     ordering = ('email',)
#
# admin.site.register(Client, ClientAdmin)