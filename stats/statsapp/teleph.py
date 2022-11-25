import os
import requests
from django.db.models import Q

from .models import *


TELEPH_ENDPOINT = 'https://151.248.121.33:9000/api/calls'
TELEPH_TOKEN = {
    'token': os.getenv('TELEPH_TOKEN')
}


def get_teleph_clients():
    ids = Clients.objects \
        .values('teleph_id') \
        .filter(Q(active=True) & Q(teleph_id__isnull=False))
    active_clients_ids = [i['teleph_id'] for i in ids]
    return active_clients_ids


def get_teleph_calls(from_, to, client_id):

    delete_teleph_calls(from_, to, client_id)

    params = {
        'login': client_id,
        'dateFrom': from_.strftime("%Y-%m-%d"),
        'dateTo': to.strftime("%Y-%m-%d"),
        'pageSize': 1000
    }
    teleph_response = requests.get(url=TELEPH_ENDPOINT, headers=TELEPH_TOKEN,
                                   params=params, verify=False).json()

    try:
        if teleph_response['totalElements']:
            add_teleph_calls(teleph_response, client_id)
            page_count = teleph_response['totalPages']
            if page_count > 1:
                for page in range(1, page_count - 1):
                    params['pageNumber'] = page
                    teleph_response = requests.get(url=TELEPH_ENDPOINT, headers=TELEPH_TOKEN,
                                                   params=params, verify=False).json()
                    add_teleph_calls(teleph_response, client_id)
    except KeyError:
        print(f'Клиент {client_id}, нет данных')


def add_teleph_calls(data, client_id):
    teleph_calls = []
    for call in data['content']:
        datetime = call['dateTime']
        num_from = call['numFrom']
        mark = call['mark']
        model = call['model']
        target = call['target']
        moderation = call['moderation']
        call_price = call['callPrice']
        price_autoru = call['priceAutoRu']
        price_drom = call['priceDrom']

        record_exists_check = TelephCalls.objects.filter(
            client_id=f'{client_id}', datetime=f'{datetime}', num_from=f'{num_from}')
        if record_exists_check.count() == 0:
            teleph_calls.append(TelephCalls(client_id=client_id, datetime=datetime, num_from=num_from,
                                            mark=mark, model=model, target=target, moderation=moderation,
                                            call_price=call_price, price_autoru=price_autoru, price_drom=price_drom))
    if len(teleph_calls) > 0:
        TelephCalls.objects.bulk_create(teleph_calls)


def delete_teleph_calls(from_, to, client_id):
    TelephCalls.objects.filter(datetime__gte=from_, datetime__lte=to, client_id=client_id).delete()
