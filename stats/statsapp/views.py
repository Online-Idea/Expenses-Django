import urllib.parse

import pandas as pd
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.views.generic import ListView, FormView, DetailView
from django.db.models import *
from django.contrib import messages

import datetime
import calendar
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from .models import *
from .forms import *
from .converter import *
from .autoru import get_autoru_products, autoru_authenticate, update_autoru_catalog, update_autoru_regions
from .utils import xlsx_column_width


def home(request):
    if request.method == 'POST':
        form = ClientsChooseForm(request.POST)

        daterange = form['daterange'].value().split(' ')
        # Разбиваю дату на день, месяц, год
        date_start = [int(i) for i in daterange[0].split('.')]
        date_end = [int(i) for i in daterange[2].split('.')]
        datefrom = datetime.datetime(date_start[2], date_start[1], date_start[0], 00, 00, 00, 629013)
        dateto = datetime.datetime(date_end[2], date_end[1], date_end[0], 19, 59, 59, 629013)
        # Выбранные клиенты
        clients_checked = [c for c in request.POST.getlist('client_checkbox')]

        # Таблица себестоимости
        # Беру данные из базы
        # TODO возможно что это можно упростить, смотри на auction
        stats = Clients.objects \
            .values('id', 'name', 'charge_type', 'commission_size', 'autoru_id', 'teleph_id') \
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
            platform = calls_sum + products_sum

            if client['charge_type'] == Clients.CALLS:  # звонки
                try:
                    teleph_calls_sum = telephcalls_dict[client['teleph_id']]['teleph_calls_sum']
                except KeyError:
                    teleph_calls_sum = 0
            elif client['charge_type'] == Clients.COMMISSION_PERCENT:  # комиссия процент
                teleph_calls_sum = platform + (platform * client['commission_size'] / 100)
            elif client['charge_type'] == Clients.COMMISSION_SUM:  # комиссия сумма
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

            if client['charge_type'] == Clients.CALLS:
                client['margin'] = round(client['client_cost'] - client['call_cost'], 2)  # Маржа
                client['profit'] = round(client['margin'] * teleph_target, 2)  # Заработок
            elif client['charge_type'] == Clients.COMMISSION_PERCENT:
                client['margin'] = client['profit'] = platform * client['commission_size'] / 100
            elif client['charge_type'] == Clients.COMMISSION_SUM:
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
        subtotal['calls_cost'] = round(subtotal['platform'] / subtotal['teleph_target'], 2)
        subtotal['client_cost'] = round(subtotal['teleph_calls_sum'] / subtotal['teleph_target'], 2)
        subtotal['margin'] = round(subtotal['client_cost'] - subtotal['calls_cost'], 2)
        subtotal['profit'] = round(subtotal['margin'] * subtotal['teleph_target'], 2)
        # Конец таблицы себестоимости

        context = {
            'form': form,
            'clients_checked': json.dumps(clients_checked),
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
    dayto = today.day - 1 if today.day > 1 else 1
    dateto = datetime.date(year, month, dayto).strftime('%d.%m.%Y')
    context = {
        'form': form,
        'datefrom': datefrom,
        'dateto': dateto,
        'clients': clients,
    }
    return render(request, 'statsapp/index.html', context)


class ConverterManual(SuccessMessageMixin, FormView):
    template_name = 'statsapp/converter_manual.html'
    ordering = ['client']
    form_class = ConverterManualForm
    success_url = 'converter'
    success_message = format_html('Готово, файлы в <a href="https://t.me/ConverterLogsBot">телеграме</a>')

    def form_valid(self, form):
        tasks = form.cleaned_data['task_checkbox']
        for task in tasks:
            get_price(ConverterTask.objects.get(pk=task.id))
        return super().form_valid(form)


def get_auction_data(request):
    """
    Возвращает данные истории аукциона по форме с сайта.
    Вынес это отдельно чтобы использовать для разных кнопок
    :param request:
    :return: context с данными формы и с Django QuerySet с историей аукциона
    """
    form = AuctionChooseForm(request.POST)

    daterange = form['daterange'].value().split(' ')
    # Разбиваю дату на день, месяц, год
    date_start = [int(i) for i in daterange[0].split('.')]
    date_end = [int(i) for i in daterange[2].split('.')]
    datefrom = datetime.datetime(date_start[2], date_start[1], date_start[0], 00, 00, 00, 629013)
    dateto = datetime.datetime(date_end[2], date_end[1], date_end[0], 23, 59, 59, 629013)
    # Выбранные марки
    marks_checked = [m for m in request.POST.getlist('mark_checkbox')]
    # Выбранные регионы
    regions_checked = [r for r in request.POST.getlist('region_checkbox')]
    # Данные истории аукциона
    auction_data = (
        AutoruAuctionHistory.objects.select_related(
            "mark", "model", "client"
        )
        .filter(
            datetime__gte=datefrom,
            datetime__lte=dateto,
            mark_id__in=marks_checked,
            autoru_region__in=regions_checked,
        )
        .order_by("-datetime", "autoru_region", "mark", "model", "position")
    )
    context = {
        'form': form,
        'marks_checked': json.dumps(marks_checked),
        'regions_checked': json.dumps(regions_checked),
        'datefrom': date_start,
        'dateto': date_end,
        'auction_data': auction_data,
    }
    return context


def auction(request):
    if request.method == 'POST':

        context = get_auction_data(request)

        # График plotly, только по одной марке и одному региону
        if len(context['marks_checked']) == 1 and len(context['regions_checked']) == 1 and context['auction_data']:
            auction_data_values = list(
                context['auction_data'].values("datetime", "autoru_region", "mark__mark", "model__model", "position",
                                               "bid", "competitors", "client__name"))

            df = pd.DataFrame.from_records(auction_data_values)

            df = df.rename(columns={"mark__mark": "mark", "model__model": "model", "client__name": "client"})

            # Только первая позиция
            df = df[df['position'] == 1]

            uniq_models = df['model'].unique()

            fig = make_subplots(rows=len(uniq_models), cols=1, subplot_titles=uniq_models)

            for i, model in enumerate(uniq_models):
                data = df[df['model'] == model]
                fig.add_trace(
                    go.Scatter(x=data['datetime'], y=data['bid']),
                    row=i + 1, col=1
                )
            fig_title = f'{df["autoru_region"][0]}<br>{df["mark"][0]}'
            fig.update_layout(title_text=fig_title, showlegend=False,
                              height=len(uniq_models) * 200, margin={'t': 130, 'b': 130})
            fig.update_yaxes(tickformat=',.0f')

            # Generate the HTML code for the plot
            plot_html = fig.to_html(full_html=False)
            context['plot_html'] = plot_html

        return render(request, 'statsapp/auction.html', context)

    else:
        form = AuctionChooseForm()

    marks = Marks.objects.all()
    today = datetime.date.today()
    year = today.year
    month = today.month
    # datefrom = datetime.date(year, month, 1).strftime('%d.%m.%Y')
    # dayto = today.day if today.day > 1 else 1
    # dateto = datetime.date(year, month, dayto).strftime('%d.%m.%Y')
    context = {
        'form': form,
        # 'datefrom': datefrom,
        # 'dateto': dateto,
        'datefrom': today,
        'dateto': today,
        'clients': marks,
    }
    return render(request, 'statsapp/auction.html', context)


def download_auction(request):
    context = get_auction_data(request)

    wb = Workbook()
    ws = wb.active
    headers = ['id', 'Дата и время', 'Регион', 'Марка', 'Модель', 'Позиция', 'Ставка', 'Имя клиента',
               'Количество конкурентов']
    ws.append(headers)
    data = context['auction_data'].values_list('id', 'datetime', 'autoru_region', 'mark__mark', 'model__model',
                                               'position', 'bid', 'client__name', 'competitors')
    for row in data:
        row = [dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo else dt for dt in row]
        ws.append(row)

    ws = xlsx_column_width(ws)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    datefrom = datetime.date(*context['datefrom'][::-1]).strftime("%d.%m.%Y")
    dateto = datetime.date(*context['dateto'][::-1]).strftime("%d.%m.%Y")
    filename = f'Аукцион {datefrom}-{dateto}.xlsx'
    filename = urllib.parse.quote(filename)
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'

    wb.save(response)

    return response



def photo_folders(request):
    get_photo_folders()
    return redirect('home')


def configurations(request):
    get_configurations()
    return redirect('home')


def autoru_catalog(request):
    update_autoru_catalog()
    return redirect('home')


def autoru_regions(request):
    update_autoru_regions()
    return redirect('home')


def get_models_for_mark(request, mark_id):
    models = Models.objects.filter(mark_id=mark_id).values('id', 'mark', 'model')
    return JsonResponse(list(models), safe=False)
