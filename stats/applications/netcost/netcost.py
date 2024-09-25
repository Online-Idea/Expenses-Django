from datetime import datetime
from typing import List

import pandas as pd
from django.db.models import Sum, Q, Count, F
from django.utils import timezone

from applications.accounts.models import Client
from libs.autoru.models import AutoruCall, AutoruProduct
from libs.teleph.models import TelephCall


def calculate_teleph_calls_sum(row):
    if row['charge_type'] == Client.ChargeType.CALLS:
        return row['teleph_calls_sum']
    elif row['charge_type'] == Client.ChargeType.COMMISSION_PERCENT:
        return row['platform'] + (row['platform'] * row['commission_size'] / 100)
    elif row['charge_type'] == Client.ChargeType.COMMISSION_SUM:
        return row['platform'] + row['commission_size']
    else:
        return 0


def calculate_call_cost(row):
    if row['teleph_target'] > 0:
        return round(row['platform'] / row['teleph_target'], 2)
    else:
        return 0


def calculate_client_cost(row):
    if row['teleph_target'] > 0:
        return round(row['teleph_calls_sum'] / row['teleph_target'], 2)
    else:
        return 0


def calculate_margin(row):
    if row['charge_type'] == Client.ChargeType.CALLS:
        return round(row['client_cost'] - row['call_cost'], 2)
    elif row['charge_type'] == Client.ChargeType.COMMISSION_PERCENT:
        return row['platform'] * row['commission_size'] / 100
    elif row['charge_type'] == Client.ChargeType.COMMISSION_SUM:
        return row['commission_size']


def calculate_profit(row):
    if row['charge_type'] == Client.ChargeType.CALLS:
        return round(row['margin'] * row['teleph_target'], 2)
    elif row['charge_type'] == Client.ChargeType.COMMISSION_PERCENT:
        return row['platform'] * row['commission_size'] / 100
    elif row['charge_type'] == Client.ChargeType.COMMISSION_SUM:
        return row['commission_size']


def calculate_netcost(datefrom: datetime, dateto: datetime, clients: List[str]) -> (dict, dict):
    """
    Готовит данные для таблицы себестоимости
    :param datefrom: дата от
    :param dateto: дата до
    :param clients: список id клиентов
    :return: отдельно данные таблицы по каждому клиенту и отдельно итоги
    """
    datefrom = timezone.make_aware(datefrom)
    dateto = timezone.make_aware(dateto)

    # Собираю данные из базы в отдельные датафреймы
    clients_df = pd.DataFrame(Client.objects
                              .filter(id__in=clients)
                              .values('id', 'name', 'charge_type', 'commission_size', 'autoru_id', 'teleph_id'))
    autoru_calls_df = pd.DataFrame(AutoruCall.objects
                                   .values('client_id')
                                   .filter(datetime__gte=datefrom, datetime__lte=dateto)
                                   .annotate(calls_sum=Sum('billing_cost')))
    autoru_products_df = pd.DataFrame(AutoruProduct.objects
                                      .values('client_id')
                                      .filter(date__gte=datefrom, date__lte=dateto)
                                      .annotate(products_sum=Sum('sum')))
    teleph_calls_df = pd.DataFrame(TelephCall.objects
                                   .values('client_id')
                                   .filter((Q(datetime__gte=datefrom) & Q(datetime__lte=dateto))
                                           & (Q(target='Да') | Q(target='ПМ - Целевой'))
                                           & Q(moderation__startswith='М'))
                                   .annotate(teleph_calls_sum=Sum('call_price'), teleph_target=Count('target')))

    # Объединяю все датафреймы в один
    merged_df = pd.merge(clients_df, autoru_calls_df, left_on='autoru_id', right_on='client_id', how='left', suffixes=('', '_autoru_calls'))
    merged_df = pd.merge(merged_df, autoru_products_df, left_on='autoru_id', right_on='client_id', how='left', suffixes=('', '_autoru_products'))
    merged_df = pd.merge(merged_df, teleph_calls_df, left_on='id', right_on='client_id', how='left', suffixes=('', '_teleph_calls'))

    merged_df = merged_df.fillna(0)

    # Добавляю вычисляемые столбцы
    merged_df['platform'] = merged_df['calls_sum'] + merged_df['products_sum']  # Траты на площадку
    merged_df['teleph_calls_sum'] = merged_df.apply(calculate_teleph_calls_sum, axis=1)  # Приход с площадки
    merged_df['call_cost'] = merged_df.apply(calculate_call_cost, axis=1)  # Цена звонка
    merged_df['client_cost'] = merged_df.apply(calculate_client_cost, axis=1)  # Цена клиента
    merged_df['margin'] = merged_df.apply(calculate_margin, axis=1)  # Маржа
    merged_df['profit'] = merged_df.apply(calculate_profit, axis=1)  # Заработок

    # Убираю клиентов с пустыми данными
    merged_df = merged_df[~((merged_df['teleph_calls_sum'] == 0)
                          & (merged_df['platform'] == 0)
                          & (merged_df['teleph_target'] == 0))]

    # Итоги по столбцам
    totals = {
        'name': 'Всего',
        'calls_sum': merged_df['calls_sum'].sum(),
        'products_sum': merged_df['products_sum'].sum(),
        'teleph_calls_sum': merged_df['teleph_calls_sum'].sum(),
        'teleph_target': merged_df['teleph_target'].sum(),
        'platform': merged_df['platform'].sum(),
        # Убрал Цену звонка, Цену клиента и Маржу из итогов т.к. они не вычисляемы
        # из-за того что есть клиенты как по звонкам так и по комиссии
        # 'call_cost': round(merged_df['platform'].sum() / merged_df['teleph_target'].sum(), 2),
        # 'client_cost': round(merged_df['teleph_calls_sum'].sum() / merged_df['teleph_target'].sum(), 2),
        # 'margin': merged_df['margin'].sum(),
        'profit': merged_df['profit'].sum(),
    }

    df_dict = merged_df.to_dict('records')

    return df_dict, totals
