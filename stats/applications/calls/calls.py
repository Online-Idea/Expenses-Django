import calendar
import datetime
import json
import time

import pandas as pd
from django.db.models import Max, QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils.http import urlencode

from applications.accounts.models import Client
from applications.calls.models import CallPriceSetting, TargetChoice, ChargeTypeChoice, Call, Plan
from libs.services.forms import ClientChooseForm
from libs.services.utils import split_daterange, get_all_fields_verbose_names


def get_calls_data(request):
    form = get_and_validate_form(request)

    daterange_str = form.cleaned_data.get('daterange')
    daterange = split_daterange(daterange_str)

    clients_checked = [c for c in request.POST.getlist('client_checkbox')]
    clients_qs = Client.objects.filter(pk__in=clients_checked)

    call_filters = {
        'datetime__gte': daterange['from'],
        'datetime__lte': daterange['to'],
        'client_primatel__client_id__in': clients_checked,
        'deleted': False,
    }

    filter_params = {
        'daterange': daterange_str,
        'clients_checked': clients_checked,
        'deleted': False,
    }

    last_updated = get_last_updated_call_datetime()

    context = {
        'form': form,
        'clients_checked': json.dumps(clients_checked),
        'clients_qs': clients_qs,
        'datefrom': daterange['start'],
        'dateto': daterange['end'],
        'datefrom_dt': daterange['from'],
        'dateto_dt': daterange['to'],
        'call_filters': call_filters,
        'filter_params': filter_params,
        'last_updated': last_updated,
    }
    return context


def get_last_updated_call_datetime():
    """
    Возвращает дату последнего звонка
    :return:
    """
    return Call.objects.aggregate(Max('datetime'))['datetime__max']


def get_and_validate_form(request):
    form = ClientChooseForm(request.POST)
    return form if form.is_valid() else HttpResponse(form.errors)


def make_agency_autoru_links(clients_qs: QuerySet[Client], datefrom: datetime, dateto: datetime) -> list:
    """
    Делает ссылки на кабинеты авто.ру
    :param clients_qs:
    :param datefrom:
    :param dateto:
    :return:
    """
    return [(c.name, f'https://agency.auto.ru/calls/?client_id={c.autoru_id}'
                     f'&from={datefrom.strftime("%Y-%m-%d")}'
                     f'&to={dateto.strftime("%Y-%m-%d")}')
            for c in clients_qs if c.autoru_id]


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


def dates_for_daterange(end_of_month: bool = False):
    """
    Период дат для формы на сайте. По умолчанию от первого дня текущего месяца до сегодняшнего дня.
    Если end_of_month то датой до будет последний день текущего месяца.
    :param end_of_month:
    :return:
    """
    today = datetime.date.today()
    year = today.year
    month = today.month
    if end_of_month:
        day_to = calendar.monthrange(year, month)[1]
    else:
        day_to = today.day
    datefrom = datetime.date(year, month, 1).strftime('%d.%m.%Y')
    dateto = datetime.date(year, month, day_to).strftime('%d.%m.%Y')
    return datefrom, dateto


def prepare_pivot_data(queryset: QuerySet[Call]):
    """
    Готовит данные звонков для WebDataRocks
    :param queryset:
    :return:
    """
    values = ['datetime', 'num_from', 'num_to', 'num_redirect', 'duration', 'client_primatel__client__name',
              'mark__mark', 'model__model', 'target', 'moderation', 'call_price', 'status']

    result = [{
        # 'datetime': obj['datetime'].isoformat(),  # Такой вид разбивает на отдельные столбцы: День, Месяц, Год
        'datetime': obj['datetime'].strftime('%d.%m.%Y'),
        'num_from': obj['num_from'],
        'num_to': obj['num_to'],
        # 'num_redirect': obj['num_redirect'],
        # 'duration': obj['duration'],
        'client_primatel__client__name': obj['client_primatel__client__name'],
        'mark__mark': obj['mark__mark'],
        'model__model': obj['model__model'],
        'target': obj['target'],
        'moderation': obj['moderation'],
        'call_price': int(obj['call_price']) if obj['call_price'] else 0,
        'status': obj['status'],
    }
        for obj in queryset.values(*values)]

    # Русские названия столбцов
    verbose_names = get_all_fields_verbose_names(Call)
    verbose_names['datetime'] = 'Дата'
    verbose_names['client_primatel__client__name'] = 'Клиент'
    verbose_names['moderation'] = 'Площадка'
    result_verbose_names = []
    for item in result:
        verbose_item = {verbose_names.get(k, k): v for k, v in item.items()}
        result_verbose_names.append(verbose_item)

    return json.dumps(result_verbose_names, default=lambda o: 'null' if o is None else o)


