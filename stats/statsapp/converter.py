import ftplib
from ftplib import FTP
from pathlib import Path
import os
import requests
import datetime
import xml.etree.ElementTree as ET
import xlsxwriter
import pandas as pd
from telebot.types import InputFile

from stats.settings import env
from statsapp.models import *
from statsapp.management.commands.bot import bot


# Список Конфигураций: POST http://151.248.118.19/Api/Configurations/GetList
# Список Папок с фото: POST http://151.248.118.19/Api/Stock/GetClients

# Прогон шаблона (4 запроса)
# POST http://151.248.118.19/Api/Stock/StartProcess
# POST http://151.248.118.19/Api/Stock/GetProcessStep
# POST http://151.248.118.19/Api/Stock/GetProcessResult
# POST http://151.248.118.19/Api/Log/GetByProcessId

def get_converter_tasks():
    active_tasks = ConverterTask.objects.filter(active=True)
    return active_tasks


def get_price(task):
    """
    Полный цикл для одного клиента.
    :param task: строка из таблицы Задачи конвертера
    """
    template = converter_template(task)
    client_slug = task.client.slug
    client_name = task.client.name
    process_id = converter_post(task)
    print(f'Клиент {client_slug}, pid: {process_id}')
    progress = converter_process_step(process_id)
    while progress < 100:
        print(progress)
        progress = converter_process_step(process_id)
    price = converter_process_result(process_id, client_slug)
    logs = converter_logs(process_id)
    logs_xlsx = logs_to_xlsx(logs, template, client_slug)
    bot_messages(logs, logs_xlsx, price, client_slug, client_name)
    save_on_ftp(logs_xlsx)
    os.remove(logs_xlsx)

    print(f'Клиент {client_slug} - прайс готов')
    return


def converter_template(task):
    # Сохраняю сток клиента, делаю по нему шаблон для конвертера
    slug = task.client.slug
    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')
    stock_path = f'converter/{slug}/stocks/stock_{slug}_{file_date}'

    # Получаю сток
    if task.stock_source == 'Ссылка':
        response = requests.get(url=task.stock_url)
    elif task.stock_source == 'POST-запрос':
        data = {
            'login': task.stock_post_login,
            'password': task.stock_post_password,
        }
        response = requests.post(url=task.stock_post_host, data=data)

    # Получаю тип файла стока
    content_type = response.headers['content-type']
    if 'text/xml' in content_type or 'application/xml' in content_type:
        stock_path += '.xml'
        content_type = 'xml'
    elif 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
        stock_path += '.xlsx'
        content_type = 'xlsx'

    # Сохраняю сток на ftp
    os.makedirs(os.path.dirname(stock_path), mode=0o755, exist_ok=True)
    with open(stock_path, mode='wb') as file:
        file.write(response.content)
    # with open(stock_path, mode='w', encoding=task.stock_fields.encoding) as file:
    #     file.write(response.text)
    save_on_ftp(stock_path)

    # Путь шаблона
    template_path = f'converter/{slug}/templates/template_{slug}_{file_date}.xlsx'
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    task.template = template_path
    task.save()

    # Разные функции в зависимости от типа файла стока
    if content_type == 'xml':
        template = template_xml(stock_path, template_path, task)
    elif content_type == 'xlsx':
        template = template_xlsx(stock_path, template_path, task)

    save_on_ftp(template_path)
    os.remove(stock_path)

    return template


