from django.contrib import admin

from applications.autoconverter.models import *


class ConverterTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'name', 'active', 'photos_folder', 'configuration')
    list_display_links = ('id', 'client', 'name')
    list_editable = ('active',)
    search_fields = ('name',)
    list_filter = ('client', 'active')
    fields = ('id', 'client', 'name', 'stock_source', 'stock_url', 'stock_post_host', 'stock_post_login',
              'stock_post_password', 'active', 'photos_folder', 'front', 'back', 'interior', 'salon_only', 'template',
              'stock_fields', 'configuration', 'notifications_email')
    readonly_fields = ('id', 'template')
    save_on_top = True


class StockFieldsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    fields = (
        'name', 'encoding', 'car_tag', 'modification_code', 'color_code', 'interior_code', 'options_code', 'price',
        'year',
        'vin', 'id_from_client', 'modification_explained', 'color_explained', 'interior_explained', 'description',
        'trade_in', 'credit', 'insurance', 'max_discount', 'availability', 'run', 'images')
    save_on_top = True


class PhotoFolderAdmin(admin.ModelAdmin):
    list_display = ('id', 'folder')
    list_display_links = ('id', 'folder')
    search_fields = ('folder',)
    fields = ('id', 'folder')
    readonly_fields = ('id',)


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    fields = ('id', 'converter_id', 'name', 'configuration')
    readonly_fields = ('id',)


class ConverterLogsBotDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_id')
    list_display_links = ('id', 'chat_id')
    search_fields = ('chat_id',)
    fields = ('id', 'chat_id')
    readonly_fields = ('id',)


class ConverterFilterAdmin(admin.ModelAdmin):
    list_display = ('id', 'converter_task', 'field', 'condition', 'value')
    list_display_links = ('id', 'converter_task', 'field')
    list_editable = ('condition',)
    search_fields = ('converter_task', 'field')
    list_filter = ('converter_task',)
    fields = ('id', 'converter_task', 'field', 'condition', 'value')
    readonly_fields = ('id',)
    ordering = ('converter_task', 'field')


class ConditionalInline(admin.TabularInline):
    model = Conditional
    extra = 1


class ConverterExtraProcessingAdmin(admin.ModelAdmin):
    inlines = [ConditionalInline, ]
    list_display = ('id', 'converter_task', 'source', 'price_column_to_change', 'new_value')
    list_display_links = ('id', 'converter_task')
    search_fields = ('converter_task__name', 'price_column_to_change', 'new_value')
    list_filter = ('converter_task',)
    fields = ('id', 'converter_task', 'source', 'price_column_to_change', 'new_value')
    readonly_fields = ('id',)
    ordering = ('converter_task', 'price_column_to_change')


admin.site.register(ConverterTask, ConverterTaskAdmin)
admin.site.register(StockFields, StockFieldsAdmin)
admin.site.register(PhotoFolder, PhotoFolderAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(ConverterLogsBotData, ConverterLogsBotDataAdmin)
admin.site.register(ConverterFilter, ConverterFilterAdmin)
admin.site.register(ConverterExtraProcessing, ConverterExtraProcessingAdmin)