def get_calls_pivot_data(calls_qs: QuerySet[Call], datefrom: datetime, dateto: datetime) -> dict:
    """
    Данные сводной таблицы звонков
    :param calls_qs:
    :param dateto:
    :param datefrom:
    :return:
    """
    df = pd.DataFrame.from_records(calls_qs)
    df = df.rename(columns={
        'client_primatel__client__id': 'client_id',
        'client_primatel__client__name': 'client_name'
    })
    df['day'] = df['datetime'].dt.date

    client_order = df['client_id'].drop_duplicates()

    pivot_data = {}
    # Сводные pandas. all - всего звонков, yes - всего целевых звонков
    pivot_df_all = pd.pivot_table(
        df,
        index='day',
        columns='client_id',
        values=['datetime'],
        aggfunc='count',
        fill_value=0,
        sort=False
    )
    pivot_df_yes = pd.pivot_table(
        df[df['target'].isin([TargetChoice.YES, TargetChoice.PM_YES])],
        index='day',
        columns='client_id',
        values=['datetime'],
        aggfunc='count',
        fill_value=0,
        sort=False
    )
    # Итоги по строкам
    row_totals_all = pivot_df_all.sum(axis=1)
    row_totals_yes = pivot_df_yes.sum(axis=1)

    # Данные таблицы
    for day, row in pivot_df_all.iterrows():
        client_counts = []
        timestamp = time.mktime(day.timetuple())  # Для правильной сортировки в DataTables
        # day_fmt = datetime.datetime.strftime(day, '%d-%m-%Y')
        row_total_all = row_totals_all[row_totals_all.index == day]
        row_total_all = row_total_all.iloc[0] if not row_total_all.empty else 0
        row_total_yes = row_totals_yes[row_totals_yes.index == day]
        row_total_yes = row_total_yes.iloc[0] if not row_total_yes.empty else 0

        for client, count in row.items():
            if day in pivot_df_yes.index and client in pivot_df_yes.columns:
                target_total_yes = pivot_df_yes.loc[day, client]
            else:
                target_total_yes = 0
            full_url = make_url_for_day_and_client([client[1]], day, day)
            client_counts.append({
                'target_total_all': count,
                'target_total_yes': target_total_yes,
                'link': full_url,
            })

        day_url = make_url_for_day_and_client(client_order.tolist(), day, day)
        pivot_data[day] = {
            'timestamp': timestamp,
            'row_total_all': row_total_all,
            'row_total_yes': row_total_yes,
            'data': client_counts,
            'day_url': day_url,
        }

    # Итоги по столбцам
    transposed_df_all = pivot_df_all.T
    column_totals_all = transposed_df_all.sum(axis=1)
    transposed_df_yes = pivot_df_yes.T
    column_totals_yes = transposed_df_yes.sum(axis=1)
    client_urls = [make_url_for_day_and_client([client], datefrom, dateto) for client in client_order.tolist()]
    combined_totals = pd.DataFrame({
        'column_totals_all': column_totals_all,
        'column_totals_yes': column_totals_yes,
    })
    convert_columns = ['column_totals_all', 'column_totals_yes']
    combined_totals[convert_columns] = combined_totals[convert_columns].fillna(0)
    combined_totals[convert_columns] = combined_totals[convert_columns].astype(int)
    # Сортирую обратно как было в column_totals_all чтобы был верный порядок
    combined_totals = combined_totals.loc[column_totals_all.index]
    combined_totals['client_urls'] = client_urls
    combined_totals = combined_totals.to_dict(orient='records')
    grand_total_url = make_url_for_day_and_client(client_order.tolist(), datefrom, dateto)
    pivot_grand_totals = {
        'totals_all_sum': column_totals_all.sum(),
        'totals_yes_sum': column_totals_yes.sum(),
        'combined_totals': combined_totals,
        'grand_total_url': grand_total_url,
    }

    # Бюджет
    total_budget = df.call_price.sum()
    total_budget = total_budget.astype(int) if total_budget else 0
    budget_by_client = df.groupby('client_id')['call_price'].sum().astype(int)
    budget_by_client = budget_by_client.loc[client_order]
    budget = [total_budget] + budget_by_client.to_list()

    # План
    plan_queryset = Plan.objects.filter(client_primatel__client__in=client_order)
    plan_data = []
    if plan_queryset:
        for plan in plan_queryset:
            dates = pd.date_range(plan.datefrom, plan.dateto)
            plan_for_days = [plan.plan_for_day] * len(dates)
            clients = [plan.client_primatel.client.id] * len(dates)
            for date, plan_for_day, client in zip(dates, plan_for_days, clients):
                plan_data.append({'date': date, 'plan_for_day': plan_for_day, 'client_id': client})
        df_plan = pd.DataFrame(plan_data)
        filtered_by_daterange = df_plan[(df_plan.date >= datefrom) & (df_plan.date <= dateto)]
        total_plan = filtered_by_daterange.plan_for_day.sum().astype(int)
        grouped_by_client = filtered_by_daterange.groupby('client_id')['plan_for_day'].sum().astype(int)
        grouped_by_client = grouped_by_client.reindex(client_order)
        plan_by_client = grouped_by_client.fillna(0).astype(int).replace(0, '-').tolist()
        plan = [total_plan] + plan_by_client
    else:
        plan = ['-'] * len(budget)

    # Процент плана
    percent_plan = [round(budget[i] / plan[i] * 100, 1) if plan[i] != '-' else '-' for i in range(len(budget))]

    # Дни для первого столбца, Клиенты для заголовков
    days = list(df['day'].drop_duplicates().sort_values())
    clients = list(df['client_name'].drop_duplicates())

    data = {
        'pivot_data': pivot_data,
        'pivot_grand_totals': pivot_grand_totals,
        'budget': budget,
        'plan': plan,
        'percent_plan': percent_plan,
        'days': days,
        'clients': clients
    }
    return data


