import ftplib
from ftplib import FTP
from pathlib import Path
import os
import requests
import datetime
import xml.etree.ElementTree as ET
import xlsxwriter
import pandas as pd

from stats.settings import env
from statsapp.models import *


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
    client = task.client.slug
    process_id = converter_post(task)
    print(f'Клиент {client}, pid: {process_id}')
    progress = converter_process_step(process_id)
    while progress < 100:
        print(progress)
        progress = converter_process_step(process_id)
    converter_process_result(process_id, client)
    converter_logs(task, process_id, template)
    print(f'Клиент {client} - прайс готов')
    return


def converter_template(task):
    # Сохраняю xml сток клиента, делаю по нему шаблон для конвертера
    xlsx_headers = ['Код модификации', 'Код комплектации', 'Код цвета', 'Код интерьера', 'Опции и пакеты', 'Цена',
                    'Цена по акции 1', 'Цена по акции 2', 'Год', 'Исходный VIN', 'ID от клиента', 'Трейд-ин', 'Кредит',
                    'Страховка', 'Максималка', 'Фото клиента', 'Расш. модификации', 'Расш. цвета', 'Расш. интерьера']

    slug = task.client.slug
    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')

    # XML root
    if task.stock_source == 'Ссылка':
        response = requests.get(url=task.stock_url).text
    elif task.stock_source == 'POST-запрос':
        data = {
            'login': task.stock_post_login,
            'password': task.stock_post_password,
        }
        response = requests.post(url=task.stock_post_host, data=data).text

    stock_path = f'converter/{slug}/stocks/stock_{slug}_{file_date}.xml'
    os.makedirs(os.path.dirname(stock_path), exist_ok=True)
    with open(stock_path, mode='w', encoding=task.stock_fields.encoding) as file:
        file.write(response)
    save_on_ftp(stock_path)
    tree = ET.parse(stock_path)
    root = tree.getroot()
    os.remove(stock_path)

    # XLSX шаблон
    template_path = f'converter/{slug}/templates/template_{slug}_{file_date}.xlsx'
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    task.template = template_path
    task.save()
    xlsx_template = xlsxwriter.Workbook(template_path)
    sheet = xlsx_template.add_worksheet('Шаблон')
    # Заголовки шаблона
    for i, header in enumerate(xlsx_headers):
        sheet.write(0, i, header)

    # Данные шаблона
    fields = task.stock_fields
    template_col = StockFields.TEMPLATE_COL
    exception_col = ['modification_code', 'options_code', 'images', 'modification_explained']
    for i, car in enumerate(root.iter(fields.car_tag)):
        # sheet.write(y, x, cell_data)  # Пример заполнения ячейки xlsx
        # Обычные поля
        for field in fields._meta.fields:
            field_val = getattr(fields, field.name)
            # Если не пусто И поле в полях шаблона И поле НЕ в исключениях
            if field_val and field.name in template_col and field.name not in exception_col:
                cell = car.findtext(field_val)
                if cell.isnumeric():
                    cell = int(cell)
                sheet.write(i + 1, template_col[field.name], cell)

        # Поля-исключения
        if ',' in fields.modification_code:  # Код модификации
            # Разделяет по запятой в список если есть значение. Убирает запятую из данных стока
            mod = [car.findtext(f).replace(',', '') for f in fields.modification_code.split(', ') if car.findtext(f)]
            sheet.write(i + 1, template_col['modification_code'], ' | '.join(mod))
        else:
            sheet.write(i + 1, template_col['modification_code'], car.findtext(fields.modification_code))

        if fields.options_code:
            options = multi_tags(fields.options_code, car)  # Опции
            sheet.write(i + 1, template_col['options_code'], options)

        if fields.images:
            images = multi_tags(fields.images, car)  # Фото клиента
            sheet.write(i + 1, template_col['images'], images)

        if ',' in fields.modification_explained:  # Расш. модификации
            mod = [car.findtext(f) for f in fields.modification_explained.split(', ') if car.findtext(f)]
            sheet.write(i + 1, template_col['modification_explained'], ' | '.join(mod))
        else:
            sheet.write(i + 1, template_col['modification_explained'], car.findtext(fields.modification_explained))

    xlsx_template.close()
    save_on_ftp(template_path)
    return pd.read_excel(template_path)


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

    configuration = task.configuration if task.configuration is not None else Configuration.DEFAULT
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
    read_file = pd.read_excel(save_path_date)
    # Убираю автомобили которые не расшифрованы (пустые столбцы Марка, Цвет либо Фото)
    read_file = read_file[(~read_file['Марка'].isnull()) &
                          (~read_file['Цвет'].isnull()) &
                          (~read_file['Фото'].isnull())]
    read_file.to_csv(save_path, sep=';', header=True, encoding='cp1251', index=False)
    save_on_ftp(save_path)
    os.remove(save_path_date)
    os.remove(save_path)
    return


def converter_logs(task, process_id, template):
    """
    Логи конвертера
    :param task: task (запись) из таблицы Задачи конвертера
    :param process_id: из converter_post
    :param template: шаблон как pandas dataframe из converter_template
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

    url = 'http://151.248.118.19/Api/Log/GetByProcessId'
    payload = {'processId': process_id}
    response = requests.post(url=url, json=payload)
    logs = response.json()['log']
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

        if key in ['Опции', 'Фото']:
            logs_dict[key] = pd.Series(value, name=key)
        else:
            df2 = pd.Series(value, name='Код')
            joined = pd.merge(template, df2, left_on=lookup_cols[key][0], right_on='Код')
            joined.drop_duplicates(subset=[lookup_cols[key][0]], inplace=True)
            joined = joined[[lookup_cols[key][0], lookup_cols[key][1]]]
            logs_dict[key] = joined

    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')
    save_path = f'converter/{task.client.slug}/logs/log_{task.client.slug}_{file_date}.xlsx'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with pd.ExcelWriter(save_path) as writer:
        for key, value in logs_dict.items():
            df = pd.DataFrame(value)
            # Такой длинный вариант чтобы убрать форматирование заголовков которое pandas применяет по умолчанию
            df.T.reset_index().T.to_excel(writer, sheet_name=key, header=False, index=False)

    save_on_ftp(save_path)
    os.remove(save_path)
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
    for folder in path.split('\\'):
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
