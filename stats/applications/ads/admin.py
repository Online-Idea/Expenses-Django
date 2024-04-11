from django.contrib import admin
from .models import Salon


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'city', 'address', 'telephone', 'datetime_updated',
                    'price_url')  # поля, которые будут отображаться в списке
    list_filter = ('city',)  # поля, по которым можно фильтровать в списке
    search_fields = ('name', 'city', 'address', 'telephone')  # поля, по которым можно искать в списке
    date_hierarchy = 'datetime_updated'  # позволяет фильтровать по дате
    ordering = ('datetime_updated',)  # порядок сортировки