def prepare_calls_pivot_data_for_download(data):
    headers = ['Дата', 'Итого'] + data['clients']

    rows = []
    # Данные строк
    for day in data['days']:
        row_total = f"{data['pivot_data'][day]['row_total_yes']} ({data['pivot_data'][day]['row_total_all']})"
        cells = [f"{cell['target_total_yes']} ({cell['target_total_all']})" for cell in data['pivot_data'][day]['data']]
        rows.append((day, row_total, *cells))

    # Всего
    rows.append((
        'Всего',
        f"{data['pivot_grand_totals']['totals_yes_sum']} ({data['pivot_grand_totals']['totals_all_sum']})",
        *[f"{cell['column_totals_yes']} ({cell['column_totals_all']})" for cell in data['pivot_grand_totals']['combined_totals']]
    ))
    rows.append(('Бюджет', *data['budget']))
    rows.append(('План', *data['plan']))
    rows.append(('%', *data['percent_plan']))
    return headers, rows



def make_url_for_day_and_client(clients, datefrom, dateto):
    """
    Возвращает url на calls с фильтрами по дню и клиенту
    :param clients:
    :param datefrom:
    :param dateto:
    :return:
    """
    base_url = reverse('calls')
    datefrom = datetime.datetime.strftime(datefrom, '%d-%m-%Y')
    dateto = datetime.datetime.strftime(dateto, '%d-%m-%Y')
    params = {
        'datefrom': datefrom,
        'dateto': dateto,
        'clients': ','.join([str(c) for c in clients]),
    }
    full_url = f'{base_url}?{urlencode(params)}'
    return full_url
