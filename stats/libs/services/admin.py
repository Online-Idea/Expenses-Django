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


class GenerationAdmin(admin.ModelAdmin):
    list_display = ('id', marks_mark, models_model, 'generation', 'autoru', 'avito', 'drom', 'human_name')
    list_display_links = ('id', 'generation')
    search_fields = ('mark__mark', 'model__name', 'generation', 'human_name')
    fields = ('id', 'mark', 'model', 'generation', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True

    class Media:
        js = ('js/dynamic_fields.js',)


class ModificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'clients_name', 'short_name', marks_mark, models_model, generations_generation,
                    complectations_complectation, 'body_type', 'engine_volume', 'power', 'transmission', 'engine_type',
                    'drive', 'battery_capacity', 'autoru_modification_id', 'autoru_complectation_id',
                    'avito_modification_id', 'avito_complectation_id', 'load_capacity')
    list_display_links = ('id', 'code', 'clients_name', 'short_name',)
    search_fields = ('code', 'clients_name', 'short_name', 'mark__mark', 'model__name', 'generation__generation',
                     'complectation__complectation')
    fields = (
        'id', 'code', 'clients_name', 'mark', 'model', 'generation', 'complectation', 'body_type', 'engine_volume',
        'power', 'transmission', 'engine_type', 'drive', 'battery_capacity', 'autoru_modification_id',
        'autoru_complectation_id', 'avito_modification_id', 'avito_complectation_id', 'load_capacity')
    readonly_fields = ('id',)
    save_on_top = True

    class Media:
        js = ('js/dynamic_fields.js',)


class ModificationCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'modification', 'complectation')
    list_display_links = ('id', 'code', 'complectation')
    search_fields = ('code',)
    fields = ('id', 'code', 'modification', 'complectation')
    readonly_fields = ('id',)
    save_on_top = True


# TODO прописать актуальные поля
class ComplectationAdmin(admin.ModelAdmin):
    list_display = ('id', modifications_modification, 'complectation', 'teleph', 'autoru', 'avito', 'drom',
                    'human_name')
    list_display_links = ('id', 'complectation')
    search_fields = ('modification', 'complectation', 'human_name')
    fields = ('id', 'modification', 'complectation', 'teleph', 'autoru', 'avito', 'drom', 'human_name')
    readonly_fields = ('id',)
    save_on_top = True

    class Media:
        js = ('js/dynamic_fields.js',)


# admin.site.register(Client, ClientAdmin)
# admin.site.register(Mark, MarkAdmin)
# admin.site.register(Model, ModelAdmin)
# admin.site.register(Generation, GenerationAdmin)
# admin.site.register(Complectation, ComplectationAdmin)
# admin.site.register(Modification, ModificationAdmin)
# admin.site.register(ModificationCode, ModificationCodeAdmin)
