import calendar
import datetime
import json
import time
from typing import Union, List

import numpy as np
import pandas as pd
import requests
from django.db import models
from django.db.models import Max, QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from applications.accounts.models import Client
from applications.calls.models import CallPriceSetting, TargetChoice, ChargeTypeChoice, Call, Plan, ClientPrimatel
from libs.services.forms import ClientChooseForm
from libs.services.models import Mark, Model
from libs.services.utils import split_daterange, get_all_fields_verbose_names, extract_digits


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
    form = ClientChooseForm(request.POST, user=request.user)
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
    # Если нецелевой то 0
    if 'target' not in validated_data or validated_data['target'] not in [TargetChoice.YES.value, TargetChoice.PM_YES.value]:
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
    else:
        return validated_data['call_price']


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
        *[f"{cell['column_totals_yes']} ({cell['column_totals_all']})" for cell in
          data['pivot_grand_totals']['combined_totals']]
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


def find_call_in_another_model(call: object, num_from: str, num_to: str, data: QuerySet) -> Union[object, None]:
    """
    Находит звонок из одной модели в другой модели. Подходит если нужно связать их между собой.
    Ищет по num_from, num_to и timestamp. Если по timestamp подходит несколько то дополнительно ищет по duration.
    Возвращает объект другой модели, если найден подходящий, иначе None.
    Например звонок из модели Call находит в CalltouchData и возвращает объект CalltouchData, если найден подходящий.
    :param call: объект звонка, который нужно найти в другой модели
    :param num_from:
    :param num_to:
    :param data: другая модель, в которой искать звонок call
    :return: объект другой модели, если найден, иначе None
    """

    def filter_qs(qs: Union[QuerySet, List], field: str,
                  original_value: Union[datetime.datetime.timestamp, int],
                  min_value: Union[datetime.datetime.timestamp, int],
                  max_value: Union[datetime.datetime.timestamp, int]) -> List:
        """
        Рекурсивная функция которая фильтрует данные звонков пока не найдет 1 или более звонков.
        Ищет через уменьшение min_value и увеличение max_value.
        :param qs: queryset
        :param field: поле по которому фильтровать qs: 'timestamp' или 'duration'
        :param original_value: начальное значение field
        :param min_value: минимальное значение для field
        :param max_value: максимальное значение для field
        :return: список с отфильтрованным qs
        """
        if (max_value - original_value) >= 50:  # Выхожу из рекурсии из если больше 50 вызовов
            return []
        filtered = [row for row in qs if min_value <= getattr(row, field) <= max_value]
        if len(filtered) >= 1:
            return filtered
        else:
            min_value -= 1
            max_value += 1
            return filter_qs(qs, field, original_value, min_value, max_value)

    # Чищу номера оставляя только цифры
    num_from = extract_digits(num_from)
    num_to = extract_digits(num_to)

    data_by_numbers = data.filter(num_from=num_from, num_to=num_to)

    timestamp_min = datetime.datetime.timestamp(call.datetime)
    timestamp_max = timestamp_min
    for row in data_by_numbers:
        # Чищу номера оставляя только цифры
        row.num_from = extract_digits(row.num_from)
        row.num_to = extract_digits(row.num_to)
        # Добавляю timestamp если нет
        if 'timestamp' not in row.__dict__:
            row.timestamp = datetime.datetime.timestamp(row.datetime)

    # Если есть звонки совпадающие по num_from и num_to то пробую найти нужный по timestamp
    if data_by_numbers:
        filtered_by_timestamp = filter_qs(data_by_numbers, 'timestamp',
                                          timestamp_max, timestamp_min, timestamp_max)
    else:  # Иначе звонка нет, возвращаю None
        return None

    # Если фильтрация по timestamp дала 1 результат значит звонок найден
    if len(filtered_by_timestamp) == 1:
        return filtered_by_timestamp[0]
    else:  # Иначе проверяю по duration
        filtered_by_duration = filter_qs(filtered_by_timestamp, 'duration',
                                         call.duration, call.duration, call.duration)
        # Если фильтрация по duration дала 1 результат значит звонок найден
        if len(filtered_by_duration) == 1:
            return filtered_by_duration[0]
        else:  # Иначе звонка нет, возвращаю None
            return None


