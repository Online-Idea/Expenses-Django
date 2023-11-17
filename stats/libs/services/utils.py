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
