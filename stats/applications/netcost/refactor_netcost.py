from datetime import datetime

import pandas as pd
from django.db.models import Sum, Q, Count, F

from applications.accounts.models import Client
from libs.autoru.models import AutoruCall, AutoruProduct
from libs.teleph.models import TelephCall

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

datefrom = datetime(2024, 8, 1, 0, 0, 0)
dateto = datetime(2024, 8, 22, 0, 0, 0)


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


# Собираю данные из базы в отдельные датафреймы
clients_df = pd.DataFrame(Client.objects
                          .filter(active=True)
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

# Добавляю вычисляемые столбцы
merged_df['platform'] = merged_df['calls_sum'] + merged_df['products_sum']
merged_df['teleph_calls_sum'] = merged_df.apply(calculate_teleph_calls_sum, axis=1)
merged_df['call_cost'] = merged_df.apply(calculate_call_cost, axis=1)
merged_df['client_cost'] = merged_df.apply(calculate_client_cost, axis=1)
merged_df['margin'] = merged_df.apply(calculate_margin, axis=1)
merged_df['profit'] = merged_df.apply(calculate_profit, axis=1)

# TODO Итоги

print(merged_df[merged_df['id'] == 65])
