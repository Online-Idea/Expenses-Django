import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Union, List, Dict

import numpy as np
import pandas as pd
import requests
from django.db.models import Q, Count, QuerySet
from django.utils import timezone
from pandas import DataFrame
from rest_framework.utils.serializer_helpers import ReturnList

from applications.auction.models import AutoruAuctionHistory
from applications.srav.models import AutoruParsedAd, SravPivot
from stats.settings import env
from .models import *
from ..services.email_sender import send_email
from ..services.utils import extract_digits

ENDPOINT = 'https://apiauto.ru/1.0'

API_KEY = {
    'x-authorization': env('AUTORU_API_KEY'),
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
            global session_id
            session_id = autoru_authenticate(env('AUTORU_LOGIN'), env('AUTORU_PASSWORD'))
            return True


def autoru_authenticate(login, password):
    # Аутентификация пользователя
    # https://yandex.ru/dev/autoru/doc/reference/auth-login.html
    # POST /auth/login
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
    ids = Client.objects \
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

    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}
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
                print(
                    f'Клиент {client_id} | дата {current_date} | услуга {product_type:25} | {time.perf_counter() - start:.3f}')
        current_date += timedelta(days=1)


def add_autoru_products(data):
    # Добавляю услуги в базу
    autoru_products = []
    for offer in data['offer_product_activations_stats']:
        for stat in range(len(offer['stats'])):
            sum = offer['stats'][stat]['sum']
            count = offer['stats'][stat]['count']
            if sum > 0:  # Добавляю только те услуги за которые списали средства
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
                record_exists_check = AutoruProduct.objects.filter(
                    ad_id=f'{ad_id}', date=f'{date}', product=f'{product}')
                if record_exists_check.count() == 0:
                    autoru_products.append(AutoruProduct(ad_id=ad_id, vin=vin, client_id=client_id, date=date,
                                                         mark=mark, model=model, product=product,
                                                         sum=sum, count=count))
    if len(autoru_products) > 0:
        AutoruProduct.objects.bulk_create(autoru_products)


def delete_autoru_products(from_, to, client_id):
    # Удаляю записи
    AutoruProduct.objects.filter(date__gte=from_, date__lte=to, client_id=client_id).delete()


# ---------------------------------------------------------------------------
def get_autoru_daily(from_, to, client_id):
    # Списание с кошелька за звонки и активацию услуг
    # https://yandex.ru/dev/autoru/doc/reference/dealer-wallet-product-activations-daily-stats.html
    # GET /dealer/wallet/product/activations/daily-stats
    wallet = '/dealer/wallet/product/activations/daily-stats'
    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}

    wallet_params = {
        'service': 'autoru',
        'from': from_,
        'to': to,
        'pageNum': 1,
        'pageSize': 1000
    }
    wallet_response = requests.get(url=f'{ENDPOINT}{wallet}', headers=dealer_headers,
                                   params=wallet_params).json()
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

                record_exists_check = AutoruProduct.objects.filter(
                    client_id=f'{client_id}', date=f'{date}', product=f'{product}')
                if record_exists_check.count() == 0:
                    autoru_daily.append(AutoruProduct(ad_id=ad_id, vin=vin, client_id=client_id, date=date,
                                                      mark=mark, model=model, product=product,
                                                      sum=sum, count=count))
    except KeyError:
        print(f'Клиент {client} пропущен. {data}')
        return

    if len(autoru_daily) > 0:
        AutoruProduct.objects.bulk_create(autoru_daily)


# ---------------------------------------------------------------------------
def get_autoru_calls(from_, to, client_id):
    # Возвращает список звонков дилера.
    # https://yandex.ru/dev/autoru/doc/reference/calltracking.html
    # POST /calltracking

    # from_ = datetime.strptime(from_, '%Y-%m-%dT00:00:00.000Z')
    # to = datetime.strptime(to, '%Y-%m-%dT23:59:59.000Z')

    delete_autoru_calls(from_, to, client_id)

    calltracking = 'calltracking'
    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}

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

    if 'status' in calls_response and calls_response['status'].lower() == 'error':
        print(f'Клиент {client_id} пропущен: {calls_response}')
        return

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
        num_from = extract_digits(call['source']['raw'])
        num_to = extract_digits(call['target']['raw'])
        datetime = moscow_time(call['timestamp'])
        datetime = timezone.make_aware(datetime)
        if billing_state == 'PAID':
            try:
                billing_cost = int(call['billing']['cost']['amount']) / 100
            except KeyError:
                billing_cost = 0
        elif billing_state == 'FREE':
            billing_cost = 0

        record_exists_check = AutoruCall.objects.filter(
            num_from=f'{num_from}', num_to=f'{num_to}', datetime=f'{datetime}')
        if record_exists_check.count() == 0:
            autoru_calls.append(AutoruCall(ad_id=ad_id, vin=vin, client_id=client_id, num_from=num_from, num_to=num_to,
                                           datetime=datetime, duration=duration, mark=mark, model=model,
                                           billing_state=billing_state, billing_cost=billing_cost))
    if len(autoru_calls) > 0:
        AutoruCall.objects.bulk_create(autoru_calls)


