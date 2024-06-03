from django.contrib import admin
from django import forms
from django.utils.html import linebreaks

from applications.autoconverter.models import *


class ConverterTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'name', 'active', 'photos_folder', 'configuration')
    list_display_links = ('id', 'client', 'name')
    list_editable = ('active',)
    search_fields = ('name',)
    list_filter = ('client', 'active')
    # fields = ('id', 'client', 'name', 'stock_source', 'stock_url', 'stock_post_host', 'stock_post_login',
    #           'stock_post_password', 'active', 'photos_folder', 'front', 'back', 'interior', 'salon_only', 'template',
    #           'stock_fields', 'configuration', 'price', 'notifications_email', 'import_to_onllline',
    #           'onllline_salon_to_import', 'onllline_import_mode', 'onllline_import_options',
    #           'onllline_import_multiply_price', 'export_to_onllline', 'export_to_websites')
    fieldsets = [
        (
            None,
            {
                'fields': ['id', 'active', 'client', 'name', 'slug', 'notifications_email', ],
            },
        ),
        (
            'Сток',
            {
                'fields': ['stock_source', 'stock_url', 'stock_post_host', 'stock_post_login', 'stock_post_password',],
            },
        ),
        (
            'Конвертер',
            {
                'fields': ['photos_folder', 'front', 'back', 'interior', 'salon_only', 'template', 'stock_fields',
                           'configuration', 'price', 'add_to_price', ]
            },
        ),
        (
            'База onllline.ru',
            {
                'fields': ['import_to_onllline', 'onllline_salon_to_import', 'onllline_import_mode',
                           'onllline_import_options', 'onllline_import_multiply_price', 'export_to_onllline',
                           'export_to_websites']
            }
        )
    ]
    readonly_fields = ('id', 'template', 'price')
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
    extra = 0


class ConverterExtraProcessingNewChangesInline(admin.TabularInline):
    model = ConverterExtraProcessingNewChanges
    extra = 0


class ConverterExtraProcessingAdmin(admin.ModelAdmin):
    inlines = [ConditionalInline, ConverterExtraProcessingNewChangesInline]
    list_display = ('id', 'converter_task', 'conditionals', 'new_changes')
    list_display_links = ('id', 'converter_task')
    search_fields = ('converter_task__name', 'conditional__value', 'converterextraprocessingnewchanges__new_value')
    list_filter = ('converter_task',)
    fields = ('id', 'converter_task')
    readonly_fields = ('id',)
    ordering = ('converter_task', )
    list_per_page = 10

    def conditionals(self, obj):
        conditionals_objs = Conditional.objects.filter(converter_extra_processing=obj)
        as_str = [str(o) for o in conditionals_objs]
        replaced_name = [o.replace(str(obj), '') for o in as_str]
        return '; '.join(replaced_name)
    conditionals.short_description = 'Условия'

    def new_changes(self, obj):
        new_changes_objs = ConverterExtraProcessingNewChanges.objects.filter(converter_extra_processing=obj)
        as_str = [str(o) for o in new_changes_objs]
        replaced_name = [o.replace(str(obj), '') for o in as_str]
        return '; '.join(replaced_name)
    new_changes.short_description = 'Новые значения'

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'new_value':
            kwargs['widget'] = forms.Textarea(attrs={'rows': 5, 'cols': 40})
        return super().formfield_for_dbfield(db_field, **kwargs)


admin.site.register(ConverterTask, ConverterTaskAdmin)
admin.site.register(StockFields, StockFieldsAdmin)
admin.site.register(PhotoFolder, PhotoFolderAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(ConverterLogsBotData, ConverterLogsBotDataAdmin)
admin.site.register(ConverterFilter, ConverterFilterAdmin)
admin.site.register(ConverterExtraProcessing, ConverterExtraProcessingAdmin)
