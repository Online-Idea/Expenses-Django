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
    converter_template(task)
    client = task.client.slug
    process_id = converter_post(task)
    print(f'Клиент {client}, pid: {process_id}')
    progress = converter_process_step(process_id)
    while progress < 100:
        print(progress)
        progress = converter_process_step(process_id)
    converter_process_result(process_id, client)
    converter_logs(task, process_id)
    print(f'Клиент {client} - прайс готов')
    return


def converter_template(task):
    # Сохраняю xml сток клиента, делаю по нему шаблон для конвертера
    # TODO этот вариант для РОЛЬФ, сделать универсальный либо под клиента
    xlsx_headers = ['Код модификации', 'Код комплектации', 'Код цвета', 'Код интерьера', 'Опции и пакеты', 'Цена',
                    'Цена по акции 1', 'Цена по акции 2', 'Год', 'Исходный VIN', 'ID от клиента', 'Трейд-ин', 'Кредит',
                    'Страховка', 'Максималка']

    slug = task.client.slug
    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')

    # XML root
    url = task.stock
    response = requests.get(url).text
    stock_path = f'converter/{slug}/stocks/stock_{slug}_{file_date}.xml'
    os.makedirs(os.path.dirname(stock_path), exist_ok=True)
    with open(stock_path, mode='w', encoding='ISO-8859-1') as file:
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

    # TODO отделить в функцию которая использует данные из StockFields
    # Данные шаблона
    for i, car in enumerate(root.iter('car')):
        # sheet.write(y, x, cell_data)  # Пример заполнения ячейки xlsx
        sheet.write(i + 1, 0, f"{car.findtext('folder_id')} | {car.findtext('modification_id')} | "
                              f"{car.findtext('complectation')}")  # Код модификации
        sheet.write(i + 1, 2, car.findtext('color'))  # Код цвета
        sheet.write(i + 1, 5, int(car.findtext('price')))  # Цена
        sheet.write(i + 1, 8, int(car.findtext('year')))  # Год
        sheet.write(i + 1, 9, car.findtext('vin'))  # Исходный VIN
        sheet.write(i + 1, 10, int(car.findtext('idveh')))  # ID от клиента
        sheet.write(i + 1, 11, int(car.findtext('tradein_discount')))  # Трейд-ин
        sheet.write(i + 1, 12, int(car.findtext('credit_discount')))  # Кредит
        sheet.write(i + 1, 13, int(car.findtext('insurance_discount')))  # Страховка
        sheet.write(i + 1, 14, int(car.findtext('max_discount')))  # Максималка

    xlsx_template.close()
    save_on_ftp(template_path)


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


def converter_logs(task, process_id):
    """
    Логи конвертера
    :param task: task (запись) из таблицы Задачи конвертера
    :param process_id: из converter_post
    """
    url = 'http://151.248.118.19/Api/Log/GetByProcessId'
    payload = {'processId': process_id}
    response = requests.post(url=url, json=payload)
    logs = response.json()['log']
    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')
    save_path = f'converter/{task.client.slug}/logs/log_{task.client.slug}_{file_date}.txt'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, mode='w', encoding='utf8') as file:
        file.write(logs)
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