def delete_autoru_calls(from_, to, client_id):
    AutoruCall.objects.filter(datetime__gte=from_, datetime__lte=to, client_id=client_id).delete()


# TODO вернуть чтобы работало API авто.ру
session_id = autoru_authenticate(env('AUTORU_LOGIN'), env('AUTORU_PASSWORD'))


def update_autoru_catalog():
    """
    Обновляет каталог авто.ру
    Этот вариант много ресурсов потребляет, но рабочий.
    Если update_autoru_catalog2 работает без проблем то удалить этот
    """
    # Удаляю текущие
    AutoruCatalog.objects.all().delete()

    # Скачиваю актуальный
    url = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
    response = requests.get(url)
    xml_content = response.content

    root = ET.fromstring(xml_content)

    # Мои Марки и Модели
    my_marks = Mark.objects.all()
    my_models = Model.objects.all()
    # Добавляю к себе тех что нет
    new_marks = []
    for mark in root.iter('mark'):
        mark_name = mark.get('name')
        already_in_new_marks = any(obj.autoru == mark_name for obj in new_marks)
        if not my_marks.filter(autoru=mark_name).exists() and not already_in_new_marks:
            new_marks.append(Mark(mark=mark_name, teleph=mark_name, autoru=mark_name, avito=mark_name,
                                  drom=mark_name, human_name=mark_name))
    Mark.objects.bulk_create(new_marks)
    my_marks = Mark.objects.all()

    new_models = []
    for mark in root.iter('mark'):
        mark_name = mark.get('name')
        for folder in mark.iter('folder'):
            folder_name = folder.get('name')
            model_name = folder_name.split(',')[0]
            already_in_new_models = any(obj.autoru == model_name and obj.mark.autoru == mark_name
                                        for obj in new_models)
            if not my_models.filter(mark__autoru=mark_name, autoru=model_name).exists() and not already_in_new_models:
                new_models.append(Model(mark=my_marks.filter(autoru=mark_name)[0], model=model_name, teleph=model_name,
                                        autoru=model_name, avito=model_name, drom=model_name, human_name=model_name))
    Model.objects.bulk_create(new_models)
    my_models = Model.objects.all()

    # Теперь работаю уже с каталогом авто.ру
    rows = []
    for mark in root.iter('mark'):
        mark_id = mark.get('id')
        mark_name = mark.get('name')
        mark_code = mark.find('code').text
        my_mark_id = my_marks.filter(autoru=mark_name)[0]

        for folder in mark.iter('folder'):
            folder_id = folder.get('id')
            folder_name = folder.get('name')
            model_id = folder.find('model').get('id')
            model_name = folder_name.split(',')[0]
            model_code = folder.find('model').text
            my_model_id = my_models.filter(mark__autoru=mark_name, autoru=model_name)[0]
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
                        my_mark_id=my_mark_id,
                        my_model_id=my_model_id,
                    ))

    AutoruCatalog.objects.bulk_create(rows)
    return


def update_autoru_catalog2():
    """
    Обновляет каталог авто.ру (без обработки марок и моделей).
    Этот вариант должен меньше ресурсов потреблять
    """
    # Удаляю текущие данные в каталоге
    AutoruCatalog.objects.all().delete()

    # Скачиваю актуальный с потоковым парсингом
    url = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Ensure the request was successful

    # Create an iterator to stream and parse the XML
    context = ET.iterparse(response.raw, events=("start", "end"))
    context = iter(context)
    event, root = next(context)  # Get the root element

    # Мои Марки и Модели
    my_marks = {mark.autoru: mark for mark in Mark.objects.all()}
    my_models = {(model.mark.autoru, model.autoru): model for model in Model.objects.all()}

    # Начинаем работать с AutoruCatalog
    rows = []
    for event, elem in context:
        if event == "end" and elem.tag == "mark":
            mark_id = elem.get('id')
            mark_name = elem.get('name')
            mark_code = elem.find('code').text
            my_mark_id = my_marks.get(mark_name)

            for folder in elem.iter('folder'):
                folder_id = folder.get('id')
                folder_name = folder.get('name')
                model_id = folder.find('model').get('id')
                model_name = folder_name.split(',')[0]
                model_code = folder.find('model').text
                my_model_id = my_models.get((mark_name, model_name))
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
                            my_mark_id=my_mark_id,
                            my_model_id=my_model_id,
                        ))

            root.clear()  # Clear memory for already processed elements

    # Вставляем данные в AutoruCatalog одним запросом
    if rows:
        AutoruCatalog.objects.bulk_create(rows)

    return


