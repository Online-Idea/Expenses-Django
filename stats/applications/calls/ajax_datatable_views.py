import ast
import html
from datetime import timedelta
from urllib.parse import urlencode

from ajax_datatable.views import AjaxDatatableView
from django.urls import reverse

from applications.accounts.models import Client
from applications.calls.models import Call
from libs.services.utils import split_daterange
from stats.settings import env


class CallDatatableView(AjaxDatatableView):
    model = Call
    title = 'Звонки'
    initial_order = [
        ['client', 'asc'],
        ['datetime', 'desc'],
    ]
    length_menu = [[10, 20, 50, 100], [10, 20, 50, 100]]
    search_values_separator = '+'

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'id', 'visible': False, },
        {'name': 'edit', 'title': 'Ред.', 'placeholder': True, 'searchable': False, 'orderable': False},
        {'name': 'record', 'title': 'Запись звонка', 'searchable': False, 'orderable': False, 'autofilter': False},
        {'name': 'primatel_call_id', 'visible': False, },
        {'name': 'client', 'title': 'Клиент', 'foreign_field': 'client_primatel__client__name', 'orderable': True,
            'searchable': True, },
        {'name': 'datetime', 'title': 'Дата и время', 'orderable': True, 'searchable': True},
        {'name': 'num_from', 'title': 'Исходящий', 'orderable': True, 'searchable': True},
        {'name': 'num_to', 'title': 'Входящий', 'orderable': True, 'searchable': True},
        {'name': 'duration', 'title': 'Длительность', 'orderable': True},
        {'name': 'mark', 'title': 'Марка', 'foreign_field': 'mark__mark', 'orderable': True, 'searchable': True},
        {'name': 'model', 'title': 'Модель', 'foreign_field': 'model__model', 'orderable': True, 'searchable': True},
        {'name': 'target', 'title': 'Целевой', 'orderable': True, 'choices': True, 'autofilter': True},
        {'name': 'moderation', 'title': 'М', 'orderable': True, 'choices': True, 'autofilter': True},
        {'name': 'status', 'title': 'Статус звонка', 'orderable': True, 'choices': True, 'autofilter': True},
        {'name': 'repeat_call', 'visible': False },
        {'name': 'other_comments', 'title': 'Остальные комментарии', 'searchable': True},
        {'name': 'client_primatel', 'visible': False, },
        {'name': 'client_name', 'title': 'Имя клиента', 'searchable': True},
        {'name': 'manager_name', 'title': 'Имя менеджера', 'orderable': True, 'searchable': True},
        {'name': 'car_price', 'title': 'Стоимость автомобиля', 'orderable': True, },
        {'name': 'call_price', 'title': 'Стоимость звонка', 'orderable': True, },
        {'name': 'manual_edit', 'title': 'Ручное редактирование звонка', 'orderable': True, },
        {'name': 'color', 'title': 'Цвет', 'orderable': True, },
        {'name': 'body', 'title': 'Кузов', 'orderable': True, },
        {'name': 'drive', 'title': 'Привод', 'orderable': True, },
        {'name': 'engine', 'title': 'Двигатель', 'orderable': True, },
        {'name': 'complectation', 'title': 'Комплектация', 'orderable': True, },
        {'name': 'attention', 'title': 'Обратить внимание', 'orderable': True, },
        {'name': 'city', 'title': 'Город', 'orderable': True, },
        {'name': 'delete', 'title': 'Удалить', 'placeholder': True, 'searchable': False, 'orderable': False},
    ]

    def get_initial_queryset(self, request=None):
        # Получаю переданные данные
        filter_params = request.REQUEST.get('filter_params')
        filter_params = html.unescape(filter_params)
        filter_params = ast.literal_eval(filter_params)

        # Обрабатываю даты
        daterange = split_daterange(filter_params['daterange'])
        filter_params['datetime__gte'] = daterange['from']
        filter_params['datetime__lte'] = daterange['to']
        filter_params.pop('daterange', None)

        # Клиенты
        if 'clients_checked' in filter_params:
            filter_params['client_primatel__client__in'] = filter_params['clients_checked']
            filter_params.pop('clients_checked', None)

        # Исключаю удалённые
        filter_params['deleted'] = False

        queryset = (
            self.model.objects.prefetch_related(
                'mark', 'model', 'client_primatel'
            )
            .filter(**filter_params)
            .order_by('datetime')
        )
        return queryset

    def customize_row(self, row, obj):
        # TODO Добавить прямую (или с фильтрами) ссылку на agency.auto.ru
        #  когда будет настроена интеграция наших звонков со звонками авто.ру
        # Редактирование звонка
        edit_button = f'''
            <button class="btn btn-primary edit-btn" data-id="{row["pk"]}" data-bs-toggle="modal" data-bs-target="#callModal">
                <i class="fa-regular fa-pen-to-square"></i>
            </button> 
        '''
        row['edit'] = edit_button

        # Кнопка записи звонка
        play_record_button = f'''
            <button data-audio-url="{row['record']}" class="btn btn-primary play-record-btn">
                <i class="fa-regular fa-circle-play"></i>
            </button>
        '''
        row['record'] = play_record_button

        # Ссылка в столбце Исходящий на фильтр по клиенту, периоду и номеру исходящего
        datefrom = (obj.datetime - timedelta(days=30)).strftime('%d-%m-%Y')
        dateto = obj.datetime.strftime('%d-%m-%Y')
        client = obj.client_primatel.client.id
        link = reverse('calls') + '?' + urlencode({'datefrom': datefrom, 'dateto': dateto, 'clients': client,
                                                   'num_from': obj.num_from})
        # Кнопки для копирования номеров в буфер
        row['num_from'] = f'''
            <div class="one-line">
                <a href="{link}">{row['num_from']}</a> <i class="fa-regular fa-copy" onclick="copyText(event)"></i>
            </div>
        '''
        row['num_to'] = f'''
            <div class="one-line">
                {row['num_to']} <i class="fa-regular fa-copy" onclick="copyText(event)"></i>
            </div>
        '''

        # Кнопка удаления
        delete_button = f'''
            <button class="btn btn-primary delete-btn" data-id="{row["pk"]}" onclick="deleteCall(event)">
                <i class="fa-solid fa-trash"></i>
            </button> 
        '''
        row['delete'] = delete_button

        return row
