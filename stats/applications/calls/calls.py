import json

from django.http import HttpResponse

from applications.accounts.models import Client
from applications.calls.forms import CallChooseForm
from applications.calls.models import CallPriceSetting, TargetChoice, ChargeTypeChoice, Call
from libs.services.utils import split_daterange


def get_calls_data(request):
    form = CallChooseForm(request.POST)

    if not form.is_valid():
        return HttpResponse(form.errors)

    daterange_str = form.cleaned_data.get('daterange')
    daterange = split_daterange(daterange_str)

    clients_checked = [c for c in request.POST.getlist('client_checkbox')]
    clients_qs = Client.objects.filter(pk__in=clients_checked)
    agency_autoru_links = [(c.name, f'https://agency.auto.ru/calls/?client_id={c.autoru_id}'
                                    f'&from={daterange["from"].strftime("%Y-%m-%d")}'
                                    f'&to={daterange["to"].strftime("%Y-%m-%d")}')
                           for c in clients_qs if c.autoru_id]

    filter_params = {
        'datetime__gte': daterange['from'],
        'datetime__lte': daterange['to'],
        'client_primatel__client_id__in': clients_checked,
    }

    call_data = (
        Call.objects.select_related('mark', 'model', 'client')
        .filter(**filter_params)
        .order_by('client_primatel__client__name', 'datetime')
    )

    filter_params = {
        'daterange': daterange_str,
        'clients_checked': clients_checked,
    }

    context = {
        'form': form,
        'clients_checked': json.dumps(clients_checked),
        'agency_autoru_links': agency_autoru_links,
        'datefrom': daterange['start'],
        'dateto': daterange['end'],
        'datefrom_dt': daterange['from'],
        'dateto_dt': daterange['to'],
        'call_data': call_data,
        'filter_params': filter_params,
    }
    return context


def calculate_call_price(instance, validated_data):
    # TODO проверить все варианты на ошибки
    # Если нецелевой то 0
    if validated_data['target'] not in [TargetChoice.YES.value, TargetChoice.PM_YES.value]:
        return 0

    call_price_settings = CallPriceSetting.objects.filter(client_primatel=validated_data['client_primatel'])
    moderation = f"{{{validated_data['moderation']}}}"

    by_model = call_price_settings.filter(
        charge_type=ChargeTypeChoice.MODEL,
        moderation__contains=moderation,
        mark=validated_data['mark'],
        model=validated_data['model']
    )
    if by_model:
        return by_model[0].price

    by_mark = call_price_settings.filter(
        charge_type=ChargeTypeChoice.MARK,
        moderation__contains=moderation,
        mark=validated_data['mark']
    )
    if by_mark:
        return by_mark[0].price

    by_moderation = call_price_settings.filter(
        charge_type=ChargeTypeChoice.MODERATION,
        moderation__contains=moderation,
    )
    if by_moderation:
        return by_moderation[0].price

    by_main = call_price_settings.filter(
        charge_type=ChargeTypeChoice.MAIN,
    )
    if by_main:
        return by_main[0].price