def update_marks_and_models():
    """
    Обновляет марки и модели из XML.
    """
    # Скачиваем актуальный файл
    url = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Ensure the request was successful

    # Create an iterator to stream and parse the XML
    context = ET.iterparse(response.raw, events=("start", "end"))
    context = iter(context)
    event, root = next(context)  # Get the root element

    # Мои Марки и Модели, кэшируем их в словари для быстрой проверки
    my_marks = {mark.autoru: mark for mark in Mark.objects.all()}
    my_models = {(model.mark.autoru, model.autoru): model for model in Model.objects.all()}

    # Массивы для добавления новых марок и моделей
    new_marks = []
    new_models = []

    # Обрабатываем все элементы <mark> потоком
    for event, elem in context:
        if event == "end" and elem.tag == "mark":
            mark_name = elem.get('name')

            # Если марки нет, добавляем её
            if mark_name not in my_marks:
                new_marks.append(Mark(
                    mark=mark_name, teleph=mark_name, autoru=mark_name, avito=mark_name,
                    drom=mark_name, human_name=mark_name))

            # Работаем с моделями
            for folder in elem.iter('folder'):
                folder_name = folder.get('name')
                model_name = folder_name.split(',')[0]

                if (mark_name, model_name) not in my_models:
                    new_models.append(Model(
                        mark=my_marks.get(mark_name), model=model_name, teleph=model_name,
                        autoru=model_name, avito=model_name, drom=model_name, human_name=model_name))

            root.clear()  # Clear memory for already processed elements

    # Добавляем новые марки и модели одним запросом
    if new_marks:
        Mark.objects.bulk_create(new_marks)
        # Обновляем кеш с новыми марками
        my_marks.update({mark.autoru: mark for mark in Mark.objects.all()})

    if new_models:
        Model.objects.bulk_create(new_models)
        # Обновляем кеш с новыми моделями
        my_models.update({(model.mark.autoru, model.autoru): model for model in Model.objects.all()})

    return


# Получение нужных данных для прайса из каталога авто.ру
# data = AutoruCatalog.objects \
#     .values('complectation_id') \
#     .annotate(year_from=Cast(Substr('years', 1, 4), output_field=IntegerField())) \
#     .filter(Q(mark_name='EXEED')
#             & Q(model_name='TXL')
#             & Q(generation_name='I Рестайлинг')
#             & Q(complectation_name='Flagship')
#             & Q(modification_name='1.6 AMT (186 л.с.) 4WD')
#             & Q(body_type='Внедорожник 5 дв.')
#             & Q(year_from__lte=2023)
#             )


def update_autoru_regions():
    """
    Обновляет регионы авто.ру
    """

    # Скачиваю актуальные
    regions = requests.get('https://cachev2-spb03.cdn.yandex.net/download.cdn.yandex.net/from/yandex.ru/tech/ru'
                           '/autoru/doc/files/rid.json?lid=193').json()
    if not regions:
        return

    # Удаляю текущие
    AutoruRegion.objects.all().delete()

    rows = []
    for region in regions:
        rows.append(AutoruRegion(
            autoru_region_id=region['id'],
            name=region['name'],
            path=region['path']
        ))

    AutoruRegion.objects.bulk_create(rows)
    return


def get_auction_history(client: Client) -> Union[None, dict]:
    """
    Собирает историю аукциона
    https://yandex.ru/dev/autoru/doc/reference/auction-current-state.html
    GET /dealer/auction/current-state
    :param client: клиент из базы
    """
    url = 'https://apiauto.ru/1.0/dealer/auction/current-state'
    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client.autoru_id}'}

    auction_response = requests.get(url=url, headers=dealer_headers).json()

    if autoru_errors(auction_response):
        get_auction_history(client)

    # TODO перепиши везде этот try на что-то получше
    try:
        if not auction_response or auction_response['status'] == 'error':  # Пропускаю клиента если доступ запрещён
            print(f'Клиент {client} пропущен. Нет объявлений либо отказано в доступе')
            return
    except KeyError:
        for state in auction_response['states']:
            if 'current_bid' in state:
                state['client'] = client
        return auction_response
    finally:
        print(f'Клиент {client} | история аукциона')


