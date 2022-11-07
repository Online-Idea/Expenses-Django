from django.contrib import admin

from .models import *


# Register your models here.
class ClientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'manager', 'active', 'teleph_id', 'autoru_id', 'avito_id', 'drom_id')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'manager')
    list_editable = ('active',)
    list_filter = ('manager', 'active')
    fields = ('id', 'name', 'manager', 'active', 'teleph_id', 'autoru_id', 'avito_id', 'drom_id')
    readonly_fields = ('id',)
    save_on_top = True


class MarksAdmin(admin.ModelAdmin):
    list_display = ('id', 'mark', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    list_display_links = ('id', 'mark')
    search_fields = ('mark', 'human_name')
    list_filter = ('mark', 'human_name')
    fields = ('id', 'mark', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id', )
    save_on_top = True


class ModelsAdmin(admin.ModelAdmin):
    list_display = ('id', 'mark_id', 'model', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    list_display_links = ('id', 'model')
    search_fields = ('model', 'human_name')
    list_filter = ('model', 'human_name')
    fields = ('id', 'mark_id', 'model', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True


admin.site.register(Clients, ClientsAdmin)
admin.site.register(Marks, MarksAdmin)
admin.site.register(Models, ModelsAdmin)
