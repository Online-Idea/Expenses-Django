import ast
import html
from ajax_datatable.views import AjaxDatatableView

from applications.auction.models import AutoruAuctionHistory
from libs.services.utils import split_daterange


class AuctionAjaxDatatableView(AjaxDatatableView):
    model = AutoruAuctionHistory
    title = 'Аукцион'
    initial_order = [
        ['datetime', 'desc'],
    ]
    length_menu = [[10, 20, 50, 100], [10, 20, 50, 100]]
    search_values_separator = '+'

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'id', 'visible': False, },
        {'name': 'datetime', 'visible': False, 'orderable': True, 'title': 'Дата и время'},
        {'name': 'autoru_region', 'visible': False, 'orderable': True, 'title': 'Регион'},
        {'name': 'mark', 'foreign_field': 'mark__mark', 'title': 'Марка'},
        {'name': 'model', 'foreign_field': 'model__model', 'title': 'Модель'},
        {'name': 'position', 'title': 'Позиция'},
        {'name': 'bid', 'title': 'Ставка'},
        {'name': 'dealer', 'title': 'Дилер'},
        {'name': 'competitors', 'title': 'Конкурентов по ставке'},
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
            .order_by('-datetime')
        )
        return queryset
