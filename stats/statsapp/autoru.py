from stats.settings import env
import time
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

from .models import *
from django.db.models import Q

ENDPOINT = 'https://apiauto.ru/1.0'


# Список id клиентов на новом агентском аккаунте
clients_newcard = [48572, 50793, 50877, 51128, 50048, 47554, 53443, 39014, 25832, 26648]

API_KEY = {
    'x-authorization': env('AUTORU_API_KEY'),
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
API_KEY2 = {
    'x-authorization': env('AUTORU_API_KEY2'),
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}


def moscow_time(dt):
    """Добавляет 3 часа к дате-времени чтобы получить московское время"""
    try:
        no_tz = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        no_tz = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%SZ')
    moscow_tz = no_tz + timedelta(hours=3)
    return moscow_tz


def autoru_errors(data):
    try:
        error = data['error']
    except KeyError:
        return False
    else:
        if error == 'TOO_MANY_REQUESTS':
            print('Достигнут лимит авто.ру, жду минуту')
            time.sleep(60)
            return True
        elif error == 'NO_AUTH':
            print('Слетела авторизация, захожу повторно')
            global session_id, session_id2
            session_id = autoru_authenticate(env('AUTORU_LOGIN'), env('AUTORU_PASSWORD'))
            session_id2 = autoru_authenticate(env('AUTORU_LOGIN2'), env('AUTORU_PASSWORD2'))
            return True


def autoru_authenticate(login, password):
    # Аутентификация пользователя
    auth = '/auth/login'
    login_pass = {
        'login': login,
        'password': password
    }
    auth_response = requests.post(url=f'{ENDPOINT}{auth}', headers=API_KEY, json=login_pass)
    session_id = {'x-session-id': auth_response.json()['session']['id']}
    return session_id


def get_autoru_clients():
    # Активные клиенты авто.ру
    ids = Clients.objects \
        .values('autoru_id') \
        .filter(Q(active=True) & Q(autoru_id__isnull=False))
    active_clients_ids = [i['autoru_id'] for i in ids]
    return active_clients_ids


# ---------------------------------------------------------------------------
def get_autoru_products(from_, to, client_id):
    # Возвращает статистику по активации услуги у объявлений за указанную дату.
    # https://yandex.ru/dev/autoru/doc/reference/dealer-wallet-product-activations-offer-stats.html
    # GET /dealer/wallet/product/{productName}/activations/offer-stats

    if isinstance(from_, str) and isinstance(to, str):
        from_ = datetime.strptime(from_, '%Y-%m-%d')
        to = datetime.strptime(to, '%Y-%m-%d')

    # Удаляю текущие записи чтобы вместо них добавить записи с актуальными данными
    delete_autoru_products(from_, to, client_id)

    if client_id not in clients_newcard:
        dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}
    else:
        dealer_headers = {**API_KEY, **session_id2, 'x-dealer-id': f'{client_id}'}
    current_date = from_
    # За каждый день собираю статистику по всем видам услуг
    while current_date <= to:
        date_for_daily = current_date.strftime('%Y-%m-%d')
        product_types = get_autoru_daily(date_for_daily, date_for_daily, client_id)
        for product_type in product_types:
            start = time.perf_counter()
            product_params = {
                'service': 'autoru',
                'date': f'{current_date:%Y-%m-%d}',
                'pageNum': 1,
                'pageSize': 80
            }
            product_response = requests.get(
                url=f'{ENDPOINT}/dealer/wallet/product/{product_type}/activations/offer-stats',
                headers=dealer_headers, params=product_params).json()
            if autoru_errors(product_response):
                get_autoru_products(from_, to, client_id)
            # Добавляю
            try:
                if product_response['offer_product_activations_stats']:
                    add_autoru_products(product_response)

                page_count = product_response['paging']['page_count']
                if page_count > 1:
                    for page in range(2, page_count + 1):
                        product_params['pageNum'] = page
                        product_response = requests.get(
                            url=f'{ENDPOINT}/dealer/wallet/product/{product_type}/activations/offer-stats',
                            headers=dealer_headers, params=product_params).json()
                        add_autoru_products(product_response)
            except KeyError:
                continue
            finally:
                print(f'Клиент {client_id} | дата {current_date} | услуга {product_type:25} | {time.perf_counter() - start:.3f}')
        current_date += timedelta(days=1)


