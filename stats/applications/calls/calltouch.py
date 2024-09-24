import os
from datetime import datetime
from typing import List

import requests
from django.db.models import QuerySet, Min, Max, Q
from django.urls import reverse
from django.utils import timezone
from requests.exceptions import JSONDecodeError

from applications.calls.calls import find_call_in_another_model
from applications.calls.models import Call, CalltouchSetting, CalltouchData, TargetChoice, ModerationChoice
from libs.services.email_sender import send_email
from stats.settings import env


class CalltouchLogic:
    endpoint = 'https://api.calltouch.ru/'
    date_format = '%d/%m/%Y'
    site_id = None
    token = None

    def request_api(self, url, request_type, params=None, data=None, json=None):
        if params:
            params['clientApiId'] = self.token

        if request_type == 'GET':
            response = requests.get(url, params=params, data=data, json=json)
        elif request_type == 'POST':
            response = requests.post(url, params=params, data=data, json=json)
        else:
            raise Exception('Неверный тип запроса, нужен GET либо POST')
        return response

    def request_api_list(self, url, request_type, params=None, data=None, json=None):
        page_num = 1
        result = []

        running = True
        while running:
            request_params = {
                'page': page_num,
                'limit': 1000,
            }
            if params:
                request_params.update(params)
            response = self.request_api(url, request_type, request_params, data, json)
            if response:
                try:
                    response = response.json()
                except JSONDecodeError:
                    breakpoint()
                records = response['records']
                total_records = response['recordsTotal']

                if not records:
                    return result

                result.extend(records)
            else:
                return result

            if len(result) < total_records:
                page_num += 1
            else:
                running = False

        return result

    def get_calls_details(self, site_id, token, datefrom, dateto):
        """
        Данные по звонкам
        :param site_id:
        :param token:
        :param datefrom: datetime объект
        :param dateto: datetime объект
        :return:
        """
        # https://www.calltouch.ru/support/api-metod-vygruzki-zhurnala-zvonkov/
        url = f'{self.endpoint}/calls-service/RestAPI/{site_id}/calls-diary/calls'

        self.site_id = site_id
        self.token = token
        datefrom = datefrom.strftime(self.date_format)
        dateto = dateto.strftime(self.date_format)
        params = {
            'dateFrom': datefrom,
            'dateTo': dateto,
            'withCallTags': True,
            # 'phoneNumber.value': our_phone,
        }
        result = self.request_api_list(url, 'GET', params=params)
        return result

    def get_calltouch_data(self, datefrom, dateto):
        """
        Собирает данные звонков по настройкам CalltouchSetting, сохраняет в CalltouchData
        :param datefrom: datetime объект
        :param dateto: datetime объект
        :return:
        """
        calltouch_settings = CalltouchSetting.objects.filter(active=True)
        calltouch_data = []
        for calltouch_setting in calltouch_settings:
            calltouch_data.extend(self.get_calls_details(calltouch_setting.site_id, calltouch_setting.token, datefrom,
                                                         dateto))
        for row in calltouch_data:
            row['callId'] = str(row['callId'])

        existing_calls = CalltouchData.objects.filter(datetime__gte=datefrom, datetime__lte=dateto)
        existing_calls_ids = existing_calls.values_list('calltouch_call_id', flat=True)

        new_calls = [CalltouchData(
            calltouch_call_id=row['callId'],
            timestamp=row['timestamp'],
            datetime=timezone.make_aware(datetime.strptime(row['date'], '%d/%m/%Y %H:%M:%S')),
            num_from=row['callerNumber'],
            num_to=row['phoneNumber'],
            duration=row['duration'],
            site_id=row['siteId'],
            call_tags=row['callTags'],
            site_name=row['siteName'],
            source=row['source'],
            successful=row['successful'],
            target=row['targetCall'],
            unique=row['uniqueCall'],
            unique_target=row['uniqTargetCall'],
        ) for row in calltouch_data if row['callId'] not in existing_calls_ids]

        updated_calls = []
        for row in calltouch_data:
            if row['callId'] not in existing_calls_ids:
                continue
            call = existing_calls.get(calltouch_call_id=row['callId'])
            call.call_tags = row['callTags']
            updated_calls.append(call)

        CalltouchData.objects.bulk_create(new_calls)
        CalltouchData.objects.bulk_update(updated_calls, ['call_tags'])

    def update_calls_with_calltouch_data(self, queryset: QuerySet[Call]):
        """
        Привязывает CalltouchData к нашим Call
        :return: обновлённые Call с заполненными calltouch_data
        """

        # Убираю из queryset звонки для которых нет CalltouchSetting
        calltouch_settings = CalltouchSetting.objects.filter(active=True).values_list('client_primatel_id', flat=True)
        queryset = queryset.filter(Q(client_primatel_id__in=calltouch_settings))

        # Данные по которым отфильтрую CalltouchData
        min_datetime = queryset.aggregate(Min('datetime'))['datetime__min']
        max_datetime = queryset.aggregate(Max('datetime'))['datetime__max']
        min_datetime = min_datetime.replace(hour=0, minute=0, second=0)
        max_datetime = max_datetime.replace(hour=23, minute=59, second=59)

        # Фильтрую CalltouchData
        calltouch_data = CalltouchData.objects.filter(datetime__gte=min_datetime, datetime__lte=max_datetime)
        if not calltouch_data:  # Если нет данных то пробую запросить ещё раз
            self.get_calltouch_data(min_datetime, min_datetime)
            calltouch_data = CalltouchData.objects.filter(datetime__gte=min_datetime, datetime__lte=max_datetime)
            if not calltouch_data:  # Если всё ещё нет данных значит где-то баг
                raise Exception('Что-то пошло не так при получении данных Calltouch')

        # Заполняю calltouch_data у наших звонков
        failed_filters = []
        for call in queryset:
            found_call = find_call_in_another_model(call, call.num_from, call.num_redirect, calltouch_data)
            if found_call:
                call.calltouch_data = found_call
            else:
                failed_filters.append(call)

        Call.objects.bulk_update(queryset, ['calltouch_data'])

        # Отправляю на почту звонки для которых не удалось заполнить calltouch_data
        if failed_filters:
            urls = self.make_calls_admin_urls(failed_filters)
            body = 'Эти звонки не получилось найти в Calltouch:\n' + urls
            send_email('Не удалось привязать звонки к Calltouch', body, env('EMAIL_FOR_ERRORS'))

        return queryset

    def post_calls_import(self, json):
        """
        Отправляет наши данные на звонок Calltouch
        :param json:
        :return:
        """
        # https://www.calltouch.ru/support/nastroyka-integratsii-s-proizvolnymi-cpa-ploshchadkami/
        url = 'https://api.calltouch.ru/calls-service/v1/api/cpa-platforms/calls/import'
        result = self.request_api(url, 'POST', json=json)
        return result

    def send_our_data_to_calltouch(self, queryset: QuerySet[Call]):
        """
        Берёт Call queryset и по каждому отправляет POST-запрос в Calltouch
        :param queryset:
        :return:
        """
        for call in queryset:
            if not call.calltouch_data:
                continue

            if call.target in [TargetChoice.YES, TargetChoice.PM_YES]:
                state = 'online_idea_target'
            else:
                state = 'online_idea_not_target'

            tags = self.make_call_tags(call)
            tags = ','.join(tags)

            price = str(round(call.call_price / 120 * 100, 2)) if call.call_price else 0

            json = {
                "platformName": "online-idea",
                "siteId": int(call.calltouch_data.site_id),
                "platformCallId": call.primatel_call_id,
                "state": state,
                "tags": tags,
                "price": price,
                "currency": "rub",
                "clientPhone": call.num_from,
                "date": str(call.calltouch_data.timestamp),
                "offerId": call.client_primatel.login
            }
            self.post_calls_import(json)

    def make_call_tags(self, call: Call) -> List[str]:
        """
        Возвращает список тегов
        :param call:
        :return:
        """
        tags = []
        if call.status:
            tags.append(call.status)
        if call.mark:
            tags.append(call.mark.mark)
        if call.model:
            tags.append(call.model.model)
        if call.moderation:
            tags.append(ModerationChoice.get_site_name_by_choice(choice=call.moderation))
        return tags

    def check_tags(self, datefrom: datetime, dateto: datetime) -> None:
        """
        Проверяют данные наших звонков с тегами Calltouch. Если есть несовпадающие то отправляет на почту
        :param datefrom:
        :param dateto:
        """
        # TODO после отправки наших данных делать запрос get_calls_details с params['withCallTags'] = True
        # TODO чтобы проверить всё ли дошло
        self.get_calltouch_data(datefrom, dateto)
        calls = Call.objects.filter(datetime__gte=datefrom, datetime__lte=dateto)
        # Убираю из queryset звонки для которых нет CalltouchSetting
        calltouch_settings = CalltouchSetting.objects.filter(active=True).values_list('client_primatel_id', flat=True)
        calls = calls.filter(Q(client_primatel_id__in=calltouch_settings))

        calls_with_failed_tags = []
        for call in calls:
            # Если не привязан к Calltouch то пропускаю т.к. другая функция сообщит об этом на почту
            if not call.calltouch_data:
                continue

            if not call.calltouch_data.call_tags:  # Если у Calltouch нет тегов значит наши не дошли
                calls_with_failed_tags.append(call)
                continue

            calltouch_tags = call.calltouch_data.call_tags
            call_tags = self.make_call_tags(call)
            calltouch_tags = [name for item in calltouch_tags for name in item['names']]  # Объединяю теги
            if not all(tag in calltouch_tags for tag in call_tags):
                calls_with_failed_tags.append(call)

        # Отправляю на почту звонки у которых теги не совпадают
        if calls_with_failed_tags:
            urls = self.make_calls_admin_urls(calls_with_failed_tags)
            body = 'Теги в Calltouch не совпадают с данными наших звонков:\n' + urls
            send_email('Теги Calltouch не совпадают', body, env('EMAIL_FOR_ERRORS'))

    def make_calls_admin_urls(self, calls: List[Call]):
        """
        Возвращает ссылки на редактирование Call в админ панели
        :param calls:
        :return:
        """
        website = env('WEBSITE')
        admin_urls = [reverse('admin:calls_call_change', args=[call.id]) for call in calls]
        full_urls = '\n'.join([f'{website}{url}' for url in admin_urls])
        return full_urls
