from django.contrib import admin
from django import forms
from django.utils.html import linebreaks, format_html

from applications.autoconverter.models import *


class ActiveConverterTaskFilter(admin.SimpleListFilter):
    # Фильтр для админ панели который показывает только активные ConverterTask
    title = 'Задача Конвертера'
    parameter_name = 'converter_task'

    def lookups(self, request, model_admin):
        # Возвращает список активных ConverterTask
        return [(task.id, task.name) for task in ConverterTask.objects.filter(active=True)]

    def queryset(self, request, queryset):
        # Фильтрует queryset по выбранной ConverterTask если передано значение
        if self.value():
            return queryset.filter(converter_task__id=self.value())
        return queryset


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
                'fields': ['use_converter', 'photos_folder', 'front', 'back', 'interior', 'salon_only', 'template',
                           'stock_fields', 'configuration', 'price', 'add_to_price', 'fill_vin', 'change_vin', ]
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
    list_display = ('active', 'id', 'converter_task', 'field', 'condition', 'value')
    list_display_links = ('id', 'converter_task', 'field')
    list_editable = ('active', 'condition',)
    search_fields = ('converter_task__name', 'field', 'value', 'note')
    list_filter = ('active', ActiveConverterTaskFilter,)
    fields = ('active', 'id', 'converter_task', 'field', 'condition', 'value', 'note')
    readonly_fields = ('id',)
    ordering = ('converter_task', 'active', 'field')


class ConditionalInline(admin.TabularInline):
    model = Conditional
    extra = 0
    readonly_fields = ('duplicate_button', )

    def duplicate_button(self, obj):
        return format_html('<button type="button" onclick="duplicateInline(this);"><i class="fa-solid fa-copy"></i></button>')
    duplicate_button.short_description = 'Дублировать'


class ConverterExtraProcessingNewChangesInline(admin.TabularInline):
    model = ConverterExtraProcessingNewChanges
    extra = 0
    readonly_fields = ('duplicate_button', )

    def duplicate_button(self, obj):
        return format_html('<button type="button" onclick="duplicateInline(this);"><i class="fa-solid fa-copy"></i></button>')
    duplicate_button.short_description = 'Дублировать'


class ConverterExtraProcessingAdmin(admin.ModelAdmin):
    list_display = ('active', 'id', 'converter_task', 'conditionals', 'new_changes')
    list_display_links = ('id', 'converter_task')
    list_editable = ('active', )
    search_fields = ('converter_task__name', 'conditional__value', 'converterextraprocessingnewchanges__new_value')
    list_filter = ('active', ActiveConverterTaskFilter,)
    fields = ('active', 'id', 'converter_task', 'note')
    readonly_fields = ('id',)
    ordering = ('converter_task', 'active', )
    list_per_page = 10
    inlines = [ConditionalInline, ConverterExtraProcessingNewChangesInline]
    save_on_top = True

    class Media:
        js = ('js/dynamic_fields.js', 'js/duplicate_inline.js', )

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

    # def formfield_for_dbfield(self, db_field, **kwargs):
    #     if db_field.name == 'new_value':
    #         kwargs['widget'] = forms.Textarea(attrs={'rows': 5, 'cols': 40})
    #     return super().formfield_for_dbfield(db_field, **kwargs)

admin.site.register(ConverterTask, ConverterTaskAdmin)
admin.site.register(StockFields, StockFieldsAdmin)
admin.site.register(PhotoFolder, PhotoFolderAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(ConverterLogsBotData, ConverterLogsBotDataAdmin)
admin.site.register(ConverterFilter, ConverterFilterAdmin)
admin.site.register(ConverterExtraProcessing, ConverterExtraProcessingAdmin)