def prepare_auction_history(data: dict, datetime_: datetime) -> Union[DataFrame, None]:
    """
    Обработка данных аукциона
    :param data: список с ответами по аукциону от API авто.ру
    :param datetime_: дата и время
    :return: обработанный df
    """
    # Правки данных перед pandas
    data2 = {'states': []}
    for state in data['states']:
        if 'base_price' not in state:  # Если нет Базовой цены значит пропускаем
            continue

        if 'competitive_bids' not in state:  # Если нет конкурентов
            if 'current_bid' not in state:  # Если нет нашей ставки
                # Сохраняю просто Базовую цену
                state['competitive_bids'] = [{'bid': state['base_price'], 'competitors': 0}]
            else:
                # Сохраняю только нашу ставку
                state['competitive_bids'] = [{'bid': '000', 'competitors': 0}]

        data2['states'].append(state)
    data = data2

    if not data['states']:
        return

    # Данные в pandas
    df = pd.json_normalize(data['states'],
                           record_path=['competitive_bids'],
                           meta=[['context', 'region_id'],
                                 ['context', 'mark_name'],
                                 ['context', 'model_name'],
                                 ['current_bid'],
                                 ['client']],
                           errors='ignore')
    df[['bid', 'current_bid']] = df[['bid', 'current_bid']].apply(lambda x: x.str[:-2])
    df['current_bid'] = df['current_bid'].fillna(0)
    df[['bid', 'current_bid', 'competitors']] = df[['bid', 'current_bid', 'competitors']].astype(int)

    # Для ставок, по которым несколько дилеров размещаются, делаю копии по количеству этих дилеров
    dfs = []
    for _, row in df.iterrows():
        if row['competitors'] > 1:
            dfs.append(pd.concat([pd.DataFrame(row).T] * (row['competitors'] - 1)))

    dfs.append(df)
    new_df = pd.concat(dfs)

    # Наша ставка
    current_bids = df[df['current_bid'] > 0]
    current_bids = current_bids[
        ['context.region_id', 'context.mark_name', 'context.model_name', 'current_bid', 'client']].drop_duplicates()
    new_df = new_df.drop(columns='client')
    current_bids['competitors'] = 1
    current_bids['bid'] = current_bids['current_bid']
    new_df = pd.concat([new_df, current_bids])

    # Сортирую
    new_df = new_df.sort_values(['context.region_id', 'context.mark_name', 'context.model_name', 'bid'],
                                ascending=[True, True, True, False])

    # Регионы словами
    unique_regions_ids = new_df['context.region_id'].unique()
    autoru_regions = AutoruRegion.objects.filter(autoru_region_id__in=unique_regions_ids)
    unique_regions_names = {}
    for region_id in unique_regions_ids:
        unique_regions_names[region_id] = autoru_regions.filter(autoru_region_id=region_id)[0].name
    new_df['region_name'] = new_df['context.region_id'].replace(unique_regions_names)

    # Марки как объекты из базы
    unique_marks_names = new_df['context.mark_name'].unique()
    marks = Mark.objects.filter(mark__in=unique_marks_names)

    # Добавляю марки которых нет в базе
    if len(unique_marks_names) != len(marks):
        new_marks = []
        marks_str = [m.mark for m in marks]

        for mark in unique_marks_names:
            if mark not in marks_str:
                new_marks.append(Mark(mark=mark, teleph=mark, autoru=mark, avito=mark, drom=mark, human_name=mark))
        Mark.objects.bulk_create(new_marks)
        marks = Mark.objects.filter(mark__in=unique_marks_names)

    # Подставляю
    unique_marks_objs = {}
    for mark_name in unique_marks_names:
        unique_marks_objs[mark_name] = marks.filter(mark=mark_name)[0]
    new_df['mark_obj'] = new_df['context.mark_name'].replace(unique_marks_objs)

    # Модели как объекты из базы
    unique_marks_models_names = new_df[['context.mark_name', 'context.model_name']].drop_duplicates()
    models = Model.objects.filter(mark__mark__in=unique_marks_names)

    # Добавляю модели которых нет в базе
    new_models = []
    for _, row in unique_marks_models_names.iterrows():
        curr_mark = row['context.mark_name']
        curr_model = row['context.model_name']
        if not models.filter(mark__mark=curr_mark, model=curr_model):
            new_models.append(Model(mark=marks.filter(mark=curr_mark)[0], model=curr_model, teleph=curr_model,
                                    autoru=curr_model, avito=curr_model, drom=curr_model, human_name=curr_model))
    Model.objects.bulk_create(new_models)

    # Подставляю
    models = Model.objects.filter(mark__mark__in=unique_marks_names)
    models_objs = []
    for _, row in new_df.iterrows():
        models_objs.append(models.filter(
            mark__mark=row['context.mark_name'],
            model=row['context.model_name'])[0])

    new_df['model_obj'] = models_objs

    # Позиция
    new_df['position'] = new_df.groupby(['context.region_id', 'context.mark_name', 'context.model_name']).cumcount() + 1

    # Дата и время
    new_df['datetime'] = datetime_

    # Оставляю нужные столбцы
    new_df = new_df[['datetime', 'region_name', 'mark_obj', 'model_obj', 'position', 'bid', 'competitors', 'client']]

    # Удаляю лишние строки. Это когда мы одни участвуем в аукционе
    new_df = new_df[new_df['bid'] != 0]

    # Переименовываю
    new_df = new_df.rename(columns={
        'region_name': 'autoru_region',
        'mark_obj': 'mark',
        'model_obj': 'model',
    })
    return new_df


def auction_history_drop_unknown(all_bids: DataFrame) -> DataFrame:
    """
    Удаляю лишние строки с неизвестными дилерами которые на самом деле наши дилеры.
    :param all_bids: df со всеми ставками
    :return:
    """
    # Поля для сортировок
    all_bids['mark_value'] = all_bids['mark'].apply(lambda x: x.mark)
    all_bids['model_value'] = all_bids['model'].apply(lambda x: x.model)

    # Тут дропаю неизвестных дилеров, заменяя их нашими клиентами.
    # Всех наших клиентов сортирую в верх таблицы чтобы удалялись строки-дубли где клиентов нет
    def sort_client(x):
        return 1 if isinstance(x, type(np.nan)) else 0

    all_bids = all_bids.sort_values(by='client', key=lambda x: x.apply(sort_client))

    uniqueness = ['datetime', 'autoru_region', 'mark_value', 'model_value', 'position']
    all_bids = all_bids.reset_index(drop=True)
    all_bids = all_bids.drop_duplicates(subset=uniqueness + ['client'])

    client_df = all_bids[uniqueness + ['client']].copy()
    client_notnan = client_df[client_df['client'].notna()].copy()

    rows_to_drop = []
    for index, row in client_notnan[uniqueness].iterrows():
        rows_to_drop.append(client_df.loc[(client_df['datetime'] == row.iloc[0]) &
                                          (client_df['autoru_region'] == row.iloc[1]) &
                                          (client_df['mark_value'] == row.iloc[2]) &
                                          (client_df['model_value'] == row.iloc[3]) &
                                          (client_df['position'] == row.iloc[4]) &
                                          (client_df['client'].isna())])

    if rows_to_drop:
        rows_to_drop = pd.concat(rows_to_drop)
        all_bids = all_bids.drop(rows_to_drop.index, axis=0)

    # Здесь удаляю дубли в случае если мы не участвуем в аукционе
    all_bids = all_bids.drop_duplicates(subset=uniqueness)

    # Сортировка
    sorted_df = all_bids.sort_values(by=uniqueness)

    # Удаляю временные столбцы
    sorted_df = sorted_df.drop(['mark_value', 'model_value'], axis=1)
    sorted_df['client'] = sorted_df['client'].replace(np.nan, None)
    return sorted_df