def template_xml(stock_path, template_path, task):
    # XML tree
    tree = ET.parse(stock_path)
    root = tree.getroot()

    # XLSX шаблон
    xlsx_template = xlsxwriter.Workbook(template_path)
    sheet = xlsx_template.add_worksheet('Шаблон')

    # Заголовки шаблона
    template_col = StockFields.TEMPLATE_COL
    for k, col in template_col.items():
        sheet.write(0, col[1], col[0])

    # Данные шаблона
    fields = task.stock_fields
    exception_col = ['modification_code', 'options_code', 'images', 'modification_explained']
    for i, car in enumerate(root.iter(fields.car_tag)):
        # sheet.write(y, x, cell_data)  # Пример заполнения ячейки xlsx
        if stock_xml_filter(car, task):
            # Обычные поля
            for field in fields._meta.fields:
                field_val = getattr(fields, field.name)
                # Если не пусто И поле в полях шаблона И поле НЕ в исключениях
                if field_val and field.name in template_col and field.name not in exception_col:
                    cell = car.findtext(field_val)
                    try:
                        if cell.isnumeric():
                            cell = int(cell)
                    except AttributeError:
                        pass
                    sheet.write(i + 1, template_col[field.name][1], cell)

            # Поля-исключения
            if ',' in fields.modification_code:  # Код модификации
                # Разделяет по запятой в список если есть значение. Убирает запятую из данных стока
                mod = [car.findtext(f).replace(',', '') for f in fields.modification_code.split(', ') if car.findtext(f)]
                sheet.write(i + 1, template_col['modification_code'][1], ' | '.join(mod))
            else:
                sheet.write(i + 1, template_col['modification_code'][1], car.findtext(fields.modification_code))

            if fields.options_code:
                options = multi_tags(fields.options_code, car)  # Опции
                sheet.write(i + 1, template_col['options_code'][1], options)

            if fields.images:
                images = multi_tags(fields.images, car)  # Фото клиента
                sheet.write_string(i + 1, template_col['images'][1], images)

            if ',' in fields.modification_explained:  # Расш. модификации
                mod = [car.findtext(f) for f in fields.modification_explained.split(', ') if car.findtext(f)]
                sheet.write(i + 1, template_col['modification_explained'][1], ' | '.join(mod))
            else:
                sheet.write(i + 1, template_col['modification_explained'][1], car.findtext(fields.modification_explained))

    xlsx_template.close()

    return pd.read_excel(template_path, decimal=',')


# TODO настроить для нескольких значений в f.value. Потом для xlsx стоков
def stock_xml_filter(car, task):
    """
    Проверяет автомобиль из xml стока по фильтрам из ConverterFilters
    :param car: node автомобиля из xml стока
    :param task: task (запись) из таблицы Задачи конвертера
    :return: True если фильтры пройдены
    """
    filters = ConverterFilters.objects.filter(converter_task=task)
    dict_filters, stock_fields, result = [], [], []

    # Перевожу фильтры в словарь вида: {'values': values, 'condition': condition, 'field': field}
    for f in filters:
        # Значения
        if '`' in f.value:
            values = [val.replace('`', '').strip() for val in f.value.split('`,')]
        else:
            values = [f.value]

        # Поля (теги)
        if '/' in f.field:  # Путь к детям
            parent = f.field.split('/')[0]

            if '@' not in f.field:  # Дети
                stock_fields = [tag.text for tag in car.find(parent)]

            else:  # Атрибуты
                attribute_name = f.field.split('@')[1].split('=')[0]
                attribute_value = f.field.split('"')[1].replace('"', '')
                for tag in car.find(parent):
                    for tag_attribute in tag.attrib.items():
                        if tag_attribute == (attribute_name, attribute_value):
                            stock_fields = [tag.text]

        else:  # Просто один тег
            stock_fields = [car.findtext(f.field)]

        for field in stock_fields:
            dict_filters.append({
                'values': values,
                'condition': f.condition,
                'field': field,
            })

    for sf in dict_filters:
        for value in sf['values']:
            result.append(xml_filter_conditions(value, sf['condition'], sf['field']))

    # Если длина фильтров равна сумме результатов значит каждый фильтр вернул True, соответственно автомобиль подходит
    return len(dict_filters) == sum(result)


def xml_filter_conditions(value, condition, stock_field):
    """
    Условия фильтра
    :param value: значение для проверки
    :param condition: условие
    :param stock_field: значение из стока
    :return: True если условие выполнено
    """
    if 'with' not in condition:
        return eval(f'"{value}" {condition} "{stock_field}"')
    elif condition == ConverterFilters.STARTS_WITH:
        return stock_field.startswith(value)
    elif condition == ConverterFilters.NOT_STARTS_WITH:
        return not(stock_field.startswith(value))
    elif condition == ConverterFilters.ENDS_WITH:
        return stock_field.endswith(value)
    elif condition == ConverterFilters.NOT_ENDS_WITH:
        return not(stock_field.endswith(value))


