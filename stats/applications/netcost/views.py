import datetime
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.http import HttpResponse
from django.shortcuts import render

from libs.autoru.models import AutoruCall, AutoruProduct
from libs.services.decorators import allowed_users
from libs.services.forms import ClientChooseForm
# from libs.services.models import Client
from libs.services.utils import split_daterange
from libs.teleph.models import TelephCall
from applications.accounts.models import Client


@login_required(login_url='login')
@allowed_users(allowed_groups=['admin'])
def home(request):
    if request.method == 'POST':
        form = ClientChooseForm(request.POST)

        if not form.is_valid():
            return HttpResponse(status=400)

        daterange = split_daterange(form.cleaned_data.get('daterange'))

        # Выбранные клиенты
        clients_checked = [c for c in request.POST.getlist('client_checkbox')]

        # Таблица себестоимости
        # Беру данные из базы
        # TODO возможно что это можно упростить, смотри на auction
        stats = Client.objects \
            .values('id', 'name', 'charge_type', 'commission_size', 'autoru_id', 'teleph_id') \
            .filter(id__in=clients_checked)
        autorucalls = AutoruCall.objects \
            .values('client_id') \
            .filter(datetime__gte=daterange['from'], datetime__lte=daterange['to']) \
            .annotate(calls_sum=Sum('billing_cost'))
        autoruproducts = AutoruProduct.objects \
            .values('client_id') \
            .filter(date__gte=daterange['from'], date__lte=daterange['to']) \
            .annotate(products_sum=Sum('total'))
        telephcalls = TelephCall.objects \
            .values('client_id') \
            .filter((Q(datetime__gte=daterange['from']) & Q(datetime__lte=daterange['to']))
                    & (Q(target='Да') | Q(target='ПМ - Целевой'))
                    & Q(moderation__startswith='М')) \
            .annotate(teleph_calls_sum=Sum('call_price'), teleph_target=Count('target'))
        autorucalls_dict = {}
        for row in autorucalls:
            autorucalls_dict[row['client_id']] = {'calls_sum': row['calls_sum']}
        autoruproducts_dict = {}
        for row in autoruproducts:
            autoruproducts_dict[row['client_id']] = {'products_sum': row['products_sum']}
        telephcalls_dict = {}
        for row in telephcalls:
            telephcalls_dict[row['client_id']] = {'teleph_calls_sum': row['teleph_calls_sum'],
                                                  'teleph_target': row['teleph_target']}

        # Форматирую для вывода
        for client in stats:
            try:
                calls_sum = autorucalls_dict[client['autoru_id']]['calls_sum']
            except KeyError:
                calls_sum = 0
            try:
                products_sum = autoruproducts_dict[client['autoru_id']]['products_sum']
            except KeyError:
                products_sum = 0
            platform = calls_sum + products_sum

            if client['charge_type'] == Client.ChargeType.CALLS:  # звонки
                try:
                    teleph_calls_sum = telephcalls_dict[client['teleph_id']]['teleph_calls_sum']
                except KeyError:
                    teleph_calls_sum = 0
            elif client['charge_type'] == Client.ChargeType.COMMISSION_PERCENT:  # комиссия процент
                teleph_calls_sum = platform + (platform * client['commission_size'] / 100)
            elif client['charge_type'] == Client.ChargeType.COMMISSION_SUM:  # комиссия сумма
                teleph_calls_sum = platform + client['commission_size']
            else:
                teleph_calls_sum = 0
            # Если у клиента вообще нет суммы по звонкам
            teleph_calls_sum = 0 if not teleph_calls_sum else teleph_calls_sum

            try:
                teleph_target = telephcalls_dict[client['teleph_id']]['teleph_target']
            except KeyError:
                teleph_target = 0

            client['calls_sum'] = calls_sum  # Траты на звонки
            client['products_sum'] = products_sum  # Траты на услуги
            client['teleph_calls_sum'] = teleph_calls_sum  # Приход с площадки
            client['teleph_target'] = teleph_target  # Звонки с площадки
            client['platform'] = platform  # Траты на площадку
            if teleph_target > 0:
                client['call_cost'] = round(client['platform'] / teleph_target, 2)  # Цена звонка
                client['client_cost'] = round(teleph_calls_sum / teleph_target, 2)  # Цена клиента
            else:
                client['call_cost'] = client['client_cost'] = 0

            if client['charge_type'] == Client.ChargeType.CALLS:
                client['margin'] = round(client['client_cost'] - client['call_cost'], 2)  # Маржа
                client['profit'] = round(client['margin'] * teleph_target, 2)  # Заработок
            elif client['charge_type'] == Client.ChargeType.COMMISSION_PERCENT:
                client['margin'] = client['profit'] = platform * client['commission_size'] / 100
            elif client['charge_type'] == Client.ChargeType.COMMISSION_SUM:
                client['margin'] = client['profit'] = client['commission_size']

        # Удаляю клиентов с пустыми данными
        stats = list(filter(lambda x: not (sum([x['client_cost'], x['margin'], x['profit']]) == 0), stats))

        # Суммы столбцов
        subtotal = {
            'teleph_calls_sum': 0,
            'platform': 0,
            'calls_sum': 0,
            'products_sum': 0,
            'teleph_target': 0,
            'calls_cost': 0,
            'client_cost': 0,
            'margin': 0,
            'profit': 0
        }
        for client in stats:
            subtotal['teleph_calls_sum'] += client['teleph_calls_sum']
            subtotal['platform'] += client['platform']
            subtotal['calls_sum'] += client['calls_sum']
            subtotal['products_sum'] += client['products_sum']
            subtotal['teleph_target'] += client['teleph_target']
        subtotal['calls_cost'] = round(subtotal['platform'] / subtotal['teleph_target'], 2) if subtotal['teleph_target'] > 0 else 0
        subtotal['client_cost'] = round(subtotal['teleph_calls_sum'] / subtotal['teleph_target'], 2) if subtotal['client_cost'] > 0 else 0
        subtotal['margin'] = round(subtotal['client_cost'] - subtotal['calls_cost'], 2) if subtotal['margin'] > 0 else 0
        subtotal['profit'] = round(subtotal['margin'] * subtotal['teleph_target'], 2) if subtotal['profit'] > 0 else 0
        # Конец таблицы себестоимости

        context = {
            'form': form,
            'clients_checked': json.dumps(clients_checked),
            'datefrom': daterange['start'],
            'dateto': daterange['end'],
            'stats': stats,
            'subtotal': subtotal,
        }
        return render(request, 'netcost/netcost.html', context)

    else:
        form = ClientChooseForm()

    clients = Client.objects.filter(active=True)
    today = datetime.date.today()
    year = today.year
    month = today.month
    datefrom = datetime.date(year, month, 1).strftime('%d.%m.%Y')
    dayto = today.day - 1 if today.day > 1 else 1
    dateto = datetime.date(year, month, dayto).strftime('%d.%m.%Y')
    context = {
        'form': form,
        'datefrom': datefrom,
        'dateto': dateto,
        'clients': clients,
    }
    return render(request, 'netcost/netcost.html', context)
