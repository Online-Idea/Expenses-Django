from django.contrib import admin

from .models import *
from .admin_helpers import *


# Register your models here.
class ClientsAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'manager', 'active', 'charge_type', 'commission_size', 'teleph_id', 'autoru_id', 'avito_id',
        'drom_id')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'manager', 'teleph_id', 'autoru_id', 'avito_id', 'drom_id')
    list_editable = ('active',)
    list_filter = ('manager', 'active', 'charge_type')
    fields = (
        'id', 'name', 'slug', 'manager', 'active', 'charge_type', 'commission_size', 'teleph_id', 'autoru_id',
        'avito_id',
        'drom_id')
    readonly_fields = ('id',)
    save_on_top = True


class MarksAdmin(admin.ModelAdmin):
    list_display = ('id', 'mark', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    list_display_links = ('id', 'mark')
    search_fields = ('mark', 'human_name')
    list_filter = ('mark', 'human_name')
    fields = ('id', 'mark', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True


class ModelsAdmin(admin.ModelAdmin):
    list_display = ('id', marks_mark, 'model', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    list_display_links = ('id', 'model')
    search_fields = ('model', 'human_name')
    list_filter = ('model', 'human_name')
    fields = ('id', 'mark', 'model', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True


class GenerationsAdmin(admin.ModelAdmin):
    list_display = ('id', marks_mark, models_model, 'generation', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    list_display_links = ('id', 'generation')
    search_fields = ('mark__mark', 'model__model', 'generation', 'human_name')
    fields = ('id', 'mark', 'model', 'generation', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True

    class Media:
        js = ('statsapp/js/dynamic_fields.js',)


class ModificationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'clients_name', 'short_name', marks_mark, models_model, generations_generation,
                    complectations_complectation, 'body_type', 'engine_volume', 'power', 'transmission', 'engine_type',
                    'drive', 'battery_capacity', 'autoru_modification_id', 'autoru_complectation_id',
                    'avito_modification_id', 'avito_complectation_id', 'load_capacity')
    list_display_links = ('id', 'code', 'clients_name', 'short_name',)
    search_fields = ('code', 'clients_name', 'short_name', 'mark__mark', 'model__model', 'generation__generation',
                     'complectation__complectation')
    fields = (
        'id', 'code', 'clients_name', 'mark', 'model', 'generation', 'complectation', 'body_type', 'engine_volume',
        'power', 'transmission', 'engine_type', 'drive', 'battery_capacity', 'autoru_modification_id',
        'autoru_complectation_id', 'avito_modification_id', 'avito_complectation_id', 'load_capacity')
    readonly_fields = ('id',)
    save_on_top = True

    class Media:
        js = ('statsapp/js/dynamic_fields.js',)


class ModificationCodesAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'modification', 'complectation')
    list_display_links = ('id', 'code', 'complectation')
    search_fields = ('code',)
    fields = ('id', 'code', 'modification', 'complectation')
    readonly_fields = ('id',)
    save_on_top = True


# TODO прописать актуальные поля
class ComplectationsAdmin(admin.ModelAdmin):
    list_display = ('id', modifications_modification, 'complectation', 'teleph', 'autoru', 'avito', 'drom',
                    'human_name')
    list_display_links = ('id', 'complectation')
    search_fields = ('modification', 'complectation', 'human_name')
    fields = ('id', 'modification', 'complectation', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True

    class Media:
        js = ('statsapp/js/dynamic_fields.js',)


class ConverterTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'name', 'active', 'photos_folder', 'configuration')
    list_display_links = ('id', 'client', 'name')
    list_editable = ('active',)
    search_fields = ('name',)
    list_filter = ('client', 'active')
    fields = ('id', 'client', 'name', 'stock_source', 'stock_url', 'stock_post_host', 'stock_post_login',
              'stock_post_password', 'active', 'photos_folder', 'front', 'back', 'interior', 'salon_only', 'template',
              'stock_fields', 'configuration')
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


class ConverterFiltersAdmin(admin.ModelAdmin):
    list_display = ('id', 'converter_task', 'field', 'condition', 'value')
    list_display_links = ('id', 'converter_task', 'field')
    list_editable = ('condition',)
    search_fields = ('converter_task', 'field')
    list_filter = ('converter_task',)
    fields = ('id', 'converter_task', 'field', 'condition', 'value')
    readonly_fields = ('id',)
    ordering = ('converter_task', 'field')


class ConditionalsInline(admin.TabularInline):
    model = Conditionals
    extra = 1


class ConverterExtraProcessingAdmin(admin.ModelAdmin):
    inlines = [ConditionalsInline, ]
    list_display = ('id', 'converter_task', 'source', 'price_column_to_change', 'new_value')
    list_display_links = ('id', 'converter_task')
    search_fields = ('converter_task', 'field')
    list_filter = ('converter_task',)
    fields = ('id', 'converter_task', 'source', 'price_column_to_change', 'new_value')
    readonly_fields = ('id',)
    ordering = ('converter_task', 'price_column_to_change')


admin.site.register(Clients, ClientsAdmin)
admin.site.register(Marks, MarksAdmin)
admin.site.register(Models, ModelsAdmin)
admin.site.register(Generations, GenerationsAdmin)
admin.site.register(ConverterTask, ConverterTaskAdmin)
admin.site.register(StockFields, StockFieldsAdmin)
admin.site.register(PhotoFolder, PhotoFolderAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(ConverterLogsBotData, ConverterLogsBotDataAdmin)
admin.site.register(ConverterFilters, ConverterFiltersAdmin)
admin.site.register(ConverterExtraProcessing, ConverterExtraProcessingAdmin)
admin.site.register(Complectations, ComplectationsAdmin)
admin.site.register(Modifications, ModificationsAdmin)
admin.site.register(ModificationCodes, ModificationCodesAdmin)
