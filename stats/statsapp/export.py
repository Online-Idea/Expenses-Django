from datetime import datetime
import pandas as pd
from openpyxl.reader.excel import load_workbook
from openpyxl.styles import Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

from statsapp.converter import save_on_ftp
from statsapp.models import TelephCalls


def export_calls_to_file() -> str:
    """
    Экспорт звонков в xlsx
    :return: имя файла
    """
    # РОЛЬФ клиенты которым это нужно
    # rolf_clients = {
    #     'Rolf_scoda_Center': 'РОЛЬФ Skoda Центр',
    #     'Rolf_Jetta_Center': 'РОЛЬФ Jetta Центр',
    #     'Rolf_moskvich_Himki': 'РОЛЬФ Москвич Химки',
    #     'Rolf_moskvich_Center': 'РОЛЬФ Москвич Центр',
    # }
    rolf_clients = {
        'porsche_nevsky': 'Порше Невский',
        'rolf_JLR_oct_spb': 'Рольф JLR Октябрьский СПБ',
        'rolf_multibrand_oct_spb': 'Рольф Мультибренд спб',
        'rolf_oktyabr_genesis_spb': 'Рольф Генезис СПБ',
        'rolf_viteb_exeed_spb': 'Рольф EXEED Витебский',
    }
    # Звонки из базы
    calls = TelephCalls.objects.filter(client__teleph_id__in=rolf_clients.keys())\
        .order_by('client_id', '-datetime').values()
    df = pd.DataFrame.from_records(calls)

    # Обработка столбцов
    # df['datetime'] = df['datetime'].dt.tz_convert(None)
    df['month_year'] = df['datetime'].dt.strftime('%m.%Y')
    df['datetime'] = df['datetime'].dt.strftime('%Y.%m.%d %H:%M:%S')
    df['moderation'] = df['moderation'].replace({'М': 'Авто.ру', 'М(Б)': 'Авто.ру', 'М(З)': 'Авто.ру'})
    df['client_id'] = df['client_id'].replace(rolf_clients)

    # Оставляю нужные столбцы
    df = df[['client_id', 'datetime', 'num_from', 'mark', 'model', 'target', 'moderation', 'call_price', 'month_year']]

    # Переименовываю заголовки
    df = df.rename(columns={
        'client_id': 'Клиент',
        'datetime': 'Дата и время',
        'num_from': 'Номер клиента',
        'mark': 'Марка',
        'model': 'Модель',
        'target': 'Целевой',
        'moderation': 'Площадка',
        'call_price': 'Стоимость звонка',
        'month_year': 'Месяц, год',
    })

    # Открываю xlsx
    file_name = f'Расходы РОЛЬФ.xlsx'
    file_path = f'temp/ROLF_stats/{file_name}'
    book = load_workbook(file_path)
    calls_sheet = book['Звонки']

    # Удаляю прошлые и вставляю новые
    calls_sheet.delete_rows(1, calls_sheet.max_row)
    for row in dataframe_to_rows(df, index=False, header=True):
        calls_sheet.append(row)

    # Меняю ширину столбцов
    for column in calls_sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        column_name = column[0].value

        if column_name in ['Площадка', 'Стоимость звонка']:
            calls_sheet.column_dimensions[column_letter].width = 15
        else:
            for cell in column:
                if cell.row == 1:
                    continue
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 4)
            calls_sheet.column_dimensions[column_letter].width = adjusted_width

    # Сохраняю
    book.save(file_path)

    save_on_ftp(file_path)

    # Сохраняю в xlsx
    # with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
    #     df.T.reset_index().T.to_excel(writer, sheet_name='Звонки', header=False, index=False)

    return file_name

