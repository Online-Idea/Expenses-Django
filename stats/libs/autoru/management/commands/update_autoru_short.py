import time
import requests
from lxml import etree
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import datetime
from typing import Dict, List, Union
from libs.autoru.models import AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation
from utils.colored_logger import ColoredLogger
from stats.settings import env

AUTORU_API_KEY = env('AUTORU_API_KEY')
HEADERS_AUTH = {
    'x-authorization': AUTORU_API_KEY,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
LOGIN = env('AUTORU_LOGIN')
PASSWORD = env('AUTORU_PASSWORD')
ENDPOINT = 'https://apiauto.ru/1.0'
logger = ColoredLogger(__name__)


def authenticate(login: str, password: str) -> Dict[str, str]:
    """Аутентификация и получение ID сессии."""
    auth_url = f'{ENDPOINT}/auth/login'
    login_data = {'login': login, 'password': password}
    response = requests.post(url=auth_url, headers=HEADERS_AUTH, json=login_data)
    response.raise_for_status()
    session_id = {'x-session-id': response.json()['session']['id']}
    logger.green("Аутентификация прошла успешно.")
    return session_id


def fetch_generation_name(mark_code: str, model_code: str, generation_id: str, session_id: Dict[str, str]) -> str:
    """Получение имени поколения через API."""
    param = f"{mark_code}#{model_code}#{generation_id}" if generation_id else f"{mark_code}#{model_code}"
    try:
        api_result = fetch_catalog_structure(param, session_id)
        for breadcrumb in api_result.get('breadcrumbs', []):
            if breadcrumb.get('meta_level') == 'GENERATION_LEVEL':
                generation_name = breadcrumb.get('entities', [{}])[0].get('name', 'Unknown')
                logger.green(f"Получено имя поколения из API: {generation_name}")
                return generation_name
        return 'Unknown'
    except Exception as e:
        logger.red(f"Ошибка при получении имени поколения: {e}")
        return 'Unknown'


def fetch_catalog_structure(param: str, session_id: Dict[str, str], retries: int = 3) -> Dict:
    """Получение структуры каталога через API с повторными попытками в случае неудачи."""
    url = f'{ENDPOINT}/search/cars/breadcrumbs'
    headers = {**HEADERS_AUTH, **session_id}
    params = {'bc_lookup': param}
    for attempt in range(retries):
        try:
            # logger.cyan(f"Получение структуры каталога для параметра: {param}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.red(f"Запрос не удался для параметра: {param}, попытка {attempt + 1}/{retries}")
            if response.status_code == 401:  # Неавторизован, повторная аутентификация
                session_id = authenticate(LOGIN, PASSWORD)
                headers.update(session_id)
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Экспоненциальная задержка
            else:
                raise RuntimeError(f"Не удалось получить данные от auto.ru API после {retries} попыток: {e}")


def get_existing_records():
    """Получение существующих записей из базы данных."""
    existing_marks_by_id = {mark.id_mark_level: mark for mark in AutoruMark.objects.all() if mark.id_mark_level}
    existing_marks_by_key = {f"{mark.name}_{mark.code_mark_level}": mark for mark in AutoruMark.objects.all() if
                             not mark.id_mark_level}

    existing_models = {model.id_folder: model for model in AutoruModel.objects.all()}
    existing_generations = {gen.id_generation_level: gen for gen in AutoruGeneration.objects.all()}
    existing_modifications = {mod.id_modification_autoru: mod for mod in AutoruModification.objects.all()}
    existing_complectations = {comp.id_complectation_autoru: comp for comp in AutoruComplectation.objects.all()}

    logger.green("Получены существующие записи из базы данных.")
    return {
        "marks_by_id": existing_marks_by_id,
        "marks_by_key": existing_marks_by_key,
        "models": existing_models,
        "generations": existing_generations,
        "modifications": existing_modifications,
        "complectations": existing_complectations
    }


def process_mark_element(mark_el: etree.Element) -> AutoruMark:
    """Обработка элемента марки и возврат экземпляра AutoruMark."""
    mark_name = mark_el.get('name')
    mark_code = mark_el.find('code').text
    mark_id = mark_el.get('id', None)  # Получаем id, если он есть, иначе None

    return AutoruMark(
        code_mark_level=mark_code,
        id_mark_level=mark_id,
        name=mark_name,
    )


def process_model_element(model_el: etree.Element, mark_instance: AutoruMark) -> AutoruModel:
    """Обработка элемента модели и возврат экземпляра AutoruModel."""
    model_name = model_el.get('name').split(',')[0]
    return AutoruModel(
        code_model_level=model_el.find('model').text,
        id_folder=model_el.get('id'),
        mark=mark_instance,
        name=model_name,
    )


def process_generation_element(model_el: etree.Element, model_instance: AutoruModel,
                               session_id: Dict[str, str]) -> AutoruGeneration:
    """Обработка элемента поколения и возврат экземпляра AutoruGeneration."""
    generation_code = model_el.find('generation').text
    if ',' in model_el.get('name'):
        generation_name = model_el.get('name').split(',', 1)[1]
    else:
        generation_name = fetch_generation_name(model_instance.mark.code_mark_level,
                                                model_instance.code_model_level,
                                                generation_code, session_id)
    return AutoruGeneration(
        id_generation_level=int(generation_code),
        model=model_instance,
        name=generation_name,
    )


def map_drive_type(gear_type: str) -> str:
    """Соответствие типа привода."""
    mapping = {
        'ALL_WHEEL_DRIVE': 'Полный',
        'FORWARD_CONTROL': 'Передний',
        'REAR_DRIVE': 'Задний'
    }
    return mapping.get(gear_type, 'Неизвестно')


def map_transmission_type(transmission: str) -> str:
    """Соответствие типа трансмиссии."""
    mapping = {
        'MECHANICAL': 'Механика',
        'AUTOMATIC': 'Автомат',
        'ROBOT': 'Робот',
        'VARIATOR': 'Вариатор'
    }
    return mapping.get(transmission, 'Неизвестно')


def map_drive_type_short(drive: str) -> str:
    """Соответствие типа привода (кратко)."""
    mapping = {
        'Полный': '4WD',
        'Задний': 'RWD',
        'Передний': 'FWD'
    }
    return mapping.get(drive, 'Неизвестно')


def map_transmission_type_short(transmission: str) -> str:
    """Соответствие типа трансмиссии (кратко)."""
    mapping = {
        'Механика': 'MT',
        'Автомат': 'AT',
        'Робот': 'AMT',
        'Вариатор': 'CVT'
    }
    return mapping.get(transmission, 'Неизвестно')


def map_engine_type(engine_type: str) -> str:
    """Соответствие типа двигателя."""
    mapping = {
        'DIESEL': 'Дизель',
        'ELECTRO': 'Электро',
        'GASOLINE': 'Бензин',
        'HYBRID': 'Гибрид',
        'LPG': 'Газ'
    }
    return mapping.get(engine_type, 'Неизвестно')


def process_modification_element(modification_el: etree.Element, mark_instance: AutoruMark,
                                 model_instance: AutoruModel, generation_instance: AutoruGeneration,
                                 session_id: Dict[str, str]) -> Union[AutoruModification, None]:
    """Обработка элемента модификации и возврат экземпляра AutoruModification."""
    param = (f"{mark_instance.code_mark_level}#"
             f"{model_instance.code_model_level}#"
             f"{generation_instance.id_generation_level}#"
             f"{modification_el.find('configuration_id').text}#"
             f"{modification_el.find('tech_param_id').text}")
    try:
        # logger.cyan(f"Обработка модификации с параметром: {param}")
        api_result = fetch_catalog_structure(param, session_id)
        tech_params = next(item for item in api_result['breadcrumbs'][0]['entities']
                           if item['id'] == modification_el.find('tech_param_id').text)

        power_hp = power_kw = 0
        battery_capacity = 0

        engine_type = map_engine_type(tech_params['tech_params']['engine_type'])

        if engine_type == 'Электро':
            power_kw = int(float(tech_params['tech_params'].get('power_kvt', 0)))
            battery_capacity = float(tech_params['tech_params'].get('battery_capacity', 0))
        else:
            power_hp = int(tech_params['tech_params'].get('power', 0))

        years_from = tech_params['tech_params'].get('year_start', None)
        years_to = tech_params['tech_params'].get('year_stop', None)
        if years_to is None or years_to == 0:
            years_to = datetime.now().year

        drive_type = map_drive_type(tech_params['tech_params']['gear_type'])
        drive_type_short = map_drive_type_short(drive_type)
        transmission_type = map_transmission_type(tech_params['tech_params']['transmission'])
        transmission_type_short = map_transmission_type_short(transmission_type)
        engine_volume_liters = round(tech_params['tech_params'].get('displacement', 0) / 1000, 1)
        doors = int(tech_params['tech_params'].get('doors_count', 4))

        short_name = (f"{engine_volume_liters} "
                      f"{power_hp if power_hp else power_kw} "
                      f"{'л.с.' if power_hp else 'кВт'} "
                      f"{drive_type_short} "
                      f"{engine_type} "
                      f"{transmission_type_short}")

        logger.green(
            f"Сформировано короткое имя: {logger.purple(short_name, return_value=True)} для модификации с ID: {modification_el.get('id')}")

        return AutoruModification(
            id_modification_autoru=modification_el.get('id'),
            mark=mark_instance,
            model=model_instance,
            generation=generation_instance,
            id_configuration_level=modification_el.find('configuration_id').text,
            id_tech_param_level=modification_el.find('tech_param_id').text,
            name=modification_el.find('modification_id').text,
            clients_name=modification_el.find('modification_id').text,
            short_name=short_name,
            years_from=int(years_from) if years_from else None,
            years_to=int(years_to) if years_to else None,
            power_hp=power_hp,
            power_kw=power_kw,
            engine_volume=engine_volume_liters,
            body_type=modification_el.find('body_type').text,
            transmission=transmission_type,
            drive=drive_type,
            engine_type=engine_type,
            battery_capacity=battery_capacity,
            doors=doors
        )
    except Exception as e:
        logger.red(f"Ошибка при обработке модификации с ID: {modification_el.get('id')}: {e}")
        return None


def process_complectation_element(complectation_el: etree.Element, modification_instance: AutoruModification) -> Union[
    AutoruComplectation, None]:
    """Обработка элемента комплектации и возврат экземпляра AutoruComplectation."""
    id_complectation = complectation_el.get('id')
    logger.cyan(f"Обработка комплектации с ID: {id_complectation}")

    if not id_complectation:
        logger.yellow(f"Пропуск комплектации из-за отсутствия ID.")
        return None

    complectation_name = complectation_el.text.strip() if complectation_el.text is not None else ''
    logger.green(f"Сформировано имя комплектации: {complectation_name} для ID: {id_complectation}")
    return AutoruComplectation(
        id_complectation_autoru=id_complectation,
        modification=modification_instance,
        name=complectation_name
    )


def log_new_data_counts(new_data: Dict[
    str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]):
    """Логирование количества новых созданных объектов в каждой категории."""

    for category, items in new_data.items():
        if items:
            logger.green(f"Создано новых {category[:-1]}: {len(items)}")
        else:
            logger.yellow(f"Не создано новых {category[:-1]}")


def parse_and_update(xml_file: bytes, session_id: Dict[str, str]):
    """Парсинг XML-файла и обновление базы данных новыми или измененными данными."""
    existing_records = get_existing_records()
    new_data = {
        'marks': [],
        'models': [],
        'generations': [],
        'modifications': [],
        'complectations': []
    }

    root = etree.fromstring(xml_file)
    for mark_el in root.iterfind('./mark'):
        mark_name = mark_el.get('name')
        mark_code = mark_el.find('code').text
        mark_id = int(mark_el.get('id', 0)) if mark_el.get('id') else None
        mark_key = f"{mark_name}_{mark_code}"

        # Проверяем существование марки по ID или по комбинации name и code
        if mark_id and mark_id in existing_records['marks_by_id']:
            mark_instance = existing_records['marks_by_id'].get(mark_id)
            logger.yellow(f"Марка с ID {mark_id} уже существует, пропускаем создание {mark_instance.name}")
        elif mark_key in existing_records['marks_by_key']:
            mark_instance = existing_records['marks_by_key'].get(mark_key)
            logger.yellow(f"Марка с ключом {mark_key} уже существует, пропускаем создание {mark_instance.name}")
        else:
            mark_instance = process_mark_element(mark_el)
            new_data['marks'].append(mark_instance)
            logger.green(f"Создана новая марка: {mark_instance.name}")

        for model_el in mark_el.iterfind('./folder'):
            model_id = int(model_el.get('id'))

            if model_id in existing_records['models']:
                model_instance = existing_records['models'].get(model_id)
                logger.yellow(f"Модель с ID {model_id} уже существует, пропускаем создание {model_instance.name}")
            else:
                model_instance = process_model_element(model_el, mark_instance)
                new_data['models'].append(model_instance)
                logger.green(f"Создана новая модель: {model_instance.name}")

            logger.cyan(f"Обработка поколения для модели: {model_instance.name}")
            # Обработка поколений
            generation_id = int(model_el.find('generation').text)

            if generation_id in existing_records['generations']:
                generation_instance = existing_records['generations'].get(generation_id)
                logger.yellow(
                    f"Поколение с ID {generation_id} уже существует, пропускаем создание {generation_instance.name}")
            else:
                # Создаем новое поколение с помощью API-запроса
                generation_instance = process_generation_element(model_el, model_instance, session_id)
                new_data['generations'].append(generation_instance)
                logger.green(f"Создано новое поколение: {generation_instance.name}")

            logger.cyan(f"Обработка модификации для поколения: {generation_instance.name}")

            for modification_el in model_el.iterfind('./modification'):
                modification_id = int(modification_el.get('id'))

                if modification_id in existing_records['modifications']:
                    modification_instance = existing_records['modifications'].get(modification_id)
                    logger.yellow(
                        f"Модификация с ID {modification_id} уже существует, пропускаем создание {modification_instance.name}")
                else:
                    modification_instance = process_modification_element(
                        modification_el, mark_instance, model_instance, generation_instance, session_id)
                    new_data['modifications'].append(modification_instance)
                    logger.green(f"Создана новая модификация: {modification_instance.name}")

                logger.cyan(f"Обработка комплектации для модификация: {modification_instance.name}")

                for complectation_el in modification_el.iterfind('./complectations/complectation'):
                    complectation_id = int(complectation_el.get('id'))

                    if complectation_id not in existing_records['complectations']:
                        complectation_instance = process_complectation_element(complectation_el, modification_instance)
                        new_data['complectations'].append(complectation_instance)
                        logger.green(f"Создана новая комплектация: {complectation_instance.name}")
                    else:
                        complectation_instance = existing_records['complectations'].get(complectation_id)
                        logger.yellow(
                            f"Комплектация с ID {complectation_id} уже существует, пропускаем создание {complectation_instance.name}")
                    #     existing_complectation = existing_records['complectations'][complectation_id]
                    #     if existing_complectation.name != complectation_instance.name:
                    #         existing_complectation.name = complectation_instance.name
                    #         existing_complectation.save()
                    #         logger.blue(f"Обновлена комплектация: {existing_complectation.name}")
    log_new_data_counts(new_data)
    bulk_insert_data(new_data)


def bulk_insert_data(data_to_insert: Dict[
    str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]) -> None:
    """Массовая вставка данных в базу данных."""
    with transaction.atomic():
        for name, objects in data_to_insert.items():
            if objects:
                model_name = f'Autoru{name.capitalize()[:-1]}'
                model = globals()[model_name]
                model.objects.bulk_create(objects)
                logger.purple(f"Вставлено {len(objects)} записей в {model_name}")


class Command(BaseCommand):
    help = 'Парсинг данных из XML-файла и обновление базы данных'

    def handle(self, *args, **kwargs):
        session_id = authenticate(LOGIN, PASSWORD)
        xml_link = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
        response = requests.get(xml_link)
        xml_file = response.content
        total_start = time.perf_counter()
        logger.green("Запуск процесса парсинга и обновления.")
        parse_and_update(xml_file, session_id)
        total_end = time.perf_counter()
        logger.green("Процесс завершен успешно.")
        logger.green(f"Общее время: {total_end - total_start:.2f} секунд")
        minutes = (total_end - total_start) // 60
        logger.green(f"Общее время: {minutes} минут")
#
# import time
# import requests
# from lxml import etree
# from django.core.management.base import BaseCommand
# from django.db import transaction
# from datetime import datetime
# from typing import Dict, List, Union
# from libs.autoru.models import AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation
# from utils.colored_logger import ColoredLogger
# from stats.settings import env
#
# AUTORU_API_KEY = env('AUTORU_API_KEY')
# HEADERS_AUTH = {
#     'x-authorization': AUTORU_API_KEY,
#     'Accept': 'application/json',
#     'Content-Type': 'application/json'
# }
# LOGIN = env('AUTORU_LOGIN')
# PASSWORD = env('AUTORU_PASSWORD')
# ENDPOINT = 'https://apiauto.ru/1.0'
# logger = ColoredLogger(__name__)
#
#
# def authenticate(login: str, password: str) -> Dict[str, str]:
#     """Authenticate and get session ID."""
#     auth_url = f'{ENDPOINT}/auth/login'
#     login_data = {'login': login, 'password': password}
#     response = requests.post(url=auth_url, headers=HEADERS_AUTH, json=login_data)
#     response.raise_for_status()
#     session_id = {'x-session-id': response.json()['session']['id']}
#     logger.green("Authenticated successfully.")
#     return session_id
#
#
# def fetch_generation_name(mark_code: str, model_code: str, generation_id: str, session_id: Dict[str, str]) -> str:
#     """Fetch generation name from API."""
#     param = f"{mark_code}#{model_code}#{generation_id}" if generation_id else f"{mark_code}#{model_code}"
#     try:
#         logger.cyan(f"Fetching generation name for {param}")
#         api_result = fetch_catalog_structure(param, session_id)
#         for breadcrumb in api_result.get('breadcrumbs', []):
#             if breadcrumb.get('meta_level') == 'GENERATION_LEVEL':
#                 generation_name = breadcrumb.get('entities', [{}])[0].get('name', 'Unknown')
#                 logger.green(f"Fetched generation name: {generation_name}")
#                 return generation_name
#         return 'Unknown'
#     except Exception as e:
#         logger.red(f"Error fetching generation name: {e}")
#         return 'Unknown'
#
#
# def fetch_catalog_structure(param: str, session_id: Dict[str, str], retries: int = 3) -> Dict:
#     """Fetch catalog structure from API with retries."""
#     url = f'{ENDPOINT}/search/cars/breadcrumbs'
#     headers = {**HEADERS_AUTH, **session_id}
#     params = {'bc_lookup': param}
#     for attempt in range(retries):
#         try:
#             logger.cyan(f"Fetching catalog structure for param: {param}")
#             response = requests.get(url, headers=headers, params=params)
#             response.raise_for_status()
#             return response.json()
#         except requests.RequestException as e:
#             logger.red(f"Request failed for param: {param}, attempt {attempt + 1}/{retries}")
#             if response.status_code == 401:  # Unauthorized, try re-authentication
#                 session_id = authenticate(LOGIN, PASSWORD)
#                 headers.update(session_id)
#             if attempt < retries - 1:
#                 time.sleep(2 ** attempt)  # Exponential backoff
#             else:
#                 raise RuntimeError(f"Failed to fetch data from auto.ru API after {retries} attempts: {e}")
#
#
# def get_existing_records():
#     """Get existing records from the database."""
#     existing_marks_by_id = {mark.id_mark_level: mark for mark in AutoruMark.objects.all() if mark.id_mark_level}
#     existing_marks_by_key = {f"{mark.name}_{mark.code_mark_level}": mark for mark in AutoruMark.objects.all() if not mark.id_mark_level}
#
#     existing_models = {model.id_folder: model for model in AutoruModel.objects.all()}
#     existing_generations = {gen.id_generation_level: gen for gen in AutoruGeneration.objects.all()}
#     existing_modifications = {mod.id_modification_autoru: mod for mod in AutoruModification.objects.all()}
#     existing_complectations = {comp.id_complectation_autoru: comp for comp in AutoruComplectation.objects.all()}
#
#     return {
#         "marks_by_id": existing_marks_by_id,
#         "marks_by_key": existing_marks_by_key,
#         "models": existing_models,
#         "generations": existing_generations,
#         "modifications": existing_modifications,
#         "complectations": existing_complectations
#     }
#
#
#
# def process_mark_element(mark_el: etree.Element) -> AutoruMark:
#     """Process mark element and return AutoruMark instance."""
#     mark_name = mark_el.get('name')
#     mark_code = mark_el.find('code').text
#     mark_id = mark_el.get('id', None)  # Получаем id, если он есть, иначе None
#
#     return AutoruMark(
#         code_mark_level=mark_code,
#         id_mark_level=mark_id,
#         name=mark_name,
#     )
#
# def process_model_element(model_el: etree.Element, mark_instance: AutoruMark) -> AutoruModel:
#     """Process model element and return AutoruModel instance."""
#     model_name = model_el.get('name').split(',')[0]
#     return AutoruModel(
#         code_model_level=model_el.find('model').text,
#         id_folder=model_el.get('id'),
#         mark=mark_instance,
#         name=model_name,
#     )
#
#
# def process_generation_element(model_el: etree.Element, model_instance: AutoruModel,
#                                session_id: Dict[str, str]) -> AutoruGeneration:
#     """Process generation element and return AutoruGeneration instance."""
#     generation_code = model_el.find('generation').text
#     if ',' in model_el.get('name'):
#         generation_name = model_el.get('name').split(',', 1)[1]
#     else:
#         generation_name = fetch_generation_name(model_instance.mark.code_mark_level,
#                                                 model_instance.code_model_level,
#                                                 generation_code, session_id)
#     return AutoruGeneration(
#         id_generation_level=int(generation_code),
#         model=model_instance,
#         name=generation_name,
#     )
#
#
# def map_drive_type(gear_type: str) -> str:
#     """Map gear type to drive type in Russian."""
#     mapping = {
#         'ALL_WHEEL_DRIVE': 'Полный',
#         'FORWARD_CONTROL': 'Передний',
#         'REAR_DRIVE': 'Задний'
#     }
#     return mapping.get(gear_type, 'Unknown')
#
#
# def map_transmission_type(transmission: str) -> str:
#     """Map transmission type to Russian."""
#     mapping = {
#         'MECHANICAL': 'Механика',
#         'AUTOMATIC': 'Автомат',
#         'ROBOT': 'Робот',
#         'VARIATOR': 'Вариатор'
#     }
#     return mapping.get(transmission, 'Unknown')
#
#
# def map_drive_type_short(drive: str) -> str:
#     """Map drive type to short abbreviation."""
#     mapping = {
#         'Полный': '4WD',
#         'Задний': 'RWD',
#         'Передний': 'FWD'
#     }
#     return mapping.get(drive, 'Unknown')
#
#
# def map_transmission_type_short(transmission: str) -> str:
#     """Map transmission type to short abbreviation."""
#     mapping = {
#         'Механика': 'MT',
#         'Автомат': 'AT',
#         'Робот': 'AMT',
#         'Вариатор': 'CVT'
#     }
#     return mapping.get(transmission, 'Unknown')
#
#
# def map_engine_type(engine_type: str) -> str:
#     """Map engine type to Russian."""
#     mapping = {
#         'DIESEL': 'Дизель',
#         'ELECTRO': 'Электро',
#         'GASOLINE': 'Бензин',
#         'HYBRID': 'Гибрид',
#         'LPG': 'Газ'
#     }
#     return mapping.get(engine_type, 'Unknown')
#
#
# def process_modification_element(modification_el: etree.Element, mark_instance: AutoruMark,
#                                  model_instance: AutoruModel, generation_instance: AutoruGeneration,
#                                  session_id: Dict[str, str]) -> Union[AutoruModification, None]:
#     """Process modification element and return AutoruModification instance."""
#     param = (f"{mark_instance.code_mark_level}#"
#              f"{model_instance.code_model_level}#"
#              f"{generation_instance.id_generation_level}#"
#              f"{modification_el.find('configuration_id').text}#"
#              f"{modification_el.find('tech_param_id').text}")
#     try:
#         logger.cyan(f"Processing modification with param: {param}")
#         api_result = fetch_catalog_structure(param, session_id)
#         tech_params = next(item for item in api_result['breadcrumbs'][0]['entities']
#                            if item['id'] == modification_el.find('tech_param_id').text)
#
#         power_hp = power_kw = 0
#         battery_capacity = 0
#
#         engine_type = map_engine_type(tech_params['tech_params']['engine_type'])
#
#         if engine_type == 'Электро':
#             power_kw = int(float(tech_params['tech_params'].get('power_kvt', 0)))
#             battery_capacity = float(tech_params['tech_params'].get('battery_capacity', 0))
#         else:
#             power_hp = int(tech_params['tech_params'].get('power', 0))
#
#         years_from = tech_params['tech_params'].get('year_start', None)
#         years_to = tech_params['tech_params'].get('year_stop', None)
#         if years_to is None or years_to == 0:
#             years_to = datetime.now().year
#
#         drive_type = map_drive_type(tech_params['tech_params']['gear_type'])
#         drive_type_short = map_drive_type_short(drive_type)
#         transmission_type = map_transmission_type(tech_params['tech_params']['transmission'])
#         transmission_type_short = map_transmission_type_short(transmission_type)
#         engine_volume_liters = round(tech_params['tech_params'].get('displacement', 0) / 1000, 1)
#         doors = int(tech_params['tech_params'].get('doors_count', 4))
#
#         short_name = (f"{engine_volume_liters} "
#                       f"{power_hp if power_hp else power_kw} "
#                       f"{'л.с.' if power_hp else 'кВт'} "
#                       f"{drive_type_short} "
#                       f"{engine_type} "
#                       f"{transmission_type_short}")
#
#         logger.green(f"Generated short name: {short_name} for modification ID: {modification_el.get('id')}")
#
#         return AutoruModification(
#             id_modification_autoru=modification_el.get('id'),
#             mark=mark_instance,
#             model=model_instance,
#             generation=generation_instance,
#             id_configuration_level=modification_el.find('configuration_id').text,
#             id_tech_param_level=modification_el.find('tech_param_id').text,
#             name=modification_el.find('modification_id').text,
#             clients_name=modification_el.find('modification_id').text,
#             short_name=short_name,
#             years_from=int(years_from) if years_from else None,
#             years_to=int(years_to) if years_to else None,
#             power_hp=power_hp,
#             power_kw=power_kw,
#             engine_volume=engine_volume_liters,
#             body_type=modification_el.find('body_type').text,
#             transmission=transmission_type,
#             drive=drive_type,
#             engine_type=engine_type,
#             battery_capacity=battery_capacity,
#             doors=doors
#         )
#     except Exception as e:
#         logger.red(f"Error processing modification {modification_el.get('id')}: {e}")
#         return None
#
#
# def process_complectation_element(complectation_el: etree.Element, modification_instance: AutoruModification) -> Union[
#     AutoruComplectation, None]:
#     """Process complectation element and return AutoruComplectation instance."""
#     id_complectation = complectation_el.get('id')
#     logger.cyan(f"Processing complectation with ID: {id_complectation}")
#
#     if not id_complectation:
#         logger.yellow(f"Skipping complectation due to missing id_complectation_autoru.")
#         return None
#
#     complectation_name = complectation_el.text.strip() if complectation_el.text is not None else ''
#     logger.green(f"Generated complectation name: {complectation_name} for ID: {id_complectation}")
#     return AutoruComplectation(
#         id_complectation_autoru=id_complectation,
#         modification=modification_instance,
#         name=complectation_name
#     )
#
#
# def parse_and_update(xml_file: bytes, session_id: Dict[str, str]):
#     """Parse XML file and update the database with new or changed data."""
#     existing_records = get_existing_records()
#     new_data = {
#         'marks': [],
#         'models': [],
#         'generations': [],
#         'modifications': [],
#         'complectations': []
#     }
#
#     root = etree.fromstring(xml_file)
#     for mark_el in root.iterfind('./mark'):
#         mark_name = mark_el.get('name')
#         mark_code = mark_el.find('code').text
#         mark_id = int(mark_el.get('id', 0)) if mark_el.get('id') else None
#         mark_key = f"{mark_name}_{mark_code}"
#
#         # Если есть ID, проверяем по нему
#         if mark_id and mark_id in existing_records['marks_by_id']:
#             mark_instance = existing_records['marks_by_id'].get(mark_id)
#             logger.blue(f"Извлечена существующая марка по ID: {mark_instance.name}")
#         elif mark_key in existing_records['marks_by_key']:
#             mark_instance = existing_records['marks_by_key'].get(mark_key)
#             logger.blue(f"Извлечена существующая марка по CODE_LEVEL: {mark_instance.name}")
#         else:
#             mark_instance = process_mark_element(mark_el)
#             new_data['marks'].append(mark_instance)
#             logger.blue(f"Создана новая МАРКА: {mark_instance.name}")
#
#         for model_el in mark_el.iterfind('./folder'):
#             model_id = int(model_el.get('id'))
#
#             if model_id in existing_records['models']:
#                 model_instance = existing_records['models'].get(model_id)
#             else:
#                 model_instance = process_model_element(model_el, mark_instance)
#                 new_data['models'].append(model_instance)
#                 logger.blue(f"Создана новая МОДЕЛЬ: {model_instance.name}")
#
#             logger.cyan(f"Обработка поколения для модели: {model_instance.name}")
#             # Обработка поколений
#             generation_id = int(model_el.find('generation').text)
#
#             if generation_id in existing_records['generations']:
#                 generation_instance = existing_records['generations'].get(generation_id)
#                 logger.yellow(f"Поколение с ID {generation_id} уже существует, пропускаем создание.")
#             else:
#                 # Создаем новое поколение с помощью API-запроса
#                 generation_instance = process_generation_element(model_el, model_instance, session_id)
#                 new_data['generations'].append(generation_instance)
#                 logger.green(f"Создано новое поколение: {generation_instance.name}")
#
#
#             logger.cyan(f"Обработка модификации для поколения: {generation_instance.name}")
#
#             for modification_el in model_el.iterfind('./modification'):
#                 modification_id = modification_el.get('id')
#
#                 if modification_id in existing_records['modifications']:
#                     modification_instance = existing_records['modifications'].get(modification_id)
#                 else:
#                     modification_instance = process_modification_element(
#                         modification_el, mark_instance, model_instance, generation_instance, session_id)
#                     new_data['modifications'].append(modification_instance)
#
#                 logger.cyan(f"Обработка коплектации: {modification_instance.name}")
#
#                 for complectation_el in modification_el.iterfind('./complectations/complectation'):
#                     complectation_id = complectation_el.get('id')
#                     complectation_instance = process_complectation_element(complectation_el, modification_instance)
#
#                     if complectation_id not in existing_records['complectations']:
#                         new_data['complectations'].append(complectation_instance)
#                     else:
#                         existing_complectation = existing_records['complectations'][complectation_id]
#                         if existing_complectation.name != complectation_instance.name:
#                             existing_complectation.name = complectation_instance.name
#                             existing_complectation.save()
#                             logger.blue(f"Updated complectation: {existing_complectation.name}")
#
#     bulk_insert_data(new_data)
#
#
# def bulk_insert_data(data_to_insert: Dict[
#     str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]) -> None:
#     """Bulk insert data into the database."""
#     with transaction.atomic():
#         for name, objects in data_to_insert.items():
#             if objects:
#                 model_name = f'Autoru{name.capitalize()[:-1]}'
#                 model = globals()[model_name]
#                 model.objects.bulk_create(objects)
#                 logger.purple(f"Inserted {len(objects)} records into {model_name}")
#
#
# class Command(BaseCommand):
#     help = 'Парсинг данных из XML-файла и обновление базы данных'
#
#     def handle(self, *args, **kwargs):
#         session_id = authenticate(LOGIN, PASSWORD)
#         xml_link = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
#         response = requests.get(xml_link)
#         xml_file = response.content
#         total_start = time.perf_counter()
#         logger.green("Starting the parsing and update process.")
#         parse_and_update(xml_file, session_id)
#         total_end = time.perf_counter()
#         logger.green("Process completed successfully")
#         logger.green(f"Total time: {total_end - total_start:.2f} seconds")
#         minutes = (total_end - total_start) // 60
#         logger.green(f"Total time: {minutes} minutes")
