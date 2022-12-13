import os
import requests
import logging
import http.client as http_client
import datetime
import xml.etree.ElementTree as ET
import xlsxwriter


from statsapp.models import *

# Список конфигураций: POST http://151.248.118.19/Api/Configurations/GetList
# Список Папок с фото: POST http://151.248.118.19/Api/Stock/GetClients

# Прогон шаблона (3 запроса)
# POST http://151.248.118.19/Api/Stock/StartProcess
# POST http://151.248.118.19/Api/Stock/GetProcessStep
# POST http://151.248.118.19/Api/Stock/GetProcessResult


def get_converter_tasks():
    active_tasks = ConverterTask.objects.filter(active=True)
    return active_tasks


def converter_template(task):
    # Сохраняю xml сток клиента, делаю по нему шаблон для конвертера
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
    tree = ET.parse(stock_path)
    root = tree.getroot()

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


def converter_post(task):
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

    response = requests.post(url=url, json=payload, files=files)
    process_id = response.json()['processId']
    template.close()
    return process_id


def converter_process_step(process_id):
    url = 'http://151.248.118.19/Api/Stock/GetProcessStep'
    payload = {'processId': process_id}
    response = requests.post(url=url, json=payload)
    progress = response.json()['progress']
    return progress


def converter_process_result(process_id, client):
    url = 'http://151.248.118.19/Api/Stock/GetProcessResult'
    payload = {'processId': (None, process_id)}
    response = requests.post(url=url, files=payload)
    file_date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')
    save_path = f'converter/{client}/prices/price_{client}_{file_date}.xlsx'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as file:
        file.write(response.content)
    return


def get_photo_folders():
    # Получает от конвертера список папок с фото и добавляет новые в базу
    url = 'http://151.248.118.19/Api/Stock/GetClients'
    response = requests.post(url).json()
    current_folders = [f.folder for f in PhotoFolder.objects.all()]
    new_folders = []
    for folder in response:
        if folder not in current_folders:
            new_folders.append(PhotoFolder(folder=folder))
    PhotoFolder.objects.bulk_create(new_folders)


def get_configurations():
    # Получает от конвертера конфигурации и добавляет/обновляет в базе
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

