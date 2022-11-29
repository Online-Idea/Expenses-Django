from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView
from django.db.models import *

import datetime
import calendar

from .models import *
from .forms import *


# Create your views here.
def home(request):
    if request.method == 'POST':
        form = ClientsChooseForm(request.POST)

        daterange = form['daterange'].value().split(' ')
        # Разбиваю дату на день, месяц, год
        date_start = [int(i) for i in daterange[0].split('.')]
        date_end = [int(i) for i in daterange[2].split('.')]
        datefrom = datetime.datetime(date_start[2], date_start[1], date_start[0], 00, 00, 00, 629013, tzinfo=datetime.timezone.utc)
        dateto = datetime.datetime(date_end[2], date_end[1], date_end[0], 23, 59, 59, 629013, tzinfo=datetime.timezone.utc)
        # Выбранные клиенты
        clients_checked = [c for c in request.POST.getlist('client_checkbox')]

        # Таблица себестоимости
        # Беру данные из базы
        stats = Clients.objects \
            .values('id', 'name', 'autoru_id', 'teleph_id') \
            .filter(id__in=clients_checked)
        autorucalls = AutoruCalls.objects \
            .values('client_id') \
            .filter(datetime__gte=datefrom, datetime__lte=dateto) \
            .annotate(calls_sum=Sum('billing_cost'))
        autoruproducts = AutoruProducts.objects \
            .values('client_id') \
            .filter(date__gte=datefrom, date__lte=dateto) \
            .annotate(products_sum=Sum('total'))
        telephcalls = TelephCalls.objects \
            .values('client_id') \
            .filter((Q(datetime__gte=datefrom) & Q(datetime__lte=dateto))
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
            try:
                teleph_calls_sum = telephcalls_dict[client['teleph_id']]['teleph_calls_sum']
                teleph_target = telephcalls_dict[client['teleph_id']]['teleph_target']
            except KeyError:
                teleph_calls_sum = 0
                teleph_target = 0

            client['calls_sum'] = calls_sum  # Траты на звонки
            client['products_sum'] = products_sum  # Траты на услуги
            client['teleph_calls_sum'] = teleph_calls_sum  # Приход с площадки
            client['teleph_target'] = teleph_target  # Звонки с площадки
            client['platform'] = calls_sum + products_sum  # Траты на площадку
            if teleph_target > 0:
                client['call_cost'] = round(client['platform'] / teleph_target, 2)  # Цена звонка
                client['client_cost'] = round(teleph_calls_sum / teleph_target, 2)  # Цена клиента
            else:
                client['call_cost'] = client['client_cost'] = 0
            client['margin'] = round(client['client_cost'] - client['call_cost'], 2)  # Маржа
            client['profit'] = round(client['margin'] * teleph_target, 2)  # Заработок

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
        subtotal['calls_cost'] = round(subtotal['platform'] / subtotal['teleph_target'], 2)
        subtotal['client_cost'] = round(subtotal['teleph_calls_sum'] / subtotal['teleph_target'], 2)
        subtotal['margin'] = round(subtotal['client_cost'] - subtotal['calls_cost'], 2)
        subtotal['profit'] = round(subtotal['margin'] * subtotal['teleph_target'], 2)
        # Конец таблицы себестоимости

        context = {
            'form': form,
            'clients_checked': clients_checked,
            'datefrom': date_start,
            'dateto': date_end,
            'stats': stats,
            'subtotal': subtotal,
        }
        return render(request, 'statsapp/index.html', context)

    else:
        form = ClientsChooseForm()

    clients = Clients.objects.filter(active=True)
    today = datetime.date.today()
    year = today.year
    month = today.month
    datefrom = datetime.date(year, month, 1).strftime('%d.%m.%Y')
    dateto = datetime.date(year, month, today.day - 1).strftime('%d.%m.%Y')
    context = {
        'form': form,
        'datefrom': datefrom,
        'dateto': dateto,
        'clients': clients,
    }
    return render(request, 'statsapp/index.html', context)
