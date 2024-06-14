from django.contrib import admin
from django.utils.html import format_html

from applications.calls.models import ClientPrimatelMark, ClientPrimatel, CallPriceSetting, ChargeTypeChoice, \
    ModerationChoice, CalltouchSetting
from libs.services.models import Model, Mark


# Register your models here.

class ClientPrimatelMarkInline(admin.TabularInline):
    model = ClientPrimatelMark
    extra = 0


class CallPriceSettingInline(admin.TabularInline):
    model = CallPriceSetting
    extra = 0
    readonly_fields = ('duplicate_button', )

    def duplicate_button(self, obj):
        return format_html('<button type="button" onclick="duplicateInline(this);"><i class="fa-solid fa-copy"></i></button>')
    duplicate_button.short_description = 'Дублировать'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        client_primatel = request.resolver_match.kwargs.get("object_id")
        marks = ClientPrimatelMark.objects.filter(client_primatel=client_primatel).values_list('mark__id', flat=True)
        if db_field.name == "mark":
            kwargs["queryset"] = Mark.objects.filter(id__in=marks)
        elif db_field.name == "model":
            kwargs['queryset'] = Model.objects.filter(mark__in=marks)
        return super(CallPriceSettingInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class CalltouchSettingInline(admin.TabularInline):
    model = CalltouchSetting
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        client_primatel = request.resolver_match.kwargs.get("object_id")
        marks = ClientPrimatelMark.objects.filter(client_primatel=client_primatel).values_list('mark_id', flat=True)
        if db_field.name == "mark":
            kwargs['queryset'] = Mark.objects.filter(id__in=marks)
        return super(CalltouchSettingInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ClientPrimatelAdmin(admin.ModelAdmin):
    list_display = ('id', 'login', 'name', 'active', 'client')
    list_display_links = ('id', 'login')
    search_fields = ('login', 'name', 'numbers')
    fields = ('id', 'client', 'login', 'name', 'active', 'numbers', 'cabinet_primatel')
    readonly_fields = ('id', 'numbers', 'cabinet_primatel')
    inlines = [ClientPrimatelMarkInline, CallPriceSettingInline, CalltouchSettingInline]
    save_on_top = True

    class Media:
        js = ('js/dynamic_fields.js', 'js/duplicate_inline.js', )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for call_price_setting in obj.call_price_settings.all():
            charge_type = call_price_setting.charge_type

            if charge_type == ChargeTypeChoice.MAIN.value:
                choice_values = [item[0] for item in ModerationChoice.choices]
                call_price_setting.moderation = f'{{{",".join(choice_values)}}}'

            call_price_setting.save()


admin.site.register(ClientPrimatel, ClientPrimatelAdmin)
