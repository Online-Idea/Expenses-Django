from django.contrib import admin

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

    # def get_form(self, request, obj=None, **kwargs):
    #     form_class = super().get_form(request, obj, **kwargs)
    #     if obj and hasattr(obj, 'client_primatel'):
    #         # Dynamically set the queryset for the mark field based on the current client primatel
    #         current_marks = ClientPrimatelMark.objects.filter(client_primatel=obj.client_primatel)
    #         form_class.base_fields['mark'].queryset = current_marks.values_list('mark__mark', flat=True)
    #         form_class.base_fields['model'].queryset = Model.objects.filter(mark__in=current_marks)
    #     return form_class

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
        js = ('js/dynamic_fields.js',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for call_price_setting in obj.call_price_settings.all():
            charge_type = call_price_setting.charge_type

            if charge_type == ChargeTypeChoice.MAIN.value:
                choice_values = [item[0] for item in ModerationChoice.choices]
                call_price_setting.moderation = f'{{{",".join(choice_values)}}}'

            call_price_setting.save()


admin.site.register(ClientPrimatel, ClientPrimatelAdmin)
# admin.site.register(ClientPrimatelMark)
