# import re
# from time import time
# from datetime import datetime
# from typing import List, Union, Dict
#
# from django.core.management.base import BaseCommand
# from lxml import etree
# from django.db import transaction
# from lxml.etree import Element
# from requests import Response
# from libs.autoru.models import *
# from utils.clear_space import clear_space
# import requests
# from stats.settings import env
# from pprint import pprint
#
# CYAN = '\033[96m'  # ANSI код для белого цвета текста
# GREEN = '\033[92m'
# WHITE = '\033[97m'
# RED = '\033[91m'
# YELLOW = '\033[93m'
# BLUE = '\033[94m'
# MAGENTA = '\033[95m'
# RESET = '\033[0m'  # ANSI код для сброса цвета текста
#
# SLASH_CYAN = CYAN + ' | ' + RESET
#
#
# # Функция для обработки типа двигателя
# def process_engine_type(engine_type):
#     match engine_type:
#         case 'd':
#             return 'Дизель'
#         case 'hyb':
#             return 'Гибрид'
#         case _:
#             return 'Бензин'
#
#
# def process_name(name):
#     if 'hyb' in name:
#         return name.replace('hyb', ' Hybrid')
#     return name
#
#
# def process_drive(drive):
#     match drive:
#         case 'Полный':
#             return '4WD'
#         case _:
#             return 'FWD | RWD'
#
#
# def process_transmission(transmission):
#     match transmission:
#         case 'AT':
#             return 'Автомат'
#         case 'MT':
#             return 'Механика'
#         case 'AMT':
#             return 'Робот'
#         case 'CVT':
#             return 'Вариатор'
#
#
# def extract_modification_info(modification: str) -> Dict[str, Union[str, int, float]]:
#     """
#     Извлекает информацию о модификации автомобиля из строки.
#
#     :param modification: Строка с описанием модификации.
#     :return: Словарь с информацией о модификации.
#     """
#     # Паттерн для обработки электромобилей
#     regex_pattern_electro = re.compile(
#         r'(?:[A-Z0-9]+\s+)*'
#         r'(?:'
#         r'(?P<battery>(\d+(\.\d+)?)\s*kWh|(\d+(\.\d+)?)kWh|\(\d+\s*kWh\))\s+'
#         r')?'
#         r'(?:[A-Z0-9]+\s+)*'
#         r'Electro\s+'
#         r'(?P<transmission>[A-Z]+)\s+\('
#         r'(?P<power>\d+)\s+кВт\)\s*'
#         r'(?P<drive>\w+)?'
#     )
#
#     # Паттерн для обработки обычных автомобилей
#     regex_pattern_normal = re.compile(
#         r'(?:(?P<engine_volume>[\d.]+)'
#         r'(?P<engine_type>[a-z]*)\s+)?(?:[A-Z0-9]+\s+)*'
#         r'(?P<transmission>[A-Z]+)\s+\('
#         r'(?P<power>\d+)\s+л\.с\.\)(?:\s+'
#         r'(?P<drive>\w+))?'
#     )
#     result = {}
#     if 'Electro' in modification:
#         result['engine_type'] = 'Электро'
#         match = re.search(regex_pattern_electro, modification)
#         if match:
#             battery_match = match.group('battery')
#             if battery_match:
#                 result['battery_capacity'] = float(re.search(r'\d+(\.\d+)?', battery_match).group())
#             else:
#                 result['battery_capacity'] = None
#
#     else:
#         match = re.search(regex_pattern_normal, modification)
#         if match:
#             result['engine_type'] = process_engine_type(match.group('engine_type'))
#             result['engine_volume'] = float(match.group('engine_volume'))
#
#     result['transmission'] = process_transmission(match.group('transmission'))
#     result['power'] = int(match.group('power'))
#     result['drive'] = 'Полный' if match.group('drive') else 'Передний | Задний'
#
#     return result
#
#
# def process_body_type(body_type):
#     body_type_list = body_type.split(' ')
#     if body_type_list[-1] == 'дв.':
#         return {
#             'doors': body_type_list[-2],
#             'body_type': body_type_list[0],
#         }
#     return {
#         'doors': 4,
#         'body_type': body_type,
#     }
#
#
# def procces_year(years: str) -> Dict[str, int]:
#     """
#     Обрабатывает строку с годами производства и возвращает их в виде словаря.
#
#     :param years: Строка с диапазоном лет (например, "2005-2010").
#     :return: Словарь с начальным и конечным годом производства.
#     """
#     now = datetime.now()
#     result = {
#         'years_from': (years.split('-'))[0].strip(),
#         'years_to': (years.split('-'))[1].strip()
#     }
#     result['years_from'] = int(result['years_from'])
#     try:
#         result['years_to'] = int(result['years_to'])
#     except ValueError as e:
#         result['years_to'] = now.year
#
#     return result
#
#
# def procces_folder(**kwargs) -> dict[str, AutoruModel | str]:
#     """
#     Обработка данных модели перед сохранением.
#
#     :param kwargs: Именованные аргументы с данными тега <folder>.
#     :return: Созданный экземпляр AutoruModel.
#     """
#     try:
#         if kwargs['name'].find(',') != -1:
#             try:
#                 kwargs['name'], generation = kwargs['name'].split(',', 1)
#             except ValueError as e:
#                 print(kwargs['name'], e)
#         else:
#             generation = 'take_years'
#
#         return {
#             'model_instance': AutoruModel(**kwargs),
#             'generation': clear_space(generation)
#         }
#     except KeyError as e:
#         print('Ошибка ключа: ', e)
#
#
# def procces_modification(**kwargs) -> AutoruModification:
#     """
#     Обрабатывает данные модификации перед сохранением.
#
#     :param kwargs: Именованные аргументы с данными модификации.
#     :return: Созданный экземпляр AutoruModification.
#     """
#     # kwargs['name'] = process_name(kwargs['name'])
#     modification_dict = extract_modification_info(kwargs['name'])
#     if modification_dict['engine_type'] == 'Электро':
#         kwargs['engine_volume'] = 0
#     else:
#         kwargs['battery_capacity'] = None
#     years_dict = procces_year(kwargs['years'])
#     if kwargs['generation'].name == 'take_years':
#         kwargs['generation'].name = kwargs['years']
#     del kwargs['years']
#     try:
#         modification_dict['engine_volume']
#     except KeyError as e:
#         modification_dict['engine_volume'] = 0
#     transmission_mapping = {
#         'Автомат': 'AT',
#         'Робот': 'RWD',
#         'Вариатор': 'CVT',
#         'Механика': 'MT'
#     }
#     transmission = transmission_mapping[modification_dict['transmission']]
#     kwargs['short_name'] = (f'{modification_dict['engine_volume']} {modification_dict['power']} л.с. '
#                             f'{process_drive(modification_dict['drive'])} {modification_dict['engine_type']} '
#                             f'{transmission}')
#     kwargs['clients_name'] = process_name(kwargs['name'])
#     kwargs['name'] = process_name(kwargs['name'])
#     body_type_dict = process_body_type(kwargs['body_type'])
#
#     kwargs = kwargs | modification_dict | years_dict | body_type_dict
#     return AutoruModification(**kwargs)
#
#
# class Command(BaseCommand):
#     """
#     Команда Django для импорта данных из XML-файла в базу данных.
#     """
#
#     help = 'Импорт данных из XML-файла'
#
#     autoru_models = [
#         AutoruMark,
#         AutoruModel,
#         AutoruGeneration,
#         AutoruModification,
#         AutoruComplectation,
#     ]
#
#     create_instance = {
#         'marks': [],
#         'models': [],
#         'generations': [],
#         'modifications': [],
#         'complectations': [],
#     }
#
#     def handle(self, *args, **kwargs) -> None:
#         """
#         Обработка выполнения команды.
#
#         :param args: Не используется.
#         :param kwargs: Аргументы командной строки (не используется).
#         """
#         xml_link = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
#         response: Response = requests.get(xml_link)
#         xml_file: bytes = response.content
#         # удаление старых данных перед парсингом
#         self.clear_database()
#         # Обработка XML-файла
#         self.process_xml_file(xml_file)
#         # Вставка новых данных в базу данных
#         self.insert_data()
#
#         self.stdout.write(self.style.SUCCESS("Обновление Авто.ру успешно!"))
#
#     def clear_database(self) -> None:
#         """
#         Очистка всех записей из каждой таблицы в базе данных.
#         """
#         general_start = time()
#         self.stdout.write(CYAN + f' {"Имя таблицы":<25} | {"Кол-во записей":<18} | {"Время удаления":<15}' + RESET)
#         for model in reversed(self.autoru_models):
#             start = time()  # Время начала удаления записей из текущей модели
#             entries = model.objects.all()
#             amount_entries = len(entries)
#             entries.delete()  # Удаление записей
#             duration = f'{round(time() - start, 2)} сек'  # Время удаления записей из текущей модели
#             # Вывод информации о количестве удаленных записей с окраской
#             self.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
#             self.stdout.write(
#                 GREEN + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
#                 GREEN + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
#                 GREEN + f'{duration:<15}' + RESET)
#
#             # Вывод общего времени удаления всех записей
#         self.stdout.write(self.style.WARNING(f'\nОбщее время очистки: {round(time() - general_start, 2)} сек \n'))
#
#     def insert_data(self):
#         """
#         Вставка новых данных в таблицы базы данных.
#         """
#         with transaction.atomic():
#             general_start = time()
#             self.stdout.write(CYAN + f' {"Имя таблицы":<25} | {"Кол-во записей":<18} | {"Время вставки":<15}' + RESET)
#             for model, list_objects in zip(self.autoru_models, self.create_instance.values()):
#                 start = time()  # Время начала удаления записей из текущей модели
#                 entries = model.objects.bulk_create(list_objects)
#                 amount_entries = len(entries)
#                 duration = f'{round(time() - start, 2)} сек'  # Время удаления записей из текущей модели
#                 # Вывод информации о количестве удаленных записей с окраской
#                 self.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
#                 self.stdout.write(
#                     GREEN + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
#                     GREEN + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
#                     GREEN + f'{duration:<15}' + RESET)
#
#                 # Вывод общего времени удаления всех записей
#             self.stdout.write(self.style.WARNING(f'\nОбщее время вставки: {round(time() - general_start, 2)} сек \n'))
#
#     def process_xml_file(self, xml_file: bytes) -> None:
#         """
#         Чтение и обработка XML-файла.
#         Создаёт экземпляры даных и сохраняет в списки
#
#         :param xml_file: Содержимое XML-файла.
#         """
#         root: Element = etree.fromstring(xml_file)
#
#         for mark_el in root.iterfind('./mark'):
#             mark_instance = AutoruMark(
#                 code_mark_autoru=mark_el.find('code').text,
#                 id_mark_autoru=mark_el.get('id'),
#                 name=mark_el.get('name'),
#             )
#             self.create_instance['marks'].append(mark_instance)
#
#             for model_el in mark_el.iterfind('./folder'):
#                 result = procces_folder(
#                     id_folder_autoru=model_el.get('id'),
#                     mark=mark_instance,
#                     name=model_el.get('name'),
#                 )
#                 model_instance = result['model_instance']
#                 generation_name = result['generation']
#                 self.create_instance['models'].append(model_instance)
#                 generation_instance = AutoruGeneration(
#                     id_generation_autoru=model_el.get('id'),
#                     model=model_instance,
#                     name=generation_name,
#                 )
#
#                 self.create_instance['generations'].append(generation_instance)
#                 for modification_el in model_el.iterfind('./modification'):
#                     modification_instance = procces_modification(
#                         id_modification_autoru=modification_el.get('id'),
#                         name=modification_el.get('name'),
#                         mark=mark_instance,
#                         model=model_instance,
#                         generation=generation_instance,
#                         tech_param_id=modification_el.find('tech_param_id').text,
#                         years=modification_el.find('years').text,
#                         body_type=modification_el.find('body_type').text,
#                     )
#
#                     self.create_instance['modifications'].append(modification_instance)
#
#                     for complectation_el in modification_el.iterfind('./complectations/complectation'):
#                         complectation_instance = AutoruComplectation(
#                             id_complectation_autoru=complectation_el.get('id'),
#                             modification=modification_instance,
#                             name=complectation_el.get('name')
#                         )
#                         self.create_instance['complectations'].append(complectation_instance)

