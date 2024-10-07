from django.contrib import admin
from .models import Salon


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    """
    Конфигурация административной панели для модели Salon.
    """
    # Поля, которые будут отображаться в списке объектов в админке
    list_display = ('name', 'client', 'city', 'address', 'telephone', 'datetime_updated', 'price_url')

    # Поля, по которым можно фильтровать список объектов
    list_filter = ('city',)

    # Поля, по которым можно осуществлять поиск в админке
    search_fields = ('name', 'city', 'address', 'telephone')

    # Позволяет фильтровать записи по дате
    date_hierarchy = 'datetime_updated'

    # Поля, по которым будет происходить сортировка по умолчанию
    ordering = ('datetime_updated',)
