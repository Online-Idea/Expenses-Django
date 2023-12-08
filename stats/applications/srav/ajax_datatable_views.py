import ast
import html

from ajax_datatable.views import AjaxDatatableView

from applications.srav.models import AutoruParsedAd
from libs.services.utils import split_daterange


class AutoruParsedAdAjaxDatatableView(AjaxDatatableView):
    model = AutoruParsedAd
    title = 'Сравнительная выдача'
    initial_order = [
        ['datetime', 'desc'],
        ['region', 'asc'],
        ['mark', 'asc'],
        ['model', 'asc'],
        ['complectation', 'asc'],
        ['modification', 'asc'],
        ['year', 'asc'],
        ['position_actual', 'asc'],
    ]
    length_menu = [[10, 20, 50, 100], [10, 20, 50, 100]]
    search_values_separator = '+'

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'id', 'visible': False, },
        {'name': 'datetime', 'visible': False, 'orderable': True, 'title': 'Дата и время'},
        {'name': 'region', 'visible': False, 'orderable': True, 'title': 'Регион'},
        {'name': 'mark', 'foreign_field': 'mark__mark', 'title': 'Марка'},
        {'name': 'model', 'foreign_field': 'model__model', 'title': 'Модель'},
        {'name': 'complectation', 'title': 'Комплектация'},
        {'name': 'modification', 'visible': False, 'orderable': True, 'title': 'Модификация'},
        {'name': 'year', 'title': 'Год'},
        {'name': 'dealer', 'title': 'Дилер'},
        {'name': 'price_with_discount', 'title': 'Цена со скидками'},
        {'name': 'price_no_discount', 'title': 'Цена без скидок'},
        {'name': 'with_nds', 'title': 'Цена с НДС'},
        {'name': 'position_actual', 'title': 'Позиция по актуальности'},
        {'name': 'position_total', 'title': 'Позиция общая'},
        {'name': 'link', 'visible': False, 'searchable': True, },
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

        queryset = (
            self.model.objects.prefetch_related(
                'mark', 'model', 'client'
            )
            .filter(**filter_params)
            .order_by('-datetime', 'region', 'mark', 'model')
        )
        return queryset