import re
from time import time, sleep
from datetime import datetime
from typing import List, Union, Dict

from django.core.management.base import BaseCommand
from lxml import etree
from django.db import transaction
from lxml.etree import Element
from requests import Response
from libs.autoru.models import *
from utils.clear_space import clear_space
import requests
from stats.settings import env
from pprint import pprint

CYAN = '\033[96m'  # ANSI код для белого цвета текста
GREEN = '\033[92m'
WHITE = '\033[97m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'  # ANSI код для сброса цвета текста

SLASH_CYAN = CYAN + ' | ' + RESET

API_KEY = {
    'x-authorization': env('AUTORU_API_KEY'),
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
login = env('AUTORU_LOGIN')
password = env('AUTORU_PASSWORD')

from utils.colored_logger import ColoredLogger

ENDPOINT = 'https://apiauto.ru/1.0'

logger = ColoredLogger(__name__)


def autoru_errors(data):
    try:
        error = data['error']
    except KeyError:
        return False
    else:
        if error == 'TOO_MANY_REQUESTS':
            print('Достигнут лимит авто.ру, жду минуту')
            time.sleep(60)
            return True
        elif error == 'NO_AUTH':
            print('Слетела авторизация, захожу повторно')
            global session_id
            session_id = autoru_authenticate(login, password)
            return True


def get_autoru_catalog_structure(param, session_id):
    url = 'https://apiauto.ru/1.0/search/cars/breadcrumbs'
    dealer_headers = {**API_KEY, **session_id}
    params = {
        'bc_lookup': param,
    }
    try:
        response = requests.get(url, headers=dealer_headers, params=params, timeout=10)
        response.raise_for_status()  # Это вызовет HTTPError для ошибок HTTP
        logger.green("Request successful.")
        return response.json()
    except requests.exceptions.ConnectTimeout as e:
        logger.error(f"Connection timeout: {e}")
    except requests.RequestException as e:
        if hasattr(e, 'response'):
            if e.response.status_code == 400:  # Код 400 Bad Request
                logger.error("Bad request error: %s", e.response.text)
            elif e.response.status_code == 401:  # Код 401 Unauthorized
                logger.error("Authentication error: %s", e.response.json().get('detailed_error'))
                return 'NO_AUTH'
            else:
                logger.error(f"Request failed: {e.response.text}")
        else:
            logger.error(f"Request failed: {e}")
        return None


def autoru_authenticate(login, password):
    # Аутентификация пользователя
    # https://yandex.ru/dev/autoru/doc/reference/auth-login.html
    # POST /auth/login
    auth = '/auth/login'
    login_pass = {
        'login': login,
        'password': password
    }
    try:
        auth_response = requests.post(url=f'{ENDPOINT}{auth}', headers=API_KEY, json=login_pass)
        auth_response.raise_for_status()  # Проверка успешности запроса
        session_id = {'x-session-id': auth_response.json()['session']['id']}
        return session_id
    except requests.RequestException as e:
        logger.error(f"Authentication failed: {e}")
        raise


# Функция для обработки типа двигателя
def process_engine_type(engine_type):
    match engine_type:
        case 'd':
            return 'Дизель'
        case 'hyb':
            return 'Гибрид'
        case _:
            return 'Бензин'


def process_name(name):
    if 'hyb' in name:
        return name.replace('hyb', ' Hybrid')
    return name


drive_mapping = {
    'ALL_WHEEL_DRIVE': 'Полный',
    'FORWARD_CONTROL': 'Передний',
    'REAR_DRIVE': 'Задний'

}


def process_drive(drive):
    match drive:
        case 'Полный':
            return '4WD'
        case 'Задний':
            return 'RWD'
        case 'Передний':
            return 'FWD'


def process_transmission(transmission):
    match transmission:
        case 'AT':
            return 'Автомат'
        case 'MT':
            return 'Механика'
        case 'AMT':
            return 'Робот'
        case 'CVT':
            return 'Вариатор'


def extract_modification_info(modification: str) -> Dict[str, Union[str, int, float]]:
    """
    Извлекает информацию о модификации автомобиля из строки.

    :param modification: Строка с описанием модификации.
    :return: Словарь с информацией о модификации.
    """
    # Паттерн для обработки электромобилей
    regex_pattern_electro = re.compile(
        r'(?:(?P<battery>\d+\s+)kWh\s+)?'
        r'(?:[A-Z0-9]+\s+)*'
        r'(?:(?:[A-Z0-9]+\s+)?Electro\s+)?'
        r'(?P<transmission>[A-Z]+)\s+'
        r'?\('
        r'(?P<power>\d+)\s+кВт\)(?:\s+'
        r'(?P<drive>\w+))?'
    )

    # Паттерн для обработки обычных автомобилей
    regex_pattern_normal = re.compile(
        r'(?:(?P<engine_volume>[\d.]+)'
        r'(?P<engine_type>[a-z]*)\s+)?(?:[A-Z0-9]+\s+)*'
        r'(?P<transmission>[A-Z]+)\s+\('
        r'(?P<power>\d+)\s+л\.с\.\)(?:\s+'
        r'(?P<drive>\w+))?'
    )
    result = {}
    if 'Electro' in modification:
        match = re.search(regex_pattern_electro, modification)
        if match:
            result['engine_type'] = 'Электро'
            result['battery_capacity'] = int(match.group('battery')) if match.group('battery') else None

    else:
        match = re.search(regex_pattern_normal, modification)
        if match:
            result['engine_type'] = process_engine_type(match.group('engine_type'))
            result['engine_volume'] = float(match.group('engine_volume'))

    result['transmission'] = process_transmission(match.group('transmission'))
    result['power'] = int(match.group('power'))

    return result


def process_body_type(body_type):
    body_type_list = body_type.split(' ')
    if body_type_list[-1] == 'дв.':
        return {
            'doors': body_type_list[-2],
            'body_type': body_type_list[0],
        }
    return {
        'doors': 4,
        'body_type': body_type,
    }


def procces_year(years: str) -> Dict[str, int]:
    """
    Обрабатывает строку с годами производства и возвращает их в виде словаря.

    :param years: Строка с диапазоном лет (например, "2005-2010").
    :return: Словарь с начальным и конечным годом производства.
    """
    now = datetime.now()
    result = {
        'years_from': (years.split('-'))[0].strip(),
        'years_to': (years.split('-'))[1].strip()
    }
    result['years_from'] = int(result['years_from'])
    try:
        result['years_to'] = int(result['years_to'])
    except ValueError as e:
        result['years_to'] = now.year

    return result


def procces_folder(**kwargs) -> dict[str, AutoruModel | str]:
    """
    Обработка данных модели перед сохранением.

    :param kwargs: Именованные аргументы с данными тега <folder>.
    :return: Созданный экземпляр AutoruModel.
    """
    try:
        if kwargs['name'].find(',') != -1:
            try:
                kwargs['name'], generation = kwargs['name'].split(',', 1)
            except ValueError as e:
                print(kwargs['name'], e)
        else:
            generation = 'take_years'

        return {
            'model_instance': AutoruModel(**kwargs),
            'generation': clear_space(generation)
        }
    except KeyError as e:
        print('Ошибка ключа: ', e)


def procces_modification(**kwargs) -> AutoruModification:
    """
    Обрабатывает данные модификации перед сохранением.

    :param kwargs: Именованные аргументы с данными модификации.
    :return: Созданный экземпляр AutoruModification.
    """

    # kwargs['name'] = process_name(kwargs['name'])
    modification_dict = extract_modification_info(kwargs['name'])
    if modification_dict['engine_type'] == 'Электро':
        kwargs['engine_volume'] = 0
    years_dict = procces_year(kwargs['years'])
    if kwargs['generation'].name == 'take_years':
        kwargs['generation'].name = kwargs['years']
    del kwargs['years']
    try:
        modification_dict['engine_volume']
    except KeyError as e:
        modification_dict['engine_volume'] = 0
    transmission_mapping = {
        'Автомат': 'AT',
        'Робот': 'RWD',
        'Вариатор': 'CVT',
        'Механика': 'MT'
    }
    transmission = transmission_mapping[modification_dict['transmission']]
    kwargs['short_name'] = (f'{modification_dict['engine_volume']} {modification_dict['power']} л.с. '
                            f'{process_drive(kwargs['drive'])} {modification_dict['engine_type']} '
                            f'{transmission}')
    kwargs['clients_name'] = process_name(kwargs['name'])
    kwargs['name'] = process_name(kwargs['name'])
    body_type_dict = process_body_type(kwargs['body_type'])

    kwargs = kwargs | modification_dict | years_dict | body_type_dict
    return AutoruModification(**kwargs)


class Command(BaseCommand):
    """
    Команда Django для импорта данных из XML-файла в базу данных.
    """

    help = 'Импорт данных из XML-файла'

    autoru_models = [
        AutoruMark,
        AutoruModel,
        AutoruGeneration,
        AutoruModification,
        AutoruComplectation,
    ]

    create_instance = {
        'marks': [],
        'models': [],
        'generations': [],
        'modifications': [],
        'complectations': [],
    }

    def handle(self, *args, **kwargs) -> None:
        """
        Обработка выполнения команды.

        :param args: Не используется.
        :param kwargs: Аргументы командной строки (не используется).
        """
        xml_link = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
        response: Response = requests.get(xml_link)
        xml_file: bytes = response.content
        # удаление старых данных перед парсингом
        self.clear_database()
        # Обработка XML-файла
        self.process_xml_file(xml_file)
        # Вставка новых данных в базу данных
        self.insert_data()

        self.stdout.write(self.style.SUCCESS("Обновление Авто.ру успешно!"))

    def clear_database(self) -> None:
        """
        Очистка всех записей из каждой таблицы в базе данных.
        """
        general_start = time()
        self.stdout.write(CYAN + f' {"Имя таблицы":<25} | {"Кол-во записей":<18} | {"Время удаления":<15}' + RESET)
        for model in reversed(self.autoru_models):
            start = time()  # Время начала удаления записей из текущей модели
            entries = model.objects.all()
            amount_entries = len(entries)
            entries.delete()  # Удаление записей
            duration = f'{round(time() - start, 2)} сек'  # Время удаления записей из текущей модели
            # Вывод информации о количестве удаленных записей с окраской
            self.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
            self.stdout.write(
                GREEN + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
                GREEN + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
                GREEN + f'{duration:<15}' + RESET)

            # Вывод общего времени удаления всех записей
        self.stdout.write(self.style.WARNING(f'\nОбщее время очистки: {round(time() - general_start, 2)} сек \n'))

    def insert_data(self):
        """
        Вставка новых данных в таблицы базы данных.
        """
        with transaction.atomic():
            general_start = time()
            self.stdout.write(CYAN + f' {"Имя таблицы":<25} | {"Кол-во записей":<18} | {"Время вставки":<15}' + RESET)
            for model, list_objects in zip(self.autoru_models, self.create_instance.values()):
                start = time()  # Время начала удаления записей из текущей модели
                entries = model.objects.bulk_create(list_objects)
                amount_entries = len(entries)
                duration = f'{round(time() - start, 2)} сек'  # Время удаления записей из текущей модели
                # Вывод информации о количестве удаленных записей с окраской
                self.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
                self.stdout.write(
                    GREEN + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
                    GREEN + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
                    GREEN + f'{duration:<15}' + RESET)

                # Вывод общего времени удаления всех записей
            self.stdout.write(self.style.WARNING(f'\nОбщее время вставки: {round(time() - general_start, 2)} сек \n'))

    def process_xml_file(self, xml_file: bytes) -> None:
        """
        Чтение и обработка XML-файла.
        Создаёт экземпляры даных и сохраняет в списки

        :param xml_file: Содержимое XML-файла.
        """
        counter = 0
        session_id = autoru_authenticate(env('AUTORU_LOGIN'), env('AUTORU_PASSWORD'))

        root: Element = etree.fromstring(xml_file)

        for mark_el in root.iterfind('./mark'):
            base_param = mark_el.find(
                'code').text + '#'  # Основной параметр с маркой Приклеили имя марки, например RENAULT
            mark_instance = AutoruMark(
                code_mark_autoru=mark_el.find('code').text,
                id_mark_autoru=mark_el.get('id'),
                name=mark_el.get('name'),
            )
            self.create_instance['marks'].append(mark_instance)

            for model_el in mark_el.iterfind('./folder'):
                result = procces_folder(
                    id_folder_autoru=model_el.get('id'),
                    mark=mark_instance,
                    name=model_el.get('name'),
                )
                model_instance = result['model_instance']
                generation_name = result['generation']
                self.create_instance['models'].append(model_instance)
                generation_instance = AutoruGeneration(
                    id_generation_autoru=model_el.get('id'),
                    model=model_instance,
                    name=generation_name,
                )

                self.create_instance['generations'].append(generation_instance)
                model_param = base_param + model_el.find('model').text + '#' + model_el.find('generation').text + '#'
                # приклелили имя модели, например CLIO_RS
                # приклеили id поколения, например 20926289
                for modification_el in model_el.iterfind('./modification'):
                    param = model_param + modification_el.find(
                        'configuration_id').text + '#' + modification_el.find(
                        'tech_param_id').text
                    if 'Electro' in modification_el.find('modification_id').text or '4WD' not in modification_el.find(
                            'modification_id').text:
                        result = get_autoru_catalog_structure(param, session_id)
                        if result == 'NO_AUTH':  # Если нужна повторная аутентификация
                            session_id = autoru_authenticate(login, password)
                            result = get_autoru_catalog_structure(param, session_id)
                        if result and 'breadcrumbs' in result:
                            tech_params = \
                                [dic for dic in result['breadcrumbs'][0]['entities'] if
                                 dic['id'] == modification_el.find(
                                     'tech_param_id').text][0]
                            counter += 1
                            print(counter)
                            if 'battery_capacity' in tech_params['tech_params']:
                                battery_capacity = tech_params['tech_params']['battery_capacity']
                                print('Объём батареи:', battery_capacity)
                            else:
                                battery_capacity = None
                            if 'gear_type' in tech_params['tech_params']:
                                gear_type = tech_params['tech_params']['gear_type']
                                drive = drive_mapping[gear_type]
                                print('Привод:', drive)
                            else:
                                drive = None
                    else:
                        battery_capacity = None
                        drive = 'Полный'
                    modification_instance = procces_modification(
                        id_modification_autoru=modification_el.get('id'),
                        name=modification_el.get('name'),
                        mark=mark_instance,
                        model=model_instance,
                        generation=generation_instance,
                        tech_param_id=modification_el.find('tech_param_id').text,
                        years=modification_el.find('years').text,
                        body_type=modification_el.find('body_type').text,
                        battery_capacity=battery_capacity,
                        drive=drive,

                    )

                    self.create_instance['modifications'].append(modification_instance)

                    for complectation_el in modification_el.iterfind('./complectations'):
                        complectation_instance = AutoruComplectation(
                            id_complectation_autoru=complectation_el.get('id'),
                            modification=modification_instance,
                            name=complectation_el.find('complectation').text
                            if complectation_el.find('complectation')
                            else None
                        )
                        self.create_instance['complectations'].append(complectation_instance)