def template_xlsx(stock_path, template_path, task):
    df_stock = pd.read_excel(stock_path, decimal=',')
    df_stock = stock_xlsx_filter(df_stock, task)

    fields = StockFields.objects.filter(pk=task.stock_fields.id)
    fields = fields.values()[0]
    template_col = StockFields.TEMPLATE_COL

    # Меняю имена столбцов
    swapped_cols = {v: template_col[k][0] for k, v in fields.items() if k in template_col}
    df_stock.rename(columns=swapped_cols, inplace=True)

    # Добавляю недостающие столбцы
    cur_cols = list(df_stock.columns.values)
    for k, col in template_col.items():
        if col[0] not in cur_cols:
            df_stock[col[0]] = ''

    # Оставляю только нужные столбцы в том порядке как в template_col
    df_stock = df_stock[[v[0] for k, v in template_col.items()]]
    # В Опции и пакеты заменяю переносы строк на пробел
    df_stock['Опции и пакеты'].replace(r'\n', ' ', regex=True, inplace=True)

    df_stock.T.reset_index().T.to_excel(template_path, sheet_name='Шаблон', header=False, index=False)

    return df_stock


def stock_xlsx_filter(df, task):
    """
    Проверяет автомобиль из xlsx стока по фильтрам из ConverterFilters
    :param df: xlsx сток в виде pandas dataframe
    :param task: task (запись) из таблицы Задачи конвертера
    :return: Отфильтрованный dataframe
    """
    filters = ConverterFilters.objects.filter(converter_task=task)
    filter_strings = []
    for f in filters:
        if '`' in f.value:
            values = [val.replace('`', '').strip() for val in f.value.split('`,')]
        else:
            values = [f.value]

        # TODO для условий с несколькими значениями нужно писать ИЛИ через |
        # Т.е. вместо df.loc[(df["VIN"].str.startswith("Z9M2130055L045585")) & (df["VIN"].str.startswith("Z9M2130055L046037")) & (df["Модель"] == "E (W/S213)")]
        # Писать df.loc[(df["VIN"].str.startswith("Z9M2130055L045585")) | (df["VIN"].str.startswith("Z9M2130055L046037")) & (df["Модель"] == "E (W/S213)")]
        for value in values:
            if f.condition == ConverterFilters.CONTAINS:
                filter_strings.append(f'(df["{f.field}"].str.contains({value})')
            elif f.condition == ConverterFilters.NOT_CONTAINS:
                filter_strings.append(f'(~df["{f.field}"].str.contains({value})')
            elif f.condition == ConverterFilters.EQUALS:
                filter_strings.append(f'(df["{f.field}"] == "{value}")')
            elif f.condition == ConverterFilters.NOT_EQUALS:
                filter_strings.append(f'(~df["{f.field}"] == "{value}")')
            elif f.condition == ConverterFilters.STARTS_WITH:
                filter_strings.append(f'(df["{f.field}"].str.startswith("{value}"))')
            elif f.condition == ConverterFilters.NOT_STARTS_WITH:
                filter_strings.append(f'~(df["{f.field}"].str.startswith("{value}"))')
            elif f.condition == ConverterFilters.ENDS_WITH:
                filter_strings.append(f'(df["{f.field}"].str.endswith("{value}")')
            elif f.condition == ConverterFilters.NOT_ENDS_WITH:
                filter_strings.append(f'~(df["{f.field}"].str.endswith("{value}")')
        print(f'df.loc[{" & ".join(filter_strings)}]')

    return eval(f'df.loc[{" & ".join(filter_strings)}]')


def multi_tags(field, element):
    """
    Обрабатывает поля для которых данные собираются из нескольких тегов
    :param field: поле
    :param element: элемент из xml
    :return: готовые данные для шаблона
    """
    if '/' in field:
        parent = field.split('/')[0]
        if '@' not in field:  # Если тег с детьми и нужно значение детей
            result = [tag.text for tag in element.find(parent)]
        else:  # Если тег с детьми и из детей нужен атрибут
            attribute = field.split('@')[1]
            result = [tag.attrib[attribute] for tag in element.find(parent)]
    else:
        if '@' not in field:  # Если тег несколько раз повторяется и нужно значение
            result = [tag.text for tag in element.findall(field)]
        else:  # Если тег несколько раз повторяется и из него нужен атрибут
            tag_name, attribute = field.split('@')
            result = [tag.attrib[attribute] for tag in element.findall(tag_name)]

    return ' '.join(result)


