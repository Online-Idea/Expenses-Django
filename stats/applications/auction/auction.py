import datetime
import json
from typing import Union

import numpy as np
import pandas as pd
from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils import timezone
from openpyxl.workbook import Workbook
from pandas import DataFrame
from plotly.subplots import make_subplots
import plotly.graph_objs as go

from applications.accounts.models import Client
from applications.auction.forms import AuctionChooseForm
from applications.auction.models import AutoruAuctionHistory
from libs.autoru.models import AutoruRegion
from libs.autoru.refactor_autoru import AutoruLogic
from applications.mainapp.models import Mark, Model
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

    daterange_str = form.cleaned_data.get('daterange')
    daterange = split_daterange(daterange_str)

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

    filter_params.pop('datetime__gte')
    filter_params.pop('datetime__lte')
    filter_params['daterange'] = daterange_str

    context = {
        'form': form,
        'marks_checked': json.dumps(marks_checked),
        'regions_checked': json.dumps(regions_checked),
        'datefrom': daterange['start'],
        'dateto': daterange['end'],
        'auction_data': auction_data,
        'filter_params': filter_params,
    }
    return context


def plot_auction(data: QuerySet):
    df = pd.DataFrame.from_records(data)

    df = df.rename(columns={"mark__name": "mark", "model__name": "model", "client__name": "client"})

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


def prepare_auction_history(data: dict, datetime_: datetime) -> Union[DataFrame, None]:
    """
    Обработка данных аукциона
    :param data: список с ответами по аукциону от API авто.ру
    :param datetime_: дата и время
    :return: обработанный df
    """
    # Правки данных перед pandas
    data2 = {'states': []}
    for state in data['states']:
        if 'base_price' not in state:  # Если нет Базовой цены значит пропускаем
            continue

        if 'competitive_bids' not in state:  # Если нет конкурентов
            if 'current_bid' not in state:  # Если нет нашей ставки
                # Сохраняю просто Базовую цену
                state['competitive_bids'] = [{'bid': state['base_price'], 'competitors': 0}]
            else:
                # Сохраняю только нашу ставку
                state['competitive_bids'] = [{'bid': '000', 'competitors': 0}]

        data2['states'].append(state)
    data = data2

    if not data['states']:
        return

    # Данные в pandas
    df = pd.json_normalize(data['states'],
                           record_path=['competitive_bids'],
                           meta=[['context', 'region_id'],
                                 ['context', 'mark_name'],
                                 ['context', 'model_name'],
                                 ['current_bid'],
                                 ['client']],
                           errors='ignore')
    df[['bid', 'current_bid']] = df[['bid', 'current_bid']].apply(lambda x: x.str[:-2])
    df['current_bid'] = df['current_bid'].fillna(0)
    df[['bid', 'current_bid', 'competitors']] = df[['bid', 'current_bid', 'competitors']].astype(int)

    # Для ставок, по которым несколько дилеров размещаются, делаю копии по количеству этих дилеров
    dfs = []
    for _, row in df.iterrows():
        if row['competitors'] > 1:
            dfs.append(pd.concat([pd.DataFrame(row).T] * (row['competitors'] - 1)))

    dfs.append(df)
    new_df = pd.concat(dfs)

    # Наша ставка
    current_bids = df[df['current_bid'] > 0]
    current_bids = current_bids[
        ['context.region_id', 'context.mark_name', 'context.model_name', 'current_bid', 'client']].drop_duplicates()
    new_df = new_df.drop(columns='client')
    current_bids['competitors'] = 1
    current_bids['bid'] = current_bids['current_bid']
    new_df = pd.concat([new_df, current_bids])

    # Сортирую
    new_df = new_df.sort_values(['context.region_id', 'context.mark_name', 'context.model_name', 'bid'],
                                ascending=[True, True, True, False])

    # Регионы словами
    unique_regions_ids = new_df['context.region_id'].unique()
    autoru_regions = AutoruRegion.objects.filter(autoru_region_id__in=unique_regions_ids)
    unique_regions_names = {}
    for region_id in unique_regions_ids:
        unique_regions_names[region_id] = autoru_regions.filter(autoru_region_id=region_id)[0].name
    new_df['region_name'] = new_df['context.region_id'].replace(unique_regions_names)

    # Марки как объекты из базы
    unique_marks_names = new_df['context.mark_name'].unique()
    marks = Mark.objects.filter(name__in=unique_marks_names)

    # Добавляю марки которых нет в базе
    if len(unique_marks_names) != len(marks):
        new_marks = []
        marks_str = [m.mark for m in marks]

        for mark in unique_marks_names:
            if mark not in marks_str:
                new_marks.append(Mark(name=mark, teleph=mark, autoru=mark, avito=mark, drom=mark, human_name=mark))
        Mark.objects.bulk_create(new_marks)
        marks = Mark.objects.filter(name__in=unique_marks_names)

    # Подставляю
    unique_marks_objs = {}
    for mark_name in unique_marks_names:
        unique_marks_objs[mark_name] = marks.filter(name=mark_name)[0]
    new_df['mark_obj'] = new_df['context.mark_name'].replace(unique_marks_objs)

    # Модели как объекты из базы
    unique_marks_models_names = new_df[['context.mark_name', 'context.model_name']].drop_duplicates()
    models = Model.objects.filter(mark__name__in=unique_marks_names)

    # Добавляю модели которых нет в базе
    new_models = []
    for _, row in unique_marks_models_names.iterrows():
        curr_mark = row['context.mark_name']
        curr_model = row['context.model_name']
        if not models.filter(mark__name=curr_mark, name=curr_model):
            new_models.append(Model(mark=marks.filter(name=curr_mark)[0], name=curr_model, teleph=curr_model,
                                    autoru=curr_model, avito=curr_model, drom=curr_model, human_name=curr_model))
    Model.objects.bulk_create(new_models)

    # Подставляю
    models = Model.objects.filter(mark__name__in=unique_marks_names)
    models_objs = []
    for _, row in new_df.iterrows():
        models_objs.append(models.filter(
            mark__name=row['context.mark_name'],
            name=row['context.model_name'])[0])

    new_df['model_obj'] = models_objs

    # Позиция
    new_df['position'] = new_df.groupby(['context.region_id', 'context.mark_name', 'context.model_name']).cumcount() + 1

    # Дата и время
    new_df['datetime'] = datetime_

    # Оставляю нужные столбцы
    new_df = new_df[['datetime', 'region_name', 'mark_obj', 'model_obj', 'position', 'bid', 'competitors', 'client']]

    # Удаляю лишние строки. Это когда мы одни участвуем в аукционе
    new_df = new_df[new_df['bid'] != 0]

    # Переименовываю
    new_df = new_df.rename(columns={
        'region_name': 'autoru_region',
        'mark_obj': 'mark',
        'model_obj': 'model',
    })
    return new_df