def add_autoru_products(data):
    # Добавляю услуги в базу
    autoru_products = []
    for offer in data['offer_product_activations_stats']:
        for stat in range(len(offer['stats'])):
            sum = offer['stats'][stat]['sum']
            count = offer['stats'][stat]['count']
            total = sum * count
            if total > 0:  # Добавляю только те услуги за которые списали средства
                ad_id = offer['offer']['id']
                try:
                    vin = offer['offer']['documents']['vin']
                except KeyError:
                    vin = 'null'
                client_id = int(offer['offer']['user_ref'].split(':')[1])
                date = offer['stats'][stat]['date']
                try:
                    mark = offer['offer']['car_info']['mark_info']['name']
                    model = offer['offer']['car_info']['model_info']['name']
                except KeyError:
                    mark = offer['offer']['truck_info']['mark_info']['name']
                    model = offer['offer']['truck_info']['model_info']['name']
                product = offer['stats'][stat]['product']
                # Проверяю есть ли уже эта запись
                record_exists_check = AutoruProducts.objects.filter(
                    ad_id=f'{ad_id}', date=f'{date}', product=f'{product}')
                if record_exists_check.count() == 0:
                    autoru_products.append(AutoruProducts(ad_id=ad_id, vin=vin, client_id=client_id, date=date,
                                                          mark=mark, model=model, product=product,
                                                          sum=sum, count=count, total=total))
    if len(autoru_products) > 0:
        AutoruProducts.objects.bulk_create(autoru_products)


def delete_autoru_products(from_, to, client_id):
    # Удаляю записи
    AutoruProducts.objects.filter(date__gte=from_, date__lte=to, client_id=client_id).delete()


# ---------------------------------------------------------------------------
def get_autoru_daily(from_, to, client_id):
    # Списание с кошелька за звонки и активацию услуг
    # https://yandex.ru/dev/autoru/doc/reference/dealer-wallet-product-activations-daily-stats.html
    # GET /dealer/wallet/product/activations/daily-stats
    wallet = '/dealer/wallet/product/activations/daily-stats'
    if client_id not in clients_newcard:
        dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}
    else:
        dealer_headers = {**API_KEY, **session_id2, 'x-dealer-id': f'{client_id}'}

    wallet_params = {
        'service': 'autoru',
        'from': from_,
        'to': to,
        'pageNum': 1,
        'pageSize': 1000
    }
    wallet_response = requests.get(url=f'{ENDPOINT}{wallet}', headers=dealer_headers, params=wallet_params).json()
    if autoru_errors(wallet_response):
        get_autoru_daily(from_, to, client_id)

    # Отдельной функцией добавляю в базу списания за размещения
    add_autoru_daily(wallet_response, client_id)

    # Возвращаю список примененных услуг за день (для get_autoru_products)
    try:
        product_types = [i['product'] for i in wallet_response['activation_stats']
                         if i['product'] != 'call' and i['sum'] > 0]
    except KeyError:
        product_types = []
    return product_types


def add_autoru_daily(data, client):
    # Добавляю списания за размещения в базу
    placements_filter = ['quota:placement:cars:used', 'quota:placement:cars:new', 'quota:placement:commercial',
                         'trade-in-request:cars:used', 'trade-in-request:cars:new']
    autoru_daily = []
    try:
        for day in data['activation_stats']:
            if day['product'] in placements_filter:
                ad_id = 'null'
                vin = 'null'
                client_id = client
                date = day['date']
                mark = 'null'
                model = 'null'
                product = day['product']
                sum = day['sum']
                count = day['count']
                total = sum * count

                record_exists_check = AutoruProducts.objects.filter(
                    client_id=f'{client_id}', date=f'{date}', product=f'{product}')
                if record_exists_check.count() == 0:
                    autoru_daily.append(AutoruProducts(ad_id=ad_id, vin=vin, client_id=client_id, date=date,
                                                       mark=mark, model=model, product=product,
                                                       sum=sum, count=count, total=total))
    except KeyError:
        print(f'Клиент {client} пропущен. {data}')
        return

    if len(autoru_daily) > 0:
        AutoruProducts.objects.bulk_create(autoru_daily)


# ---------------------------------------------------------------------------
def get_autoru_calls(from_, to, client_id):
    # Возвращает список звонков дилера.
    # https://yandex.ru/dev/autoru/doc/reference/calltracking.html
    # POST /calltracking

    from_ = datetime.strptime(f'{from_}T00:00:00.000Z', '%Y-%m-%dT00:00:00.000Z')
    to = datetime.strptime(f'{to}T23:59:59.000Z', '%Y-%m-%dT23:59:59.000Z')

    delete_autoru_calls(from_, to, client_id)

    calltracking = 'calltracking'
    if client_id not in clients_newcard:
        dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}
    else:
        dealer_headers = {**API_KEY, **session_id2, 'x-dealer-id': f'{client_id}'}

    calls_body = {
        "pagination": {
            "page": 1,
            "page_size": 100
        },
        "filter": {
            "period": {
                "from": from_.strftime("%Y-%m-%dT00:00:00.000Z"),
                "to": to.strftime("%Y-%m-%dT23:59:59.000Z")
            },
            "targets": 'ALL_TARGET_GROUP',
            # "results": 'ALL_RESULT_GROUP',
            # "callbacks": 'ALL_SOURCE_GROUP',
            # "unique": 'ALL_UNIQUE_GROUP',
            "category": [
                'CARS'
            ],
            "section": [
                'NEW', 'USED'
            ],
        },
        "sorting": {
            "sorting_field": 'CALL_TIME',
            "sorting_type": 'ASCENDING'
        }
    }
    calls_response = requests.post(url=f'{ENDPOINT}/{calltracking}', headers=dealer_headers, json=calls_body).json()
    if autoru_errors(calls_response):
        get_autoru_calls(from_, to, client_id)

    try:
        if calls_response['status'] == 'error':  # Пропускаю клиента если доступ запрещён
            print(f'Клиент {client_id} пропущен. Отказано в доступе')
            return
    except KeyError:
        if calls_response['pagination']['total_count'] > 0:
            add_autoru_calls(calls_response, client_id)
            # Если запрос возвращает больше одной страницы то иду по следующим
            page_count = calls_response['pagination']['total_page_count']
            if page_count > 1:
                for page in range(2, page_count + 1):
                    calls_body['pagination']['page'] = page
                    calls_response = requests.post(url=f'{ENDPOINT}/{calltracking}', headers=dealer_headers,
                                                   json=calls_body).json()
                    add_autoru_calls(calls_response, client_id)
    finally:
        print(f'Клиент {client_id} | звонки')