def converter_post(task):
    """
    Первый запрос к конвертеру. Отправляются опции и файл шаблона.
    :param task: task (запись) из таблицы Задачи конвертера
    :return: process_id для converter_process_step и converter_process_result
    """
    url = 'http://151.248.118.19/Api/Stock/StartProcess'

    configuration = task.configuration.configuration if task.configuration is not None else Configuration.DEFAULT
    payload = {
        'client': task.photos_folder.folder,
        'configuration': configuration,
        'frontLength': task.front,
        'backLength': task.back,
        'interiorsLength': task.interior,
        'onlySalon': task.salon_only,
    }
    template = open(task.template, 'rb')
    files = {'file': ('template.xlsx', template, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      {'Expires': '0'})}
    response = requests.post(url=url, data=payload, files=files)
    process_id = response.json()['processId']
    template.close()
    os.remove(task.template)
    return process_id


def converter_process_step(process_id):
    """
    Второй запрос, когда возвращает progress:100 значит прайс готов, можно вызывать converter_process_result
    :param process_id: из converter_post
    """
    url = 'http://151.248.118.19/Api/Stock/GetProcessStep'
    payload = {'processId': process_id}
    response = requests.post(url=url, json=payload)
    progress = response.json()['progress']
    return progress


def converter_process_result(process_id, client):
    """
    Третий запрос, возвращает готовый прайс
    :param process_id: из converter_post
    :param client: имя клиента как slug - используется как имя папки клиента куда сохраняется прайс
    """
    url = 'http://151.248.118.19/Api/Stock/GetProcessResult'
    payload = {'processId': (None, process_id)}
    response = requests.post(url=url, files=payload)
    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')
    save_path_date = f'converter/{client}/prices/price_{client}_{file_date}.xlsx'
    os.makedirs(os.path.dirname(save_path_date), exist_ok=True)
    with open(save_path_date, 'wb') as file:
        file.write(response.content)
    save_on_ftp(save_path_date)
    save_path = f'converter/{client}/prices/price_{client}.csv'
    read_file = pd.read_excel(save_path_date, decimal=',')
    # Убираю автомобили которые не расшифрованы (пустые столбцы Марка, Цвет либо Фото)
    read_file = read_file[(~read_file['Марка'].isnull()) &
                          (~read_file['Цвет'].isnull()) &
                          (~read_file['Фото'].isnull())]
    read_file.fillna('', inplace=True)
    read_file = read_file.astype(str).replace(r'\.0$', '', regex=True)
    read_file.to_csv(save_path, sep=';', header=True, encoding='cp1251', index=False, decimal=',')
    save_on_ftp(save_path)
    os.remove(save_path_date)
    os.remove(save_path)
    return read_file


def converter_logs(process_id):
    """
    Логи конвертера
    :param process_id: из converter_post
    """
    # Логи которые присылает конвертер
    url = 'http://151.248.118.19/Api/Log/GetByProcessId'
    payload = {'processId': process_id}
    response = requests.post(url=url, json=payload)
    logs = response.json()['log']
    return logs


def logs_to_xlsx(logs, template, client):
    """
    Логи конвертера вместе с расшифровкой в xlsx
    :param logs: логи от converter_logs
    :param template: шаблон от converter_template
    :param client: клиент как client_slug для имени папки и файла
    :return: xlsx файл логов
    """
    lookup_cols = {
        # База из лога: (Имя столбца с кодом, Имя столбца с расшифровкой)
        'Модификации': ('Код модификации', 'Расш. модификации'),
        'Цвета': ('Код цвета', 'Расш. цвета'),
        'Интерьеры': ('Код интерьера', 'Расш. интерьера'),
        'Комплектации': ('Код модификации', 'Расш. модификации'),
        # 'Опции': в логи идут только коды, без расшифровки
        # 'Фото': только количество без фото
    }

    # Переделываю логи в словарь
    lines = logs.split('\n')[:-1]
    logs_dict = {}
    for line in lines:
        key = line.split('"')[1]
        start = line.index(':') + 1
        end = line.index(';')
        value = []
        for v in line[start:end].split(','):
            v = v.strip()
            if v.isnumeric():
                v = int(v)
            value.append(v)

        if key in ['Опции', 'Фото']:  # Опции без расшифровки, Фото только количество
            logs_dict[key] = pd.Series(value, name=key)
        else:  # Остальные это pandas dataframe в виде Кода и Расшифровки
            df2 = pd.Series(value, name='Код', dtype='string')
            joined = pd.merge(template, df2, left_on=lookup_cols[key][0], right_on='Код')
            joined.drop_duplicates(subset=[lookup_cols[key][0]], inplace=True)
            joined = joined[[lookup_cols[key][0], lookup_cols[key][1]]]
            logs_dict[key] = joined

    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')
    logs_save_path = f'converter/{client}/logs/log_{client}_{file_date}.xlsx'
    os.makedirs(os.path.dirname(logs_save_path), exist_ok=True)

    # Готовые логи в xlsx
    with pd.ExcelWriter(logs_save_path) as writer:
        for key, value in logs_dict.items():
            df = pd.DataFrame(value)
            # Такой длинный вариант чтобы убрать форматирование заголовков которое pandas применяет по умолчанию
            df.T.reset_index().T.to_excel(writer, sheet_name=key, header=False, index=False)
    return logs_save_path