def add_auction_history(data: DataFrame):
    """
    Добавляет историю аукциона в базу
    :param data: df с данными аукциона
    """
    objs = [AutoruAuctionHistory(
        datetime=timezone.make_aware(row['datetime']),
        autoru_region=row['autoru_region'],
        mark=row['mark'],
        model=row['model'],
        position=row['position'],
        bid=row['bid'],
        competitors=row['competitors'],
        client=row['client'],
        dealer=''
    ) for index, row in data.iterrows()]

    AutoruAuctionHistory.objects.bulk_create(objs)


# TODO перенеси в srav приложение
def process_parsed_ads(df: DataFrame, parser_datetime: datetime, region: str) -> List[Dict]:
    """
    Обрабатывает входящие данные от сравнительной
    :param df: данные сравнительной как pandas dataframe
    :param parser_datetime: дата и время когда парсер собрал данные
    :param region: регион
    :return: список со словарями, каждый словарь это одна строка
    """
    # Для всех одна дата и время
    df['datetime'] = parser_datetime
    # Для всех один регион
    df['region'] = region

    # Список столбцов которые позже удалю
    columns_to_drop = ["mark_model", "autoru_name", "complectation_id"]

    # По complectation_id я смотрю каталог авто.ру чтобы взять верные Марки и Модели
    df['complectation_id'] = df['link'].apply(lambda x: int(x.split('/')[9]))
    unique_complectation_ids = df['complectation_id'].unique().tolist()
    autoru_catalog = AutoruCatalog.objects.filter(complectation_id__in=unique_complectation_ids) \
        .values('complectation_id', 'my_mark_id', 'my_model_id')
    df_db = pd.DataFrame(autoru_catalog)
    df_merged = pd.merge(df, df_db, on='complectation_id', how='left')

    # По modification_id смотрю в том случае если по complectation_id не найдены Марка и Модель
    if df_merged['my_mark_id'].isnull().values.any():
        df_merged['modification_id'] = df_merged['link'].apply(lambda x: int(x.split('/')[8]))
        unique_modification_ids = df_merged['modification_id'].unique().tolist()
        # autoru_catalog2 = AutoruCatalog.objects.filter(modification_id__in=unique_modification_ids) \
        #     .values('modification_id', 'my_mark_id', 'my_model_id').distinct()
        autoru_catalog2 = AutoruCatalog.objects.filter(tech_param_id__in=unique_modification_ids) \
            .values('modification_id', 'my_mark_id', 'my_model_id').distinct()
        df_db2 = pd.DataFrame(autoru_catalog2)
        df_db2 = df_db2.add_suffix('2')
        df_merged = pd.merge(df_merged, df_db2, left_on='modification_id', right_on='modification_id2', how='left')
        df_merged['my_mark_id'] = df_merged['my_mark_id'].fillna(df_merged['my_mark_id2'])
        df_merged['my_model_id'] = df_merged['my_model_id'].fillna(df_merged['my_model_id2'])

        columns_to_drop.extend(['modification_id', 'modification_id2', 'my_mark_id2', 'my_model_id2'])

    # Если всё ещё есть пустые Марка и Модель то ищу по mark_model
    if df_merged['my_mark_id'].isnull().values.any():
        df_merged['my_mark_id'] = df_merged.apply(fill_nan_for_mark, axis=1)
        marks = Mark.objects.filter(id__in=df_merged['my_mark_id'].unique())

        def remove_mark(row):
            to_replace = marks.filter(id=row['my_mark_id'])[0].mark + ' '
            return row['mark_model'].replace(to_replace, '')

        df_merged['mark_model'] = df_merged.apply(remove_mark, axis=1)
        df_merged['my_model_id'] = df_merged.apply(fill_nan_for_model, axis=1)

    clients = Client.objects.all().values('id', 'autoru_name')
    df_db = pd.DataFrame(clients)
    df_merged = pd.merge(df_merged, df_db, left_on='dealer', right_on='autoru_name', how='left')

    df_merged = df_merged.drop(columns=columns_to_drop)
    df_merged = df_merged.rename(columns={'my_mark_id': 'mark', 'my_model_id': 'model', 'id': 'client'})

    df_merged['client'] = df_merged['client'].replace(np.nan, None)

    df_merged['with_nds'] = df_merged['with_nds'].replace({'да': True, 'нет': False})

    # Словарь вместо dataframe
    df_dict = df_merged.to_dict(orient='records')
    return df_dict


