import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Union, List, Dict
from urllib.parse import urljoin

import pandas as pd
import requests
from django.db.models import Q
from django.utils import timezone
from pandas import DataFrame

from libs.services.utils import datetime_ru_str_to_datetime, get_nested_value, add_keys_to_dict
from stats.settings import env
from .models import *
from ..services.utils import extract_digits


class AutoruLogic:
    endpoint = 'https://apiauto.ru/'
    api_version = '1.0'
    headers = {
        'x-authorization': env('AUTORU_API_KEY'),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    session_id = None

    def request_api(self, url: str, request_type: str, autoru_id: str = None,
                    params: Dict[str, any] = None, json: Dict[str, any] = None) -> requests.Response:
        """
        Общая функция для всех запросов
        :param url: часть ссылки которая добавляется к endpoint+api_version
        :param request_type: тип запроса: GET или POST
        :param autoru_id: id кабинета авто.ру
        :param params:
        :param json:
        :return: Response объект
        """
        full_url = urljoin(self.endpoint, f'{self.api_version}{url}')

        print(f'{str(autoru_id):6} | {request_type:4} | {url}')

        headers = {**self.headers, 'x-session-id': self.session_id}
        if autoru_id:
            headers['x-dealer-id'] = autoru_id

        if request_type == 'GET':
            response = requests.get(url=full_url, headers=headers, params=params, json=json)
        elif request_type == 'POST':
            response = requests.post(url=full_url, headers=headers, params=params, json=json)
        else:
            raise Exception('Неверный тип запроса, нужен GET либо POST')

        if self.error_handler(response.json()):
            return self.request_api(url, request_type, autoru_id, params, json)

        return response

    def request_api_list(self, data_key: str, url: str, request_type: str,
                         page_name: str, total_pages_name: str,
                         autoru_id: str = None, params: Dict[str, any] = None, json: Dict[str, any] = None,
                         ) -> Dict[str, List[Dict[str, any]]]:
        """
        Для запросов которые могут возвращать несколько страниц.
        Т.к. у авто.ру нет единого названия ключей для номеров страниц и общего количества страниц
        их нужно передавать сюда через page_name и total_pages_name.
        Если это имя ключа то просто его передавать, если путь по словарю то разделять точкой,
        например: 'pagination.page'
        Эта функция проходит по всем страницам, собирая все результаты в один словарь с одним списком в виде:
        result = {data_key: [response1, response2]}
        :param data_key: ключ по которому получать данные из ответа авто.ру
        :param url: часть ссылки которая добавляется к endpoint+api_version
        :param request_type: тип запроса: GET или POST
        :param page_name: имя или путь к ключу который содержит номер текущей страницы
        :param total_pages_name: путь к ключу который содержит общее количество страниц
        :param autoru_id: id кабинета авто.ру
        :param params:
        :param json:
        :return: словарь со списком ответов авто.ру со всех страниц
        """
        page_num = 1

        multi_page_data = {data_key: []}
        running = True
        while running:
            # Меняю номер текущей страницы
            if params:
                params[page_name] = page_num
            elif json:
                # json['pagination']['page'] = page_num
                json = add_keys_to_dict(json, page_name, page_num)

            # Отправляю запрос
            response = self.request_api(url, request_type,
                                        params=params if params else None,
                                        json=json if json else None,
                                        autoru_id=autoru_id).json()

            # Добавляю данные к общему списку
            if data_key in response:
                multi_page_data[data_key].extend(response[data_key])

            # Беру общее количество страниц
            # if params:
                # if 'page_count' not in response['paging']:
                #     page_count = page_num
                # else:
                    # page_count = response['paging']['page_count']

            # elif json:
                # if 'total_page_count' not in response['pagination']:
                #     page_count = page_num
                # else:
                #     page_count = response['pagination']['total_page_count']

            page_count = get_nested_value(response, total_pages_name, page_num)
            # Проверяю нужно ли идти на следующую страницу
            if page_num < page_count:
                page_num += 1
            else:
                running = False

        # Добавляю данные со всех страниц в последний ответ
        response[data_key] = multi_page_data[data_key]
        return response

    def authenticate(self, login: str = None, password: str = None) -> str:
        """
        Аутентификация пользователя.
        Если логин и пароль не переданы то авторизуется по данным из переменных среды.
        https://yandex.ru/dev/autoru/doc/reference/auth-login.html
        :param login:
        :param password:
        :return: session_id который нужен для всех запросов
        """
        url = '/auth/login'

        if not login and not password:
            login = env('AUTORU_LOGIN')
            password = env('AUTORU_PASSWORD')

        json = {
            'login': login,
            'password': password
        }
        response = self.request_api(url, 'POST', json=json)
        session_id = response.json()['session']['id']
        self.session_id = session_id
        return session_id

    def error_handler(self, data: Dict[str, any]) -> bool:
        """
        Обработчик ошибок.
        :param data: ответ авто.ру
        :return: True если были ошибки, они исправлены и нужно заново отправить запрос.
                 False если ошибок нет либо их не исправить в данный момент.
        """
        if 'error' not in data:
            return False

        error = data['error']

        if error == 'TOO_MANY_REQUESTS':
            logging.error('Достигнут лимит авто.ру, жду минуту')
            time.sleep(61)
        elif error == 'NO_AUTH':
            logging.error('Слетела авторизация, захожу повторно')
            self.authenticate()
        elif error == 'AGENT_ACCESS_FROBIDDEN':
            logging.error(f'Нет доступа: {data}')
            return False
        else:
            raise Exception(f'Необработанная ошибка: {data}')
        return True

    def get_daily_products(self, datefrom: Union[datetime, str], dateto: Union[datetime, str],
                           autoru_id: str) -> Dict[str, List[Dict[str, any]]]:
        """
        Списание с кошелька за звонки и активацию услуг.
        https://yandex.ru/dev/autoru/doc/reference/dealer-wallet-product-activations-daily-stats.html
        :param datefrom: дата от
        :param dateto: дата до
        :param autoru_id: id кабинета авто.ру
        :return: Возвращает даты, услуги, суммы. Только общие данные.
        """
        datefrom, dateto = datetime_ru_str_to_datetime(datefrom, dateto)

        url = '/dealer/wallet/product/activations/daily-stats'
        params = {
            'service': 'autoru',
            'from': datefrom.strftime('%Y-%m-%d'),
            'to': dateto.strftime('%Y-%m-%d'),
            'pageSize': 1000
        }
        data_key = 'activation_stats'
        return self.request_api_list(data_key=data_key, url=url, request_type='GET', params=params,
                                     autoru_id=autoru_id, page_name='pageNum', total_pages_name='paging.page_count')

    def get_and_add_products(self, datefrom: Union[datetime, str], dateto: Union[datetime, str],
                             autoru_id: str) -> None:
        """
        Сначала собирает все списания услуг за период, через get_daily_products,
        потом с полученных каждому дню и услуге собирает детальную информацию и добавляет в базу.
        https://yandex.ru/dev/autoru/doc/reference/dealer-wallet-product-activations-offer-stats.html
        :param datefrom: дата от
        :param dateto: дата до
        :param autoru_id: id кабинета авто.ру
        :return:
        """
        start_time = time.perf_counter()
        ignored_products = [
            'call',
            'call:cars:used',
            'quota:placement:moto',  # TODO Убрать когда авто.ру починят
        ]

        datefrom, dateto = datetime_ru_str_to_datetime(datefrom, dateto)

        self.delete_products(datefrom, dateto, autoru_id)

        daily_products = self.get_daily_products(datefrom, dateto, autoru_id)
        data_key = 'offer_product_activations_stats'
        result = {data_key: []}
        for row in daily_products['activation_stats']:
            if row['product'] in ignored_products or row['sum'] == 0:
                continue

            # TODO услуга quota:placement:moto не хочет работать в запросе
            url = f'/dealer/wallet/product/{row["product"]}/activations/offer-stats'
            params = {
                'service': 'autoru',
                'date': row['date'],
                # 'pageNum': 1,
                'pageSize': 80
            }
            response = self.request_api_list(data_key=data_key, url=url, request_type='GET',
                                             params=params, autoru_id=autoru_id, page_name='pageNum',
                                             total_pages_name='paging.page_count')
            result[data_key].extend(response[data_key])

        self.add_products(result)
        logging.info(f'get_and_add_products_detailed_stats время: {time.perf_counter() - start_time} сек.')

    def add_products(self, data: Dict[str, List[Dict[str, any]]]):
        """
        Добавляет данные по услугам в базу
        :param data: данные с услугами, передаются от get_and_add_products
        :return:
        """
        if 'offer_product_activations_stats' not in data:
            return

        new_records = []
        for offer in data['offer_product_activations_stats']:
            ad_id = offer['offer']['id']
            vin = get_nested_value(offer, 'offer.documents.vin')
            client_id = int(offer['offer']['user_ref'].split(':')[1])
            client = Client.objects.get(autoru_id=client_id)

            for stat in offer['stats']:
                if stat['sum'] == 0:
                    continue

                date = stat['date']
                if 'car_info' in offer['offer']:
                    mark = offer['offer']['car_info']['mark_info']['name']
                    model = offer['offer']['car_info']['model_info']['name']
                elif 'truck_info' in offer['offer']:
                    mark = offer['offer']['truck_info']['mark_info']['name']
                    model = offer['offer']['truck_info']['model_info']['name']
                else:
                    raise Exception('Неизвестный тип транспортного средства')
                product = stat['product']
                sum_ = stat['sum']
                count = stat['count']

                record_exists = AutoruProduct.objects.filter(ad_id=ad_id, date=date, product=product).exists()
                if not record_exists:
                    new_records.append(AutoruProduct(
                        ad_id=ad_id, vin=vin, client_id=client, date=date, mark=mark, model=model, product=product,
                        sum=sum_, count=count
                    ))

        if new_records:
            AutoruProduct.objects.bulk_create(new_records)

    def delete_products(self, datefrom: Union[datetime, str], dateto: Union[datetime, str], autoru_id: str):
        """
        Удаляет из базы данные по услугам за указанный период у нужного клиента
        :param datefrom: дата от
        :param dateto: дата до
        :param autoru_id: id кабинета авто.ру
        :return:
        """
        AutoruProduct.objects.filter(date__gte=datefrom, date__lte=dateto, client__autoru_id=autoru_id).delete()

    def get_and_add_calls(self, datefrom: Union[datetime, str], dateto: Union[datetime, str], autoru_id: str) -> None:
        """
        Возвращает список звонков дилера.
        https://yandex.ru/dev/autoru/doc/reference/calltracking.html
        :param datefrom: дата от
        :param dateto: дата до
        :param autoru_id: id кабинета авто.ру
        :return:
        """
        datefrom, dateto = datetime_ru_str_to_datetime(datefrom, dateto)

        # TODO возможно что не нужно удалять так как эти звонки будут связываться с нашим Call. Обновлять вместо удаления
        self.delete_calls(datefrom, dateto, autoru_id)

        url = '/calltracking'
        json = {
            "pagination": {
                # "page": 1,
                "page_size": 100
            },
            "filter": {
                "period": {
                    "from": datefrom.strftime("%Y-%m-%dT00:00:00.000Z"),
                    "to": dateto.strftime("%Y-%m-%dT23:59:59.000Z")
                },
                "targets": 'ALL_TARGET_GROUP',
                # "results": 'ALL_RESULT_GROUP',
                # "callbacks": 'ALL_SOURCE_GROUP',
                # "unique": 'ALL_UNIQUE_GROUP',
                "category": [
                    'CARS'
                ],
                "section": [
                    'NEW',
                    'USED'
                ],
            },
            "sorting": {
                "sorting_field": 'CALL_TIME',
                "sorting_type": 'DESCENDING'
            }
        }
        data_key = 'calls'

        response = self.request_api_list(data_key=data_key, url=url, request_type='POST', json=json,
                                         autoru_id=autoru_id, page_name='pagination.page',
                                         total_pages_name='pagination.total_page_count')
        self.add_calls(data=response, autoru_id=autoru_id)

    def add_calls(self, data: Dict[str, List[Dict[str, any]]], autoru_id: str) -> None:
        """
        Добавляет звонки в базу
        :param data: данные со звонками, передаются от get_and_add_calls
        :param autoru_id: id кабинета авто.ру
        :return:
        """

        def convert_datetime(dt_str: str) -> datetime:
            """
            Переводит строковую дату и время авто.ру в datetime объект и меняет tzinfo на utc
            :param dt_str: дата и время авто.ру в виде строки
            :return: datetime объект
            """
            try:
                dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')
            finally:
                return dt.replace(tzinfo=timezone.utc)

        client = Client.objects.get(autoru_id=autoru_id)
        new_calls = []
        for call in data['calls']:
            ad_id = get_nested_value(call, 'offer.id')
            vin = get_nested_value(call, 'offer.documents.vin')
            mark = get_nested_value(call, 'offer.car_info.mark_info.name', 'Другое')
            model = get_nested_value(call, 'offer.car_info.model_info.name', 'Другое')
            duration = get_nested_value(call, 'call_duration.seconds', 0)
            billing_state = get_nested_value(call, 'billing.state', 'FREE')
            num_from = extract_digits(call['source']['raw'])
            num_to = extract_digits(call['target']['raw'])
            datetime_ = convert_datetime(call['timestamp'])
            if billing_state == 'PAID':
                billing_cost = int(get_nested_value(call, 'billing.cost.amount', 0)) / 100
            elif billing_state == 'FREE':
                billing_cost = 0

            record_exists = AutoruCall.objects.filter(num_from=num_from, num_to=num_to, datetime=datetime_).exists()
            if not record_exists:
                new_calls.append(AutoruCall(ad_id=ad_id, vin=vin, client_id=client, num_from=num_from, num_to=num_to,
                                            datetime=datetime_, duration=duration, mark=mark, model=model,
                                            billing_state=billing_state, billing_cost=billing_cost))
        if new_calls:
            AutoruCall.objects.bulk_create(new_calls)

    def delete_calls(self, datefrom: Union[datetime, str], dateto: Union[datetime, str], autoru_id: str):
        """
        Удаляет из базы данные по звонкам за указанный период у нужного клиента
        :param datefrom: дата от
        :param dateto: дата до
        :param autoru_id: id кабинета авто.ру
        :return:
        """
        AutoruCall.objects.filter(datetime__gte=datefrom, datetime__lte=dateto, client__autoru_id=autoru_id).delete()

    def get_auction_history(self, client: Client) -> Union[None, dict]:
        """
        Собирает историю аукциона
        https://yandex.ru/dev/autoru/doc/reference/auction-current-state.html
        :param client: Client объект
        :return: Данные аукциона либо None
        """
        url = '/dealer/auction/current-state'
        response = self.request_api(url, 'GET', str(client.autoru_id)).json()
        if not response or 'states' not in response:
            return None

        for state in response['states']:
            if 'current_bid' in state:
                state['client'] = client
        return response

    # TODO продолжить с get_feeds_settings
    def get_feeds_settings(self, autoru_id: str) -> dict:
        """
        Возвращает список настроек для фидов
        https://yandex.ru/dev/autoru/doc/reference/feeds-settings.html
        :param autoru_id: id клиента на авто.ру
        :return: данные по настройкам фидов
        """
        url = '/feeds/settings'
        response = self.request_api(url, 'GET', autoru_id).json()
        return response

    def post_feeds_task(self, autoru_id: str, section: str, price_url: str,
                        delete_sale: bool = True, leave_services: bool = True,
                        leave_added_images: bool = False, is_active: bool = True) -> dict:
        """
        Создает задачу на ручную загрузку прайс-листа для категории ТС «Легковые ТС».
        https://yandex.ru/dev/autoru/doc/reference/feeds-task-cars-section.html
        :param autoru_id: id клиента на авто.ру
        :param section: NEW для новых, USED для б/у
        :param price_url: url с xml прайсом
        :param delete_sale: удалять размещённые вручную объявления
        :param leave_services: не удалять услуги объявлений
        :param leave_added_images: не удалять загруженные вручную фотографии и видео
        :param is_active: активна или нет загрузка данного прайса
        :return: результат загрузки
        """

        url = f'/feeds/task/cars/{section}'
        json = {
            "settings": {
                "source": price_url,
                "delete_sale": delete_sale,
                "leave_services": leave_services,
                "leave_added_images": leave_added_images,
                "is_active": is_active
            }
        }

        response = self.request_api(url, 'POST', autoru_id, json=json).json()
        return response

    def get_feeds_history(self, autoru_id: str) -> dict:
        """
        Возвращает историю загрузок прайс-листов.
        :param autoru_id: id клиента на авто.ру
        :return: история фидов
        """
        url = '/feeds/history'
        response = self.request_api(url, 'GET', autoru_id).json()
        return response

    def get_feed_task_results(self, autoru_id: str, feed_task_id: str, error_filters: List[str] = None) -> dict:
        """
        Возвращает детализацию по задаче на ручную загрузку прайс-листа.
        :param autoru_id: id клиента на авто.ру
        :param feed_task_id: id задачи от авто.ру по ручной загрузке фида
        :param error_filters: фильтры типов ошибок, можно несколько. Допустимые: 'NONE', 'ERROR', 'NOTICE'.
                              По умолчанию 'ERROR'
        :return: подробные данные по загрузке нужного фида
        """
        if not error_filters:
            error_filters = ['ERROR']

        url = f'/feeds/history/{feed_task_id}'
        params = {
            'page_size': 100,
            'error_type': error_filters
        }
        data_key = 'offers'
        response = self.request_api_list(data_key=data_key, url=url, request_type='GET', params=params,
                                         autoru_id=autoru_id, page_name='page',
                                         total_pages_name='pagination.total_page_count')
        return response

    # TODO продолжи с get_autoru_ads
    def get_autoru_ads(autoru_id: str) -> list[dict]:
        """
        Возвращает список объявлений пользователя.
        https://yandex.ru/dev/autoru/doc/reference/user-offers-category.html
        :param autoru_id: id клиента на авто.ру
        :return: список объявлений
        """
        url = '/user/offers/cars'
        json = {
            # 'page': 1,
            'page_size': 100,
        }
        data_key = 'offers'
        result = {data_key: []}




def get_autoru_clients() -> List[str]:
    """
    Возвращает autoru_id активных клиентов
    :return:
    """
    autoru_ids = (Client.objects
                  .filter(Q(active=True) & Q(autoru_id__isnull=False))
                  .values_list('autoru_id', flat=True))
    return [str(autoru_id) for autoru_id in autoru_ids]


def update_autoru_catalog() -> None:
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

    # Мои Марки и Модели
    my_marks = Mark.objects.all()
    my_models = Model.objects.all()
    # Добавляю к себе тех что нет
    new_marks = []
    for mark in root.iter('mark'):
        mark_name = mark.get('name')
        already_in_new_marks = any(obj.autoru == mark_name for obj in new_marks)
        if not my_marks.filter(autoru=mark_name).exists() and not already_in_new_marks:
            new_marks.append(Mark(name=mark_name, teleph=mark_name, autoru=mark_name, avito=mark_name,
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
                new_models.append(Model(mark=my_marks.filter(autoru=mark_name)[0], name=model_name, teleph=model_name,
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


def update_autoru_regions() -> None:
    """
    Обновляет регионы авто.ру
    """
    # Скачиваю актуальные
    # похоже что ссылка мёртвая, другого такого же подробного источника не нашёл
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