def bot_messages(logs, logs_xlsx, price, client_slug, client_name):
    """
    Сообщения для телеграм бота
    :param logs: логи от converter_logs
    :param logs_xlsx: логи в xlsx от logs_to_xlsx
    :param price: прайс от converter_process_result
    :param client_slug: клиент как client_slug для имени папки и файла
    :param client_name: клиент как client_name для сообщения бота
    """
    # Прайс в csv
    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')
    price_save_path = f'converter/{client_slug}/prices/price_{client_slug}_{file_date}.csv'
    price.to_csv(price_save_path, sep=';', header=True, encoding='cp1251', index=False, decimal=',')

    # Отправка логов и прайса через бота телеграма
    chat_ids = ConverterLogsBotData.objects.all()
    for chat_id in chat_ids:
        if len(logs) > 4095:  # У телеграма ограничение на 4096 символов в сообщении
            for x in range(0, len(logs), 4095):
                bot.send_message(chat_id.chat_id, logs[x:x + 4095])
        else:
            bot.send_message(chat_id.chat_id, f'🔵 {client_name}\n\n{logs}')
        bot.send_document(chat_id.chat_id, InputFile(logs_xlsx))
        bot.send_document(chat_id.chat_id, InputFile(price_save_path))

    os.remove(price_save_path)
    return


def save_on_ftp(save_path):
    """
    Сохраняет файл на ftp
    :param save_path: полный путь к файлу
    """
    file_path = Path(save_path)
    with FTP('ph.onllline.ru', env('FTP_LOGIN'), env('FTP_PASSWORD')) as ftp, open(save_path, 'rb') as file:
        cd_tree(ftp, str(file_path.parents[0]))
        ftp.storbinary(f'STOR {file_path.name}', file)
        ftp.cwd('/')
    return


def cd_tree(ftp, path):
    """
    Создаёт папки на ftp если они не существуют
    :param ftp: FTP класс из ftplib
    :param path: путь который нужен на ftp
    """
    path = path.replace('\\', '/')  # Костыль для windows
    for folder in path.split('/'):
        try:
            ftp.cwd(folder)
        except ftplib.error_perm:
            ftp.mkd(folder)
            ftp.cwd(folder)


def get_photo_folders():
    """ Получает от конвертера список папок с фото и добавляет новые в базу """
    url = 'http://151.248.118.19/Api/Stock/GetClients'
    response = requests.post(url).json()
    current_folders = [f.folder for f in PhotoFolder.objects.all()]
    new_folders = []
    for folder in response:
        if folder not in current_folders:
            new_folders.append(PhotoFolder(folder=folder))
    PhotoFolder.objects.bulk_create(new_folders)


def get_configurations():
    """ Получает от конвертера конфигурации и добавляет/обновляет в базе """
    url = 'http://151.248.118.19/Api/Configurations/GetList'
    response = requests.post(url).json()
    current_configurations = Configuration.objects.all()
    new_configurations = []
    updated_configurations = []
    for conf in response:
        exists = current_configurations.filter(converter_id=conf['id'])
        if exists.count() > 0:
            updated = exists[0]
            updated.name = conf['name']
            updated.configuration = conf['configuration']
            updated_configurations.append(updated)
        else:
            new_configurations.append(Configuration(converter_id=conf['id'], name=conf['name'],
                                                    configuration=conf['configuration']))
    Configuration.objects.bulk_update(updated_configurations, ['name', 'configuration'])
    if len(new_configurations):
        Configuration.objects.bulk_create(new_configurations)