def fill_nan_for_mark(row):
    """
    Функция для pandas для того чтобы найти объект Mark по её названию
    :param row: строка pandas
    :return: id Mark
    """
    marks = Mark.objects.all()
    if pd.isna(row['my_mark_id']):
        possible_name = ' '.join(row['mark_model'].split()[:-1])
        found_obj = recursive_search(marks, 'mark', possible_name).id
        if found_obj:
            return found_obj
        else:
            raise ValueError(f'Марка {row["mark_model"]} не найдена в базе')
    else:
        return row['my_mark_id']


def fill_nan_for_model(row):
    """
    Функция для pandas для того чтобы найти объект Model по её названию
    :param row: строка pandas
    :return: id Model
    """
    models = Model.objects.filter(mark=row['my_mark_id'])
    if pd.isna(row['my_model_id']):
        possible_name = ' '.join(row['mark_model'].split())
        found_obj = recursive_search(models, 'model', possible_name)
        if found_obj:
            return found_obj.id
        else:
            send_email('Не найдена модель',
                       f'Проблема при обработке {possible_name}\nДобавь её вручную либо поправь код',
                       env['EMAIL_FOR_ERRORS'])
            raise ValueError(f'Модель {row["mark_model"]} не найдена в базе')
    else:
        return row['my_model_id']


def recursive_search(db_model: QuerySet, db_field: str, possible_name: str) -> Union[models.Model, None]:
    """
    Фильтрует Django модель по строке, отнимая по одному слову с конца
    :param db_model: QuerySet Django
    :param db_field: поле модели
    :param possible_name: строка по которой фильтрует
    :return: объект модели Django
    """
    qs = db_model.filter(**{db_field: possible_name})
    if qs:
        return qs[0]
    else:
        possible_name = ' '.join(possible_name.split()[:-1])
        if possible_name:
            return recursive_search(db_model, db_field, possible_name)
        else:
            return None


def fill_in_auction_with_parsed_ads(parsed_ads: list) -> None:
    """
    Заполняет пустых дилеров из аукциона по данным сравнительной
    :param parsed_ads: спарсенные объявления
    """
    parsed_datetime = parsed_ads[0].datetime
    start_of_day = parsed_datetime.replace(hour=0, minute=0)
    region = parsed_ads[0].region
    marks = list(set(d.mark for d in parsed_ads))
    models = list(set(d.model for d in parsed_ads))

    # Данные аукциона
    auction_data = AutoruAuctionHistory.objects \
        .filter(autoru_region__contains=region, mark__in=marks, model__in=models,
                datetime__lte=parsed_datetime, datetime__gte=start_of_day) \
        .order_by('-datetime')

    # Делаю повторный запрос к базе чтобы получить те же спарсенные объявления но как queryset а не list
    parsed_ads_qs = AutoruParsedAd.objects.filter(
        datetime=parsed_datetime, region=region, mark__in=marks, model__in=models) \
        .order_by('-datetime', 'model_id', 'position_total')

    unique_ads_df = pd.DataFrame.from_records(parsed_ads_qs.values('model', 'dealer', 'in_stock', 'services'))
    unique_ads_df = unique_ads_df.drop_duplicates().reset_index(drop=True)

    count_by_dealer = parsed_ads_qs.filter(in_stock__iexact='в наличии') \
        .order_by().values('dealer').annotate(count=Count('dealer'))

    rows_to_update = []
    for model in models:
        # unique_ads_model_df = unique_ads_df[unique_ads_df['model'] == model.id]
        # unique_ads = unique_ads_model_df.to_dict('records')

        auction_model_filtered = auction_data.filter(model=model)

        # Убираю уже известных дилеров (наших клиентов) из спарсенных дилеров
        exclude_clients = list(auction_model_filtered.values_list('client_id__autoru_name', flat=True))
        unique_ads_model_df = unique_ads_df[(unique_ads_df['model'] == model.id) &
                                            ~(unique_ads_df['dealer'].isin(exclude_clients))]

        unique_ads = unique_ads_model_df.to_dict('records')

        for row in auction_model_filtered:

            # Если есть данные в столбце нашего клиента то копирую его в столбец дилер
            if row.client:
                row.dealer = row.client.autoru_name
                rows_to_update.append(row)
                continue

            while not row.dealer and unique_ads:
                # Если в наличии
                if unique_ads[0]['in_stock'].lower() == 'в наличии':
                    # Если среди услуг есть премиум или поднятие
                    if 'премиум' in unique_ads[0]['services'] or 'поднятие в поиске' in unique_ads[0]['services']:
                        dealer_count = count_by_dealer.filter(dealer=unique_ads[0]['dealer'])[0]['count']
                        # Если количество объявлений этого дилера 1
                        if dealer_count == 1:
                            # Берём
                            row.dealer = unique_ads[0]['dealer']
                        else:
                            # Иначе смотрим на следующего дилера
                            unique_ads = unique_ads[1:]
                    else:
                        # Услуг нет, берём
                        row.dealer = unique_ads[0]['dealer']
                else:
                    # Иначе смотрим на следующего дилера
                    unique_ads = unique_ads[1:]

            rows_to_update.append(row)
            unique_ads = unique_ads[1:]

    # Обновляю данные в базе
    AutoruAuctionHistory.objects.bulk_update(rows_to_update, ['dealer'])


