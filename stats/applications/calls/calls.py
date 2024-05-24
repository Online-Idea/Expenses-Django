import json

from applications.calls.forms import CallChooseForm
from applications.calls.models import CallPriceSetting, TargetChoice, ChargeTypeChoice
from libs.services.utils import split_daterange


def get_calls_data(request, form):
    daterange_str = form.cleaned_data.get('daterange')
    daterange = split_daterange(daterange_str)

    clients_checked = [c for c in request.POST.getlist('client_checkbox')]

    filter_params = {
        'daterange': daterange_str,
        'clients_checked': clients_checked,
    }

    context = {
        'form': form,
        'clients_checked': json.dumps(clients_checked),
        'datefrom': daterange['start'],
        'dateto': daterange['end'],
        'datefrom_dt': daterange['from'],
        'dateto_dt': daterange['to'],
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