def transfer_data_from_old_telephony(data_json_url: str, datefrom: datetime, dateto: datetime) -> None:
    """
    Переносит данные со старой телефонии в новую.
    В новой телефонии звонки уже должны быть получены от Примател - они и будут обновляться данными со старой телефонии.
    Чтобы получить данные со старой телефонии нужно со страницы с данными звонков открыть DevTools
    и во вкладке Network найти запрос graphql у которого в Payload ключ query начинается с getCallsDetails.
    Дальше со вкладки Response скопировать все данные, сохранить как json и загрузить на ftp - ссылку на этот файл
    передавать сюда как data_json_url
    :param data_json_url: ссылка на json с данными со старой телефонии
    :param datefrom: дата от
    :param dateto: дата до
    :return:
    """
    moderation_mapping = {
        'М': 'Авто.ру',
        'М(З)': 'Авто.ру',
        'М(Б)': 'Авто.ру (Б)',
        'БУ': 'Авто.ру БУ',
        'Авто.ру БУ': 'Авто.ру БУ',
        'Заявки': 'Заявка',
        'Дром': 'Дром',
        'Авито': 'Авито',
        'Авито БУ': 'Авито БУ',
        'Запас': 'Заявка',
        'Доп.ресурсы': 'Доп.ресурсы',
        None: ''
    }
    data = requests.get(data_json_url).json()

    df = pd.DataFrame.from_records(data['data']['getCallsDetails'])
    df = df.drop(columns='previousCalls')

    marks = Mark.objects.all().values('id', 'teleph')
    df_marks = pd.DataFrame.from_records(marks)
    merged_df = pd.merge(df, df_marks, left_on='mark', right_on='teleph', suffixes=('', '_mark'), how='left')

    models = Model.objects.all().values('id', 'teleph', 'mark__teleph')
    df_models = pd.DataFrame.from_records(models)
    merged_df['mark_model'] = merged_df['mark'] + merged_df['model']
    df_models['mark_model'] = df_models['mark__teleph'] + df_models['teleph']
    merged_df = pd.merge(merged_df, df_models, left_on='mark_model', right_on='mark_model', suffixes=('', '_model'), how='left')
    fill_na_cols = ['callPrice', 'id_mark', 'id_model', 'duration']
    merged_df[fill_na_cols] = merged_df[fill_na_cols].fillna(0)

    calls = Call.objects.filter(datetime__gte=datefrom, datetime__lte=dateto)
    updated_calls = []
    for call in calls:
        teleph_data = merged_df[merged_df['callId'] == call.primatel_call_id]
        if not teleph_data.empty:
            teleph_data = teleph_data.iloc[0]
        else:
            continue

        call.mark_id = teleph_data.id_mark if teleph_data.id_mark != 0 else None
        call.model_id = teleph_data.id_model if teleph_data.id_model != 0 else None
        call.target = teleph_data.objective
        call.moderation = moderation_mapping[teleph_data.moderation]
        call.call_price = teleph_data.callPrice
        call.status = teleph_data.callStatus
        call.car_price = teleph_data.price
        call.color = teleph_data.color
        call.body = teleph_data.body
        call.drive = teleph_data.driveUnit
        call.engine = teleph_data.engine
        call.complectation = teleph_data.equipment
        call.other_comments = teleph_data.comment

        updated_calls.append(call)

    Call.objects.bulk_update(updated_calls,
                             ['mark', 'model', 'target', 'moderation', 'call_price', 'status', 'car_price', 'color',
                              'body', 'drive', 'engine', 'complectation', 'other_comments'])

    # TODO создавать новые звонки которых нет в новой телефонии но есть в старой - это заявки добавленные вручную
    manual_calls = merged_df[merged_df['callId'].isna()]

    existing_calls = Call.objects.filter(datetime__gte=datefrom, datetime__lte=dateto).values('datetime', 'num_from')
    existing_calls_df = pd.DataFrame.from_records(existing_calls)

    clients_data = requests.get('http://ph.onllline.ru/temp/old_telephony_data/clients.json').json()
    clients_df = pd.DataFrame.from_records(clients_data['data']['getCabinetsWithClients'][0]['clients'])

    new_calls = []
    for index, row in manual_calls.iterrows():
        if row['numFrom'] == '79879789318':
            print('y')
        call_datetime = datetime.datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
        call_datetime = timezone.make_aware(call_datetime)
        # Пропускаю звонок если он уже есть в базе
        call_exists = not existing_calls_df[
            (existing_calls_df['datetime'] == call_datetime)
            & (existing_calls_df['num_from'] == row['numFrom'])
            ].empty
        if call_exists:
            continue

        login_id = row['loginId']
        primatel_login = clients_df[clients_df['id'] == login_id]['login'].iloc[0]
        try:
            client_primatel_obj = ClientPrimatel.objects.get(login=primatel_login)
        except ClientPrimatel.DoesNotExist:
            continue

        mark = row['id_mark'] if row['id_mark'] != 0 else None
        model = row['id_model'] if row['id_model'] != 0 else None

        new_call = Call(
            datetime=call_datetime,
            num_from=row['numFrom'],
            num_to=row['numTo'],
            duration=row['duration'],
            mark_id=mark,
            model_id=model,
            target=row['objective'],
            moderation=moderation_mapping[row['moderation']],
            call_price=row['callPrice'],
            status=row['callStatus'],
            repeat_call=False,
            other_comments=row['comment'],
            client_name=row['client'],
            manager_name=row['manager'],
            car_price=row['price'],
            color=row['color'],
            body=row['body'],
            drive=row['driveUnit'],
            engine=row['engine'],
            complectation=row['equipment'],
            attention=row['attention'] if row['attention'] else False,
            city=row['city'],
            client_primatel=client_primatel_obj,
            deleted=False,
        )
        new_calls.append(new_call)
    Call.objects.bulk_create(new_calls)
    # TODO проверить на повторные звонки

    return