# SQL запрос чтобы показать каких моделей нам не хватает для заполнения аукциона
"""
SELECT
  DISTINCT ma.mark, mo.model
FROM
  srav_autoru_parsed_ad AS ads
INNER JOIN services_mark AS ma ON ads.mark_id = ma.id
INNER JOIN services_model AS mo ON ads.model_id = mo.id
WHERE
  datetime > '2023-11-17 00:00'
  AND datetime < '2023-11-17 23:59'
  AND (ma.mark, mo.model) NOT IN (
    SELECT
      DISTINCT ma2.mark, mo2.model
    FROM
      auction_autoru_auction_history AS au
    INNER JOIN services_mark AS ma2 ON au.mark_id = ma2.id
    INNER JOIN services_model AS mo2 ON au.model_id = mo2.id
    LEFT JOIN services_client AS cl ON au.client_id = cl.id
    WHERE
      au.datetime > '2023-10-31 00:00'
      AND au.datetime < '2023-10-31 23:59'
      AND au.dealer > ''
  )
ORDER BY
  ma.mark,
  mo.model
;  
"""


def fill_in_unique_cheapest_for_srav_pivot(qs: Union[QuerySet[AutoruParsedAd], ReturnList]) -> QuerySet[SravPivot]:
    """
    Со спарсенных объявлений берёт самые дешёвые и уникальные и заносит в базу
    :param qs: спарсенные объявления, передавать все объявления с одного запуска парсера
    :return: самые дешевые и уникальные как записи из SravPivot
    """
    if type(qs) == QuerySet[AutoruParsedAd]:
        df = pd.DataFrame.from_records(qs.values())
        common_cols = ['mark_id', 'model_id']
    elif type(qs) == ReturnList:
        df = pd.DataFrame.from_records(qs)
        common_cols = ['mark', 'model']
    else:
        raise ValueError('Неверные данные, должны быть QuerySet[AutoruParsedAd] либо ReturnList')

    common_cols.extend(['complectation', 'modification', 'year'])

    # Сортирую
    df = df.sort_values(by=common_cols + ['price_with_discount'])

    # Количество автомобилей
    df_in_stock = df[df['in_stock'] == 'В наличии']
    count_df = df_in_stock.groupby(common_cols + ['dealer']) \
        .size().reset_index(name='stock')
    df = pd.merge(df, count_df, on=common_cols + ['dealer'], how='left')

    df_for_order = df[df['in_stock'].isin(['В пути', 'На заказ'])]
    count_df = df_for_order.groupby(common_cols + ['dealer']) \
        .size().reset_index(name='for_order')
    df = pd.merge(df, count_df, on=common_cols + ['dealer'], how='left')

    # Пустые на 0
    df[['stock', 'for_order']] = df[['stock', 'for_order']].fillna(0)

    # Удаляю дубликаты
    df = df.drop_duplicates(subset=common_cols + ['dealer'])

    # Позиция по цене
    df['position_price'] = df.groupby(common_cols).cumcount() + 1

    # В базу
    df_records = df.to_dict('records')

    # id AutoruParsedAd
    ids = [record['id'] for record in df_records]
    ads = AutoruParsedAd.objects.filter(id__in=ids)
    ad_dict = {ad.id: ad for ad in ads}

    # Новые SravPivot
    model_instances = [SravPivot(
        autoru_parsed_ad=ad_dict[record['id']],
        position_price=record['position_price'],
        in_stock_count=record['stock'],
        for_order_count=record['for_order']
    ) for record in df_records]

    objs = SravPivot.objects.bulk_create(model_instances)

    return objs


def get_feeds_settings(client_id: int) -> json:
    """
    # Возвращает список настроек для прайс-листов.
    # https://yandex.ru/dev/autoru/doc/reference/feeds-settings.html
    # GET /feeds/settings
    :param client_id: id клиента на авто.ру
    :return: json с ответом
    """

    req_url = 'feeds/settings'

    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}

    feeds_response = requests.get(url=f'{ENDPOINT}/{req_url}', headers=dealer_headers)
    return feeds_response.json()


