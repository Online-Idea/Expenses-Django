from datetime import datetime, timedelta


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