def auction_history_drop_unknown(all_bids: DataFrame) -> DataFrame:
    """
    Удаляю лишние строки с неизвестными дилерами которые на самом деле наши дилеры.
    :param all_bids: df со всеми ставками
    :return: обработанный df
    """
    # Поля для сортировок
    all_bids['mark_value'] = all_bids['mark'].apply(lambda x: x.name)
    all_bids['model_value'] = all_bids['model'].apply(lambda x: x.name)

    # Тут дропаю неизвестных дилеров, заменяя их нашими клиентами.
    # Всех наших клиентов сортирую в верх таблицы чтобы удалялись строки-дубли где клиентов нет
    def sort_client(x):
        return 1 if isinstance(x, type(np.nan)) else 0

    all_bids = all_bids.sort_values(by='client', key=lambda x: x.apply(sort_client))

    uniqueness = ['datetime', 'autoru_region', 'mark_value', 'model_value', 'position']
    all_bids = all_bids.reset_index(drop=True)
    all_bids = all_bids.drop_duplicates(subset=uniqueness + ['client'])

    client_df = all_bids[uniqueness + ['client']].copy()
    client_notnan = client_df[client_df['client'].notna()].copy()

    rows_to_drop = []
    for index, row in client_notnan[uniqueness].iterrows():
        rows_to_drop.append(client_df.loc[(client_df['datetime'] == row.iloc[0]) &
                                          (client_df['autoru_region'] == row.iloc[1]) &
                                          (client_df['mark_value'] == row.iloc[2]) &
                                          (client_df['model_value'] == row.iloc[3]) &
                                          (client_df['position'] == row.iloc[4]) &
                                          (client_df['client'].isna())])

    if rows_to_drop:
        rows_to_drop = pd.concat(rows_to_drop)
        all_bids = all_bids.drop(rows_to_drop.index, axis=0)

    # Здесь удаляю дубли в случае если мы не участвуем в аукционе
    all_bids = all_bids.drop_duplicates(subset=uniqueness)

    # Сортировка
    sorted_df = all_bids.sort_values(by=uniqueness)

    # Удаляю временные столбцы
    sorted_df = sorted_df.drop(['mark_value', 'model_value'], axis=1)
    sorted_df['client'] = sorted_df['client'].replace(np.nan, None)
    return sorted_df


def add_auction_history(data: DataFrame) -> None:
    """
    Добавляет историю аукциона в базу
    :param data: df с данными аукциона
    """
    objs = [AutoruAuctionHistory(
        datetime=timezone.make_aware(row['datetime']),
        autoru_region=row['autoru_region'],
        mark=row['mark'],
        model=row['model'],
        position=row['position'],
        bid=row['bid'],
        competitors=row['competitors'],
        client=row['client'],
        dealer=''
    ) for index, row in data.iterrows()]

    AutoruAuctionHistory.objects.bulk_create(objs)


def get_and_add_auction_history(clients: Client) -> None:
    """
    Получает и добавляет историю аукциона
    :param clients: Client объекты
    :return:
    """
    logic = AutoruLogic()
    responses = [logic.get_auction_history(client) for client in clients]

    datetime_ = datetime.datetime.today()
    dfs = [prepare_auction_history(data=response, datetime_=datetime_) for response in responses if response]
    if dfs:
        all_bids = pd.concat(dfs)
        all_bids = auction_history_drop_unknown(all_bids)
        add_auction_history(all_bids)
