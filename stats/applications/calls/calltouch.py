from datetime import datetime

import requests
from django.db.models import QuerySet, Min, Max
from django.utils import timezone
from requests.exceptions import JSONDecodeError

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
            if row['callId'] not in existing_calls:
                continue
            call = existing_calls.get(calltouch_call_id=row['callId'])
            call.call_tags = row['callTags']
            updated_calls.append(call)

        # TODO новые создавать, имеющиеся обновлять. А то сейчас дубли добавляет
        # TODO И почисти потом таблицу от дублей
        CalltouchData.objects.bulk_create(new_calls)
        CalltouchData.objects.bulk_update(updated_calls, ['call_tags'])

    def update_calls_with_calltouch_data(self, queryset: QuerySet[Call]):
        """
        Привязывает CalltouchData к нашим Call
        :return: обновлённые Call с заполненными calltouch_data
        """
        def filter_calltouch_data(calltouch_data, call, field, min_value, max_value):
            """
            Рекурсивная функция которая фильтрует CalltouchData пока не найдет 1 или более звонков.
            Ищет через уменьшение min_value и увеличение max_value.
            :param calltouch_data: CalltouchData queryset
            :param call: объект Call
            :param field: поле по которому фильтровать calltouch_data: 'timestamp' или 'duration'
            :param min_value: минимальное значение для field
            :param max_value: максимальное значение для field
            :return: список с отфильтрованными CalltouchData
            """
            filtered = [row for row in calltouch_data if min_value <= getattr(row, field) <= max_value]
            if len(filtered) >= 1:
                return filtered
            else:
                min_value -= 1
                max_value += 1
                return filter_calltouch_data(calltouch_data, call, field, min_value, max_value)

        # Данные по которым отфильтрую CalltouchData
        # client_primatels = queryset.distinct('client_primatel')
        # marks = queryset.distinct('mark')
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
            timestamp_min = datetime.timestamp(call.datetime)
            timestamp_max = timestamp_min
            calltouch_data_by_numbers = calltouch_data.filter(num_from=call.num_from, num_to=call.num_redirect)

            # Если есть звонки совпадающие по num_from и num_to то пробую найти нужный по timestamp
            if calltouch_data_by_numbers:
                filtered_by_timestamp = filter_calltouch_data(calltouch_data_by_numbers, call, 'timestamp',
                                                              timestamp_min, timestamp_max)
            else:  # Иначе звонка почему-то нет в Calltouch, добавляю в список на отправление на почту
                failed_filters.append(call)

            # Если фильтрация по timestamp дала 1 результат значит звонок найден
            if len(filtered_by_timestamp) == 1:
                call.calltouch_data = filtered_by_timestamp[0]
            else:  # Иначе проверяю по duration
                filtered_by_duration = filter_calltouch_data(filtered_by_timestamp, call, 'duration',
                                                             call.duration, call.duration)
                # Если фильтрация по duration дала 1 результат значит звонок найден
                if len(filtered_by_duration) == 1:
                    call.calltouch_data = filtered_by_duration[0]
                else:  # Иначе ошибка, добавляю в список на отправление на почту
                    failed_filters.append(call)

        updated_calls = Call.objects.bulk_update(queryset, ['calltouch_data'])

        # Отправляю на почту звонки для которых не удалось заполнить calltouch_data
        if failed_filters:
            failed_filters = '\n'.join([str(i) for i in failed_filters])
            send_email('Не удалось привязать звонки к Calltouch', failed_filters, env('EMAIL_FOR_ERRORS'))

        return updated_calls


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

            website = ModerationChoice.get_site_name_by_choice(choice=call.moderation)
            tags = ','.join([call.status, call.mark.mark, call.model.model, website, 'test333'])

            json = {
                "platformName": "online-idea",
                "siteId": int(call.calltouch_data.site_id),
                "platformCallId": call.primatel_call_id,
                "state": state,
                "tags": tags,
                "price": str(round(call.call_price / 120 * 100, 2)),
                "currency": "rub",
                "clientPhone": call.num_from,
                "date": str(call.calltouch_data.timestamp),
                "offerId": call.client_primatel.login
            }
            self.post_calls_import(json)
        # TODO после отправки наших данных делать запрос get_calls_details с params['withCallTags'] = True
        # TODO чтобы проверить всё ли дошло
