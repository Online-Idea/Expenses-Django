import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import List

import requests
from django.utils import timezone

from applications.autoconverter.converter import save_on_ftp
from applications.calls.models import CabinetPrimatel, ClientPrimatel, SipPrimatel, Call, ClientPrimatelMark
from libs.services.email_sender import send_email
from stats.settings import WEBSITE, env


# TODO добавить async
class PrimatelLogic:
    url = 'https://iapi.primatel.ru/'
    mode = 'json'
    login = ''
    password = ''
    session_id = None
    datetime_format = '%Y-%m-%d %H:%M:%S'
    request_count = 0
    request_limit = 1500
    list_users = []
    list_sips = []
    errors = ''
    # sip_login = '1014765_did'  # sip - это наш номер телефона в примателе, даёт request_list_sips
    # user_login = 'avilon_premium_vol_new'
    datetime_from = datetime(2024, 3, 27, 0, 0, 0)
    datetime_to = datetime(2024, 3, 28, 23, 59, 59)

    def request_api(self, svc, params=None):
        """
        Общий метод для отправки запросов
        :param svc:
        :param params:
        :return:
        """
        url = f'{self.url}?svc={svc}&mode={self.mode}'
        data = {
            'login': self.login,
            'password': self.password,
            'sid': self.session_id
        }
        body = data.copy()
        if params is not None:
            body.update(params)
        headers = {
            'Accept': 'application/json, application/xml, text/plain, text/html, *.*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        response = requests.post(url, headers=headers, data=body)
        return response

    def request_api_list(self, svc, params=None):
        page_num = 1
        result = []
        total_items_count = 0

        running = True
        while running:
            request_data = {
                'page_size': 100,
                'page_num': page_num,
            }
            if params:
                request_data.update(params)
            response = self.request_api(svc, request_data)
            if response:
                response = response.json()
                try:
                    data = response['data']['data']
                except TypeError:
                    logging.info(response)
                    return result
                names = response['data']['names']
                total = response['data']['total']
                total_items_count = int(total)

                if not data or not len(data):
                    return result

                for values in data:
                    item = {}
                    for index in range(len(values)):
                        if names[index] and values[index]:
                            item[names[index]] = values[index]
                    result.append(item)
            else:
                return result

            if len(result) < total_items_count:
                page_num += 1
            else:
                running = False

        return result

    def request_login(self, login, password):
        """
        Авторизация
        :return:
        """
        self.login = login
        self.password = password
        response = self.request_api('login').json()
        if response and 'data' in response and response['data'] and 'sid' in response['data']:
            self.session_id = response['data']['sid']
        else:
            self.session_id = None

    def request_list_users(self):
        """
        :return: список Клиентов Примател
        """
        return self.request_api_list('listUsers')

    def request_list_sips(self, login):
        """
        Возвращает sip для Клиента Примател. sip это наш телефон в Примателе
        :param login: логин Клиента Примател
        :return: список sip
        """
        return self.request_api_list('listSip', {'user_login': login})

    def download_call_records(self, calls):
        """
        Скачивает запись звонка
        :param calls: объекты Call
        :return:
        """
        for call in calls:
            if not self.session_id:
                cabinet = call.client_primatel.cabinet_primatel
                self.request_login(cabinet.login, cabinet.password)
            params = {
                'user_login': call.client_primatel.login,
                'call_id': call.primatel_call_id
            }
            record = self.request_api('downloadCallRecord', params)
            # record = BytesIO(record.content)

            if 'error_message' in str(record.content):
                continue

            save_path = f'{env("FTP")}/calls/{call.client_primatel.client.slug}/records/{call.primatel_call_id}.mp3'
            save_on_ftp(save_path, record.content)
            call.record = save_path

        Call.objects.bulk_update(calls, ['record'])

    def download_missing_call_records(self, cabinet, from_, to):
        """
        Собирает звонки у которых нет файлов записей и скачивает их
        :param cabinet:
        :param from_:
        :param to:
        :return:
        """
        calls_without_records = Call.objects.filter(
            client_primatel__cabinet_primatel=cabinet, datetime__gte=from_, datetime__lte=to,
            record__isnull=True, client_primatel__client__isnull=False, deleted=False
        )
        self.download_call_records(calls_without_records)

    def update_list_users(self, cabinet_primatel):
        """
        Собирает ClientPrimatel
        :param cabinet_primatel:
        :return:
        """
        if not self.session_id:
            self.request_login(self.login, self.password)
        list_users = self.request_list_users()
        self.list_users.extend([item['login'] for item in list_users])
        list_users = [{**item, 'cabinet_primatel': cabinet_primatel} for item in list_users]
        # instances = [ClientPrimatel(**{k: v for k, v in d.items()}) for d in list_users]
        client_primatel_logins = (ClientPrimatel.objects.filter(cabinet_primatel=cabinet_primatel)
                                  .values_list('login', flat=True))
        new_objs = [ClientPrimatel(login=item['login'], cabinet_primatel=item['cabinet_primatel'])
                    for item in list_users if item['login'] not in client_primatel_logins]
        created_objs = ClientPrimatel.objects.bulk_create(new_objs)
        if created_objs:
            send_email_request_to_fill_in_fields(created_objs)

    def update_list_sips(self, cabinet_primatel):
        """
        Собирает Sip
        :param cabinet_primatel:
        :return:
        """
        clients = ClientPrimatel.objects.filter(cabinet_primatel=cabinet_primatel, active=True)
        for client in clients:
            if not self.session_id:
                self.request_login(self.login, self.password)
            list_sips = self.request_list_sips(client.login)
            self.list_sips.extend([item['login'] for item in list_sips])
            # list_sips = [{**item, 'sip_login': item['login'], 'client_primatel': client.id} for item in list_sips]
            sip_primatel_sip_logins = SipPrimatel.objects.all().values_list('sip_login', flat=True)
            new_objs = [SipPrimatel(client_primatel=client, sip_login=item['login'])
                        for item in list_sips if item['login'] not in sip_primatel_sip_logins]
            SipPrimatel.objects.bulk_create(new_objs)

    def update_calls_details(self, cabinet_primatel, from_, to):
        """
        Собирает звонки
        :param cabinet_primatel:
        :param from_:
        :param to:
        :return:
        """
        clients = ClientPrimatel.objects.filter(cabinet_primatel=cabinet_primatel, active=True)
        sips = SipPrimatel.objects.filter(client_primatel__in=clients)
        existing_calls = Call.objects.filter(sip_primatel__in=sips, datetime__gte=from_, datetime__lte=to, deleted=False)
        existing_calls_primatel_call_ids = existing_calls.values_list('primatel_call_id', flat=True)

        step = 7
        new_calls = []
        updated_calls = []

        # while from_ < to:
        for sip in sips:
            client = clients.get(login=sip.client_primatel.login)
            params = {
                'sip_login': sip.sip_login,
                'min_duration': 0,
                'from': from_.strftime(self.datetime_format),
                # 'to': (from_ + timedelta(days=step)).strftime(self.datetime_format),
                'to': to.strftime(self.datetime_format),
                'show_destination': 1,
            }
            if not self.session_id:
                self.request_login(self.login, self.password)
            calls_details_list = self.request_api_list('getCallsDetails', params)
            if not calls_details_list:
                continue

            main_mark = check_main_mark(client)

            for item in calls_details_list:
                # Часовой пояс, чтобы Django не выдавал ошибку
                item['time'] = datetime.strptime(item['time'], '%Y-%m-%d %H:%M:%S')
                item['time'] = timezone.make_aware(item['time'], timezone.get_current_timezone())

                # TODO был баг когда дубли звонков добавились. Пока не нашёл из-за чего, возможно что-то отсюда
                if item['callid'] not in existing_calls_primatel_call_ids:
                    new_call = Call(
                        datetime=item['time'],
                        num_from=item['numfrom'],
                        num_to=item['numto'],
                        num_redirect=item['destination'],
                        duration=item['duration'],
                        primatel_call_id=item['callid'],
                        mark=main_mark,
                        client_primatel=sip.client_primatel,
                        sip_primatel=sip,
                        repeat_call=False,
                    )
                    if int(item['duration']) <= 25:
                        new_call.status = 'Сорвался'
                        new_call.target = 'Нет'

                    new_calls.append(new_call)
                else:
                    updated_call = existing_calls.get(primatel_call_id=item['callid'])
                    updated_call.datetime = item['time']
                    updated_call.num_from = item['numfrom']
                    updated_call.num_to = item['numto']
                    updated_call.num_redirect = item['destination']
                    updated_call.duration = item['duration']
                    updated_calls.append(updated_call)

            # from_ = from_ + timedelta(days=step)

        Call.objects.bulk_create(new_calls)
        Call.objects.bulk_update(updated_calls, fields=['datetime', 'num_from', 'num_to', 'num_redirect', 'duration'])
        # Повторно вызываю save() чтобы выполнить функции в нём, возможно что это нужно переделать
        save_again = Call.objects.filter(datetime__gte=from_, datetime__lte=to, deleted=False)
        for obj in save_again:
            obj.save()

    def update_data(self, datefrom=None, dateto=None):
        """
        Главная функция которая вызывает остальные
        :param datefrom:
        :param dateto:
        :return:
        """
        self.request_count = 0
        self.list_users = []
        self.list_sips = []
        self.errors = ''
        if not datefrom or not dateto:
            datefrom = datetime.now() - timedelta(days=1)
            dateto = datetime.now()
        datefrom = datefrom.replace(hour=0, minute=0, second=0)
        dateto = dateto.replace(hour=23, minute=59, second=59)
        datefrom = timezone.make_aware(datefrom)
        dateto = timezone.make_aware(dateto)
        cabinets = CabinetPrimatel.objects.filter(active=True)

        for cabinet in cabinets:
            self.request_login(cabinet.login, cabinet.password)
            self.update_list_users(cabinet)
            self.update_list_sips(cabinet)
            self.update_calls_details(cabinet, datefrom, dateto)
            self.download_missing_call_records(cabinet, datefrom, dateto)

        update_numbers()


def check_main_mark(client: ClientPrimatel):
    """
    Возвращает Mark если у клиента только одна Mark, иначе None.
    Используется для автоматического заполнения звонков.
    :param client:
    :return:
    """
    client_primatel_marks = ClientPrimatelMark.objects.filter(client_primatel=client)
    if len(client_primatel_marks) == 1:
        return client_primatel_marks[0].mark
    else:
        return None


def update_numbers():
    """
    Обновляет список номеров у Клиентов Приматела
    :return:
    """
    client_primatels = ClientPrimatel.objects.filter(active=True)
    calls = Call.objects.filter(client_primatel__in=client_primatels).values('client_primatel', 'num_to')
    for client in client_primatels:
        numbers = (calls.filter(client_primatel=client).values_list('num_to', flat=True)
                   .distinct().order_by('num_to'))
        client.numbers = ', '.join(numbers)

    ClientPrimatel.objects.bulk_update(client_primatels, fields=['numbers'])


def send_email_request_to_fill_in_fields(objs):
    """
    Отправляет письмо с просьбой заполнить новых клиентов
    :param objs: ClientPrimatel объекты
    :return:
    """
    links = [f'{WEBSITE}/admin/calls/clientprimatel/{i.id}/change/' for i in objs]
    subject = 'Нужно заполнить клиентов'
    body = 'Здравствуйте, нужно заполнить новых клиентов в базе:\n\n' + '\n'.join(links)
    recipients = 'evgen0nlin3@gmail.com'
    send_email(subject, body, recipients)


# logic = PrimatelLogic()
# logic.request_calls_details()
# calls_details = logic.request_calls_details()
# pprint(calls_details)
# api_list = logic.request_api_list('listUsers')
# pprint(api_list)
# list_sips = logic.request_list_sips(logic.user_login)
# pprint(list_sips)