def post_feeds_task(client_id: int, section: str, price_url: str,
                    delete_sale: bool = True, leave_services: bool = True,
                    leave_added_images: bool = False, is_active: bool = True) -> json:
    """
    # Создает задачу на ручную загрузку прайс-листа для категории ТС «Легковые ТС».
    # https://yandex.ru/dev/autoru/doc/reference/feeds-task-cars-section.html
    # POST /feeds/task/cars/{section}
    :param client_id: id клиента на авто.ру
    :param section: NEW для новых, USED для б/у
    :param price_url: url с xml прайсом
    :param delete_sale: удалять размещённые вручную объявления
    :param leave_services: не удалять услуги объявлений
    :param leave_added_images: не удалять загруженные вручную фотографии и видео
    :param is_active: активна или нет загрузка данного прайса
    :return: json с ответом
    """

    req_url = f'feeds/task/cars/{section}'

    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}

    req_body = {
        # "internal_url": price_url,
        "settings": {
            "source": price_url,
            "delete_sale": delete_sale,
            "leave_services": leave_services,
            "leave_added_images": leave_added_images,
            "is_active": is_active
        }
    }

    feeds_task_response = requests.post(url=f'{ENDPOINT}/{req_url}', headers=dealer_headers, json=req_body)
    return feeds_task_response


def get_autoru_ads(client_id: int) -> list[dict]:
    """
    Возвращает список объявлений пользователя.
    https://yandex.ru/dev/autoru/doc/reference/user-offers-category.html
    GET /user/offers/{category}
    :param client_id: id клиента на авто.ру
    :return: список объявлений
    """
    url = f'{ENDPOINT}/user/offers/cars'
    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}
    req_body = {
        'page': 1,
        'page_size': 100,
    }
    ads_response = requests.get(url=url, headers=dealer_headers, params=req_body).json()

    if autoru_errors(ads_response):
        get_autoru_ads(client_id)

    ads = []
    if ads_response['pagination']['total_offers_count'] > 0:
        ads.extend(ads_response['offers'])
        page_count = ads_response['pagination']['total_page_count']
        if page_count > 1:
            for page in range(2, page_count + 1):
                req_body['page'] = page
                ads_response = requests.get(url=url, headers=dealer_headers, params=req_body).json()
                ads.extend(ads_response['offers'])

    return ads


def activate_autoru_ads(ads_ids: Union[List[str], List[Dict[str, str]]], client_id: int) -> None:
    """
    Активирует объявления, снятые с продажи
    https://yandex.ru/dev/autoru/doc/reference/user-offers-category-offer-id-activate.html
    POST /user/offers/{category}/{offerID}/activate
    :param ads_ids: список авто.ру-идентификаторов объявлений
    :param client_id: id клиента на авто.ру
    :return:
    """
    url = f'{ENDPOINT}/user/offers/cars/offerID/activate'
    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}

    ads_ids = take_out_ids(ads_ids)

    for ad_id in ads_ids:
        url_with_id = url.replace('offerID', ad_id)
        response = requests.post(url=url_with_id, headers=dealer_headers)
        if autoru_errors(response.json()):
            response = requests.post(url=url_with_id, headers=dealer_headers)


def take_out_ids(ads: Union[List[str], List[Dict[str, str]]]) -> list:
    # Если передают полные данные объявлений с get_autoru_ads то вытаскиваю из них id
    if 'id' in ads[0]:
        return [ad['id'] for ad in ads]
    return ads


def stop_autoru_ads(ads_ids: Union[List[str], List[Dict[str, str]]], client_id: int) -> None:
    """
    Снимает объявления с продажи.
    https://yandex.ru/dev/autoru/doc/reference/user-offers-category-offer-id-hide.html
    PUT /user/offers/{category}/{offerID}/hide
    :param ads_ids: список авто.ру-идентификаторов объявлений
    :param client_id: id клиента на авто.ру
    :return:
    """
    url = f'{ENDPOINT}/user/offers/cars/offerID/hide'
    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}

    ads_ids = take_out_ids(ads_ids)

    for ad_id in ads_ids:
        url_with_id = url.replace('offerID', ad_id)
        response = requests.put(url=url_with_id, headers=dealer_headers)
        if autoru_errors(response.json()):
            response = requests.put(url=url_with_id, headers=dealer_headers)


def delete_autoru_ads(ads_ids: Union[List[str], List[Dict[str, str]]], client_id: int) -> None:
    """
    Удаляет объявления
    https://yandex.ru/dev/autoru/doc/reference/user-offers-category-offer-id.html
    DELETE /user/offers/{category}/{offerID}
    :param ads_ids:
    :param client_id:
    :return:
    """
    url = f'{ENDPOINT}/user/offers/cars/offerID'
    dealer_headers = {**API_KEY, **session_id, 'x-dealer-id': f'{client_id}'}

    ads_ids = take_out_ids(ads_ids)

    for ad_id in ads_ids:
        url_with_id = url.replace('offerID', ad_id)
        response = requests.delete(url=url_with_id, headers=dealer_headers)
        if autoru_errors(response.json()):
            response = requests.delete(url=url_with_id, headers=dealer_headers)


def get_autoru_catalog_structure():
    url = 'https://apiauto.ru/1.0/search/cars/breadcrumbs'
    dealer_headers = {**API_KEY, **session_id}
    catalog = AutoruCatalog.objects.all()[:500]
    bc_lookups = [f'{row.mark_code}#{row.model_code}' for row in catalog]
    params = {
        # 'bc_lookup': 'HIPHI#Y#23668078#23668106',
        # 'bc_lookup': 'HIPHI#Y',
        'bc_lookup': bc_lookups,
        'rid': 213,
        'state': 'NEW'
    }
    response = requests.get(url=url, headers=dealer_headers, params=params)
    return response.json()
