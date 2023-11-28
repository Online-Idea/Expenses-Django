import datetime
import json

import pandas as pd
from django.db.models import QuerySet
from django.http import HttpResponse
from openpyxl.workbook import Workbook
from plotly.subplots import make_subplots
import plotly.graph_objs as go

from applications.auction.forms import AuctionChooseForm
from applications.auction.models import AutoruAuctionHistory
from libs.services.utils import xlsx_column_width, split_daterange


def get_auction_data(request):
    """
    Возвращает данные истории аукциона по форме с сайта.
    Вынес это отдельно чтобы использовать для разных кнопок
    :param request:
    :return: context с данными формы и с Django QuerySet с историей аукциона
    """
    form = AuctionChooseForm(request.POST)

    if not form.is_valid():
        return HttpResponse(status=400)

    daterange = split_daterange(form.cleaned_data.get('daterange'))

    # Выбранные марки
    marks_checked = [m for m in request.POST.getlist('mark_checkbox')]
    # Выбранные регионы
    regions_checked = [r for r in request.POST.getlist('region_checkbox')]

    filter_params = {
        'datetime__gte': daterange['from'],
        'datetime__lte': daterange['to'],
        'mark_id__in': marks_checked,
        'autoru_region__in': regions_checked
    }

    # Только первые места
    only_first = form.cleaned_data.get('only_first')
    if only_first:
        filter_params['position'] = 1

    # Все дилеры заполнены
    all_dealers_filled = form.cleaned_data.get('all_dealers_filled')
    if all_dealers_filled:
        filter_params['dealer__gt'] = ''

    # Данные истории аукциона
    auction_data = (
        AutoruAuctionHistory.objects.select_related(
            "mark", "model", "client"
        )
        .filter(**filter_params)
        .order_by("-datetime", "autoru_region", "mark", "model", "position")
    )
    context = {
        'form': form,
        'marks_checked': json.dumps(marks_checked),
        'regions_checked': json.dumps(regions_checked),
        'datefrom': daterange['start'],
        'dateto': daterange['end'],
        'auction_data': auction_data,
    }
    return context


def plot_auction(data: QuerySet):
    df = pd.DataFrame.from_records(data)

    df = df.rename(columns={"mark__mark": "mark", "model__model": "model", "client__name": "client"})

    # Только первая позиция
    df = df[df['position'] == 1]

    uniq_models = df['model'].unique()

    fig = make_subplots(rows=len(uniq_models), cols=1, subplot_titles=uniq_models)

    for i, model in enumerate(uniq_models):
        data = df[df['model'] == model]
        y_min, y_max = data['bid'].min(), data['bid'].max()
        fig.add_trace(
            go.Scatter(x=data['datetime'], y=data['bid']),
            row=i + 1, col=1
        )
        fig.update_yaxes(range=[y_min - 0.2 * (y_max - y_min),
                                y_max + 0.2 * (y_max - y_min)],
                         row=i + 1, col=1)
    fig_title = f'{df["autoru_region"][0]}<br>{df["mark"][0]}'
    fig.update_layout(title_text=fig_title, showlegend=False,
                      height=len(uniq_models) * 200, margin={'t': 130, 'b': 130},
                      plot_bgcolor='white')
    fig.update_xaxes(gridcolor='#E1E1E0')
    fig.update_yaxes(gridcolor='#E1E1E0', tickformat=',.0f')
    fig.update_traces(line={'shape': 'spline'})

    # Generate the HTML code for the plot
    return fig.to_html(full_html=False)


def make_xlsx_for_download(context: dict) -> Workbook:
    """
    Создаёт xlsx файл для скачивания
    :param context: словарь с данными аукциона
    :return: openpyxl Workbook
    """
    wb = Workbook()
    ws = wb.active
    headers = ['id', 'Дата и время', 'Регион', 'Марка', 'Модель', 'Позиция', 'Ставка', 'Дилер',
               'Количество конкурентов']
    ws.append(headers)
    data = context['auction_data'].values_list('id', 'datetime', 'autoru_region', 'mark__mark', 'model__model',
                                               'position', 'bid', 'dealer', 'competitors')
    for row in data:
        row = [dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo else dt for dt in row]
        row = [dt + datetime.timedelta(hours=3) if isinstance(dt, datetime.datetime) else dt for dt in row]
        ws.append(row)

    ws = xlsx_column_width(ws)
    return wb
