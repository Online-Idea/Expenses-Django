from django.contrib import admin

from applications.mainapp.admin_helpers import *
from applications.mainapp.models import Mark, Model


class MarkAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'human_name')
    fields = ('id', 'name', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True


class ModelAdmin(admin.ModelAdmin):
    list_display = ('id', marks_mark, 'name', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    list_display_links = ('id', marks_mark, 'name')
    search_fields = ('mark__name', 'name', 'human_name')
    fields = ('id', 'mark', 'name', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True


admin.site.register(Mark, MarkAdmin)
admin.site.register(Model, ModelAdmin)
