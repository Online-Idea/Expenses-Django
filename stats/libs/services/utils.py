from datetime import datetime, timedelta
from django.db import models
from openpyxl.workbook import Workbook


def last_30_days():
    minus_30 = (datetime.now() - timedelta(days=31)).replace(hour=0, minute=0)
    yesterday = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59)
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
    date_start = [int(i) for i in dates[0].split('.')]
    date_end = [int(i) for i in dates[2].split('.')]
    datefrom = datetime(date_start[2], date_start[1], date_start[0], 00, 00, 00, 629013)
    dateto = datetime(date_end[2], date_end[1], date_end[0], 23, 59, 59, 629013)
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
