from ajax_datatable.views import AjaxDatatableView
from django.contrib.auth.models import Permission

from applications.srav.models import AutoruParsedAd


# Пример из инструкции django-ajax-datatable
class PermissionAjaxDatatableView(AjaxDatatableView):
    model = Permission
    title = 'Permissions'
    initial_order = [["app_label", "asc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]
    search_values_separator = '+'

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'id', 'visible': False, },
        {'name': 'codename', 'visible': True, },
        {'name': 'name', 'visible': True, },
        {'name': 'app_label', 'foreign_field': 'content_type__app_label', 'visible': True, },
        {'name': 'model', 'foreign_field': 'content_type__model', 'visible': True, },
    ]


class AutoruParsedAdAjaxDatatableView(AjaxDatatableView):
    model = AutoruParsedAd
    title = 'Сравнительная выдача'
    initial_order = [['position_actual', 'asc'], ]
    length_menu = [[10, 20, 50, 100], [10, 20, 50, 100]]
    search_values_separator = '+'

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'id', 'visible': False, },
        {'name': 'datetime', 'visible': False, },
        {'name': 'region', 'visible': False, },
        {'name': 'mark', 'visible': False, },
        {'name': 'model', },
        {'name': 'complectation', },
        {'name': 'modification', 'visible': False, },
        {'name': 'year', },
        {'name': 'dealer', },
        {'name': 'price_with_discount', },
        {'name': 'price_no_discount', },
        {'name': 'with_nds', },
        {'name': 'position_actual', },
        {'name': 'position_total', },
    ]
