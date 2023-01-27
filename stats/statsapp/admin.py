from django.contrib import admin

from .models import *


# Register your models here.
class ClientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'manager', 'active', 'charge_type', 'commission_size', 'teleph_id', 'autoru_id', 'avito_id', 'drom_id')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'manager', 'teleph_id', 'autoru_id', 'avito_id', 'drom_id')
    list_editable = ('active',)
    list_filter = ('manager', 'active', 'charge_type')
    fields = ('id', 'name', 'slug', 'manager', 'active', 'charge_type', 'commission_size', 'teleph_id', 'autoru_id', 'avito_id', 'drom_id')
    readonly_fields = ('id', )
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
    readonly_fields = ('id', )
    save_on_top = True


class ConverterTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'name', 'active', 'photos_folder', 'configuration')
    list_display_links = ('id', 'client', 'name')
    list_editable = ('active', )
    search_fields = ('client', 'name')
    list_filter = ('client', 'active')
    fields = ('id', 'client', 'name', 'stock_source', 'stock_url', 'stock_post_host', 'stock_post_login',
              'stock_post_password', 'active', 'photos_folder', 'front', 'back', 'interior', 'salon_only', 'template',
              'stock_fields', 'configuration')
    readonly_fields = ('id', 'template')
    save_on_top = True


class StockFieldsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name', )
    fields = ('name', 'encoding', 'car_tag', 'modification_code', 'color_code', 'interior_code', 'options_code', 'price', 'year',
              'vin', 'id_from_client', 'modification_explained', 'color_explained', 'interior_explained', 'description',
              'trade_in', 'credit', 'insurance', 'max_discount', 'availability', 'run', 'images')
    save_on_top = True


class PhotoFolderAdmin(admin.ModelAdmin):
    list_display = ('id', 'folder')
    list_display_links = ('id', 'folder')
    search_fields = ('folder', )
    fields = ('id', 'folder')
    readonly_fields = ('id', )


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name', )
    fields = ('id', 'converter_id', 'name', 'configuration')
    readonly_fields = ('id', )


class ConverterLogsBotDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_id')
    list_display_links = ('id', 'chat_id')
    search_fields = ('chat_id', )
    fields = ('id', 'chat_id')
    readonly_fields = ('id', )


admin.site.register(Clients, ClientsAdmin)
admin.site.register(Marks, MarksAdmin)
admin.site.register(Models, ModelsAdmin)
admin.site.register(ConverterTask, ConverterTaskAdmin)
admin.site.register(StockFields, StockFieldsAdmin)
admin.site.register(PhotoFolder, PhotoFolderAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(ConverterLogsBotData, ConverterLogsBotDataAdmin)
