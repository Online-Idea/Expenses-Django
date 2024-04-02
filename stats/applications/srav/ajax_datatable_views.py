import ast
import html

from ajax_datatable.views import AjaxDatatableView

from applications.srav.models import AutoruParsedAd, SravPivot
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
    length_menu = [[10, 20, 50, 100, 250, 500, 1000], [10, 20, 50, 100, 250, 500, 1000]]
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


class ComparisonDatatableView(AjaxDatatableView):
    model = SravPivot
    title = 'Сравнительная'
    initial_order = [
        ['datetime', 'desc'],
        ['region', 'asc'],
        ['mark', 'asc'],
        ['model', 'asc'],
        ['complectation', 'asc'],
        ['modification', 'asc'],
        ['year', 'asc'],
        ['position_price', 'asc'],
    ]
    length_menu = [[10, 20, 50, 100, 250, 500, 1000], [10, 20, 50, 100, 250, 500, 1000]]
    search_values_separator = '+'

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'id', 'visible': False, },
        {'name': 'datetime', 'foreign_field': 'autoru_parsed_ad__datetime',
            'visible': False, 'orderable': True, 'title': 'Дата и время'},
        {'name': 'region', 'foreign_field': 'autoru_parsed_ad__region',
            'visible': False, 'orderable': True, 'title': 'Регион'},
        {'name': 'mark', 'foreign_field': 'autoru_parsed_ad__mark__mark', 'title': 'Марка', },
        {'name': 'model', 'foreign_field': 'autoru_parsed_ad__model__model', 'title': 'Модель', },
        {'name': 'complectation', 'foreign_field': 'autoru_parsed_ad__complectation', 'title': 'Комплектация', },
        {'name': 'modification', 'foreign_field': 'autoru_parsed_ad__modification',
            'visible': False, 'orderable': True, 'title': 'Модификация', },
        {'name': 'year', 'foreign_field': 'autoru_parsed_ad__year', 'title': 'Год', },
        {'name': 'dealer', 'foreign_field': 'autoru_parsed_ad__dealer', 'title': 'Дилер', },
        {'name': 'price_with_discount', 'foreign_field': 'autoru_parsed_ad__price_with_discount',
            'title': 'Цена со скидками', },
        {'name': 'price_no_discount', 'foreign_field': 'autoru_parsed_ad__price_no_discount',
            'title': 'Цена без скидок', },
        {'name': 'price_with_discount_diff', 'searchable': False, 'title': 'Разница цены со скидками', },
        {'name': 'price_no_discount_diff', 'searchable': False, 'title': 'Разница цены без скидок', },
        {'name': 'position_price', 'title': 'Позиция по цене', },
        {'name': 'position_actual', 'foreign_field': 'autoru_parsed_ad__position_actual',
            'title': 'Позиция по актуальности', },
        {'name': 'in_stock_count', 'title': 'В наличии', },
        {'name': 'for_order_count', 'title': 'Под заказ', },
        {'name': 'link', 'foreign_field': 'autoru_parsed_ad__link', 'visible': False, 'searchable': True, },
    ]

    def get_initial_queryset(self, request=None):
        # Получаю переданные данные
        filter_params = request.REQUEST.get('filter_params')
        filter_params = html.unescape(filter_params)
        filter_params = ast.literal_eval(filter_params)
        self.dealer_for_comparison = request.REQUEST.get('dealer_for_comparison')

        # Обрабатываю даты
        daterange = split_daterange(filter_params['daterange'])
        filter_params['autoru_parsed_ad__datetime__gte'] = daterange['from']
        filter_params['autoru_parsed_ad__datetime__lte'] = daterange['to']
        filter_params.pop('daterange', None)

        queryset = (
            self.model.objects.prefetch_related(
                'autoru_parsed_ad',
            )
            .filter(**filter_params)
        )
        self.qs = queryset
        return queryset

    def customize_row(self, row, obj):
        # Расчет столбцов Разница цены со скидками и Разница цены без скидок
        dealers_row = self.qs.filter(
            autoru_parsed_ad__mark__mark=row['mark'],
            autoru_parsed_ad__model__model=row['model'],
            autoru_parsed_ad__complectation=row['complectation'],
            autoru_parsed_ad__modification=row['modification'],
            autoru_parsed_ad__year=row['year'],
            autoru_parsed_ad__dealer=self.dealer_for_comparison,
        )
        if dealers_row:
            dealers_price_with_discount = dealers_row[0].autoru_parsed_ad.price_with_discount
            dealers_price_no_discount = dealers_row[0].autoru_parsed_ad.price_no_discount
            row['price_with_discount_diff'] = int(row['price_with_discount']) - dealers_price_with_discount
            row['price_no_discount_diff'] = int(row['price_no_discount']) - dealers_price_no_discount
        else:
            row['price_with_discount_diff'] = ''
            row['price_no_discount_diff'] = ''