def add_autoru_calls(data, client):
    autoru_calls = []
    for call in data['calls']:
        try:
            ad_id = call['offer']['id']
        except KeyError:
            ad_id = 'null'
        try:
            vin = call['offer']['documents']['vin']
        except KeyError:
            vin = 'null'
        try:
            mark = call['offer']['car_info']['mark_info']['name']
        except KeyError:
            mark = 'Другое'
        try:
            model = call['offer']['car_info']['model_info']['name']
        except KeyError:
            model = 'Другое'
        try:
            duration = call['call_duration']['seconds']
        except KeyError:
            duration = 0
        try:
            billing_state = call['billing']['state']
        except KeyError:
            billing_state = 'FREE'
        client_id = client
        source = call['source']['raw']
        target = call['target']['raw']
        datetime = moscow_time(call['timestamp'])
        if billing_state == 'PAID':
            try:
                billing_cost = int(call['billing']['cost']['amount']) / 100
            except KeyError:
                billing_cost = 0
        elif billing_state == 'FREE':
            billing_cost = 0

        record_exists_check = AutoruCalls.objects.filter(
            source=f'{source}', target=f'{target}', datetime=f'{datetime}')
        if record_exists_check.count() == 0:
            autoru_calls.append(AutoruCalls(ad_id=ad_id, vin=vin, client_id=client_id, source=source, target=target,
                                            datetime=datetime, duration=duration, mark=mark, model=model,
                                            billing_state=billing_state, billing_cost=billing_cost))
    if len(autoru_calls) > 0:
        AutoruCalls.objects.bulk_create(autoru_calls)


def delete_autoru_calls(from_, to, client_id):
    AutoruCalls.objects.filter(datetime__gte=from_, datetime__lte=to, client_id=client_id).delete()


session_id = autoru_authenticate(env('AUTORU_LOGIN'), env('AUTORU_PASSWORD'))
session_id2 = autoru_authenticate(env('AUTORU_LOGIN2'), env('AUTORU_PASSWORD2'))


def update_autoru_catalog():
    """
    Обновляет каталог авто.ру
    """
    # Удаляю текущие
    AutoruCatalog.objects.all().delete()

    # Скачиваю актуальный
    url = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
    response = requests.get(url)
    xml_content = response.content

    root = ET.fromstring(xml_content)

    rows = []
    for mark in root.iter('mark'):
        mark_id = mark.get('id')
        mark_name = mark.get('name')
        mark_code = mark.find('code').text

        for folder in mark.iter('folder'):
            folder_id = folder.get('id')
            folder_name = folder.get('name')
            model_id = folder.find('model').get('id')
            model_name = folder_name.split(',')[0]
            model_code = folder.find('model').text
            generation_id = folder.find('generation').get('id')
            try:
                generation_name = folder_name.split(',')[1].strip()
            except IndexError:
                generation_name = 'take_years'

            for modification in folder.iter('modification'):
                modification_id = modification.get('id')
                modification_name = modification.get('name')
                configuration_id = modification.find('configuration_id').text
                tech_param_id = modification.find('tech_param_id').text
                body_type = modification.find('body_type').text
                years = modification.find('years').text

                if generation_name == 'take_years':
                    generation_name = years

                for complectation in modification.iter('complectation'):
                    complectation_id = complectation.get('id')
                    complectation_name = complectation.text

                    rows.append(AutoruCatalog(
                        mark_id=mark_id,
                        mark_name=mark_name,
                        mark_code=mark_code,
                        folder_id=folder_id,
                        folder_name=folder_name,
                        model_id=model_id,
                        model_name=model_name,
                        model_code=model_code,
                        generation_id=generation_id,
                        generation_name=generation_name,
                        modification_id=modification_id,
                        modification_name=modification_name,
                        configuration_id=configuration_id,
                        tech_param_id=tech_param_id,
                        body_type=body_type,
                        years=years,
                        complectation_id=complectation_id,
                        complectation_name=complectation_name,
                    ))

    AutoruCatalog.objects.bulk_create(rows)
    return
