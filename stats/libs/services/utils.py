import csv
import re
from datetime import datetime, timedelta
from typing import List, Union

import pandas as pd
from django.db import models
from django.utils import timezone
from openpyxl.workbook import Workbook


def last_30_days():
    minus_30 = (datetime.now() - timedelta(days=31)).replace(hour=0, minute=0)
    yesterday = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59)
    minus_30 = timezone.make_aware(minus_30)
    yesterday = timezone.make_aware(yesterday)
    return minus_30, yesterday


def xlsx_column_width(sheet, custom_width: dict = None):
    """
    Меняет ширину столбцов в xlsx файле с помощью openpyxl. Если имя столбца не указано в custom_width то
    ширина будет по длине ячейки с максимальным количеством символов.
    :param sheet: лист openpyxl
    :param custom_width: словарь с ручной шириной столбцов, пример {'имя_столбца': 15}
    :return: лист openpyxl
    """
    for column in sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        column_name = column[0].value

        if custom_width and column_name in custom_width.keys():
            sheet.column_dimensions[column_letter].width = custom_width[column_name]
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
            sheet.column_dimensions[column_letter].width = adjusted_width

    return sheet


def split_daterange(daterange: str) -> dict:
    """
    Разбивает период из форм на отдельные даты
    :param daterange: строка периода из формы
    :return: словарь с датой до и по. В виде строки и в виде datetime
    """
    dates = daterange.split(' ')
    # Разбиваю дату на день, месяц, год
    separator = '.' if '.' in dates[0] else '-'
    date_start = [int(i) for i in dates[0].split(separator)]
    date_end = [int(i) for i in dates[2].split(separator)]
    datefrom = datetime(date_start[2], date_start[1], date_start[0], 00, 00, 00, 0)
    dateto = datetime(date_end[2], date_end[1], date_end[0], 23, 59, 59, 999999)
    return {
        'start': date_start,
        'end': date_end,
        'from': datefrom,
        'to': dateto,
    }


def get_all_fields_verbose_names(model, prefix='') -> dict:
    """
    Возвращает verbose_name всех полей модели.
    Если есть внешние ключи то по ним также проходит.
    :param model: Django модель
    :param prefix:
    :return: словарь {'field': verbose_name, 'fk_field__field': verbose_name}
    """
    result = {}
    for field in model._meta.fields:
        if isinstance(field, models.ForeignKey):
            related_model = field.related_model
            related_prefix = f'{prefix}{field.name}__'
            related_result = get_all_fields_verbose_names(related_model, related_prefix)
            result.update(related_result)
        else:
            result[f'{prefix}{field.name}'] = field.verbose_name
    return result


def make_xlsx_for_download(qs, headers) -> Workbook:
    """
    Создаёт xlsx файл для скачивания
    :param qs: list of tuples
    :param headers: list заголовков
    :return: openpyxl Workbook
    """
    wb = Workbook()
    ws = wb.active
    ws.append(headers)

    replacement_bool = {True: 'да', False: 'нет'}

    for row in qs:
        row = [dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo else dt for dt in row]
        row = [dt + timedelta(hours=3) if isinstance(dt, datetime) else dt for dt in row]
        row = [replacement_bool[element] if isinstance(element, bool) else element for element in row]
        ws.append(row)

    ws = xlsx_column_width(ws)
    return wb


def get_models_verbose_names(model):
    """
    Возвращает список verbose_name полей модели
    :param model: Django модель
    :return:
    """
    return [f.verbose_name for f in model._meta.get_fields() if hasattr(f, 'verbose_name')]


def export_queryset_to_csv(queryset, file_path=None):
    """
    Экспортирует Queryset в csv
    :param queryset:
    :param file_path:
    :return:
    """
    if not file_path:
        file_path = 'temp/exported_queryset.csv'

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        fields_list = queryset[0]._meta.get_fields()
        field_names = [field.name for field in fields_list]
        writer.writerow(field_names)
        for row in queryset.values_list():
            writer.writerow([cell for cell in row])


def pandas_numeric_to_object(df: pd.DataFrame) -> pd.DataFrame:
    """
    Меняет тип в датафрейме на object если он числовой, потом заполняет nan как ''
    :param df:
    :return:
    """
    for col in df.columns:
        if df[col].dtype.kind in 'bifc':
            df[col] = df[col].astype(object)
            df[col] = df[col].fillna('')
    return df


def extract_digits(s: str) -> str:
    """
    Вытаскивает из строки числа, сцепляет их как одну строку.
    :param s:
    :return:
    """
    return re.sub(r'\D', '', s)


def datetime_ru_str_to_datetime(*args) -> List[datetime]:
    """
    Переводит строковые даты и время в datetime объекты
    :param args: строки с датой и временем, форматы:
        '%d.%m.%Y %H:%M:%S',
        '%d.%m.%Y %H:%M',
        '%d.%m.%Y'
        datetime тоже можно передавать - вернутся без изменений
    :return: список с datetime объектами
    """
    dt_formats = [
        '%d.%m.%Y %H:%M:%S',
        '%d.%m.%Y %H:%M',
        '%d.%m.%Y'
    ]
    result = []
    for arg in args:
        if isinstance(arg, datetime):
            result.append(arg)
            continue

        for dt_format in dt_formats:
            try:
                parsed_date = datetime.strptime(arg, dt_format)
            except ValueError:
                continue
            else:
                result.append(parsed_date)
                break
    return result


def get_nested_value(dictionary: dict, keys: str, default: Union[str, int] = None) -> Union[str, int]:
    """
    Возвращает данные со словаря dictionary по ключам keys если эти данные есть в словаре.
    Иначе возвращает default.
    Например если dictionary = {'key1': {'key2': 123}} и keys = 'key1.key2' то вернёт 123
    :param dictionary: словарь с данными
    :param keys: ключи в словарях по которым нужно взять данные
    :param default: значение по умолчанию если по ключам keys нет данных
    :return: данные по ключам keys либо default
    """
    value = dictionary
    for key in keys.split('.'):
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def add_keys_to_dict(existing_dict: dict, keys_path: str, value: any = None) -> dict:
    """
    Создаёт ключи в словаре если их нет.
    Если value передано то ставит его как значение последнего ключа иначе оставляет пустым словарём
    :param existing_dict: существующий словарь
    :param keys_path: путь ключей который должен быть в словаре. Строка с ключами разделёнными точкой
    :param value: значение для последнего ключа
    :return: словарь с нужными ключами
    """
    keys = keys_path.split('.')
    current_dict = existing_dict

    for key in keys[:-1]:  # Traverse until the second-to-last key
        if key not in current_dict:
            current_dict[key] = {}
        current_dict = current_dict[key]

    # If value is provided, set it; otherwise, set the last key to an empty dict
    if value is not None:
        current_dict[keys[-1]] = value
    else:
        current_dict[keys[-1]] = {}

    return existing_dict
