from django.contrib import admin

from applications.calls.models import ClientPrimatelMark, ClientPrimatel


# Register your models here.

class ClientPrimatelMarkInline(admin.TabularInline):
    model = ClientPrimatelMark
    extra = 0


class ClientPrimatelAdmin(admin.ModelAdmin):
    list_display = ('id', 'login', 'name', 'active', 'client')
    list_display_links = ('id', 'login')
    search_fields = ('login', 'name', 'numbers')
    fields = ('id', 'client', 'login', 'name', 'active', 'numbers', 'main_mark', 'price', 'cabinet_primatel')
    readonly_fields = ('id', 'numbers', 'cabinet_primatel')
    inlines = [ClientPrimatelMarkInline]
    save_on_top = True


admin.site.register(ClientPrimatel, ClientPrimatelAdmin)
admin.site.register(ClientPrimatelMark)
