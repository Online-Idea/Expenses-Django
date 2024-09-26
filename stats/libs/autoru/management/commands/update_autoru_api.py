import time
from pprint import pprint

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
    """Authenticate and get session ID."""

    auth_url = f'{ENDPOINT}/auth/login'
    login_data = {'login': login, 'password': password}
    response = requests.post(url=auth_url, headers=HEADERS_AUTH, json=login_data)
    response.raise_for_status()
    session_id = {'x-session-id': response.json()['session']['id']}
    return session_id


def fetch_generation_name(mark_code: str, model_code: str, generation_id: str, session_id: Dict[str, str]) -> str:
    """Извлечение названия поколения из API. Если название не указано, возвращает годы в формате '2020 - 2024'."""

    param = f"{mark_code}#{model_code}#{generation_id}" if generation_id else f"{mark_code}#{model_code}"
    try:
        api_result = fetch_catalog_structure(param, session_id)
        for breadcrumb in api_result.get('breadcrumbs', []):
            if breadcrumb.get('meta_level') == 'GENERATION_LEVEL':
                generation_entity = breadcrumb.get('entities', [{}])[0]
                generation_name = generation_entity.get('name', '').strip()

                if not generation_name:
                    # Если название поколения пустое, извлекаем годы из поля super_gen
                    super_gen = generation_entity.get('super_gen', {})
                    year_start = super_gen.get('year_from', 'Unknown')
                    # Если года окончания нет, используем 'н.в.'
                    year_end = super_gen.get('year_to', 'н.в.')
                    generation_name = f"{year_start} - {year_end}"

                return generation_name

        return 'Unknown'
    except Exception as e:
        logger.red(f"Ошибка при извлечении названия поколения: {e}")
        return 'Unknown'


def fetch_catalog_structure(param: str, session_id: Dict[str, str], retries: int = 3) -> Dict:
    """Получение структуры каталога из API с повторными попытками."""

    url = f'{ENDPOINT}/search/cars/breadcrumbs'
    headers = {**HEADERS_AUTH, **session_id}
    params = {'bc_lookup': param}

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            status_code = None
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code  # Извлечение статус-кода из объекта исключения
                logger.yellow(
                    f"Ошибка запроса на попытке {attempt + 1}/{retries}. Статус-код: {status_code}. Ошибка: {e}")
            else:
                logger.red(
                    f"Запрос завершился неудачно на попытке {attempt + 1}/{retries} без получения объекта ответа: {e}")

            if status_code == 401:  # Unauthorized, повторная аутентификация
                logger.cyan("Ошибка 401: Неавторизованный доступ. Повторная аутентификация...")
                session_id = authenticate(LOGIN, PASSWORD)
                headers.update(session_id)

            if attempt < retries - 1:
                logger.yellow(f"Повторная попытка через {2 ** attempt} секунд(ы)...")
                time.sleep(2 ** attempt)  # Экспоненциальная задержка перед следующей попыткой
            else:
                logger.red(
                    f"Не удалось получить данные после {retries} попыток. Последний статус-код: {status_code}. Ошибка: {e}")
                raise RuntimeError(f"Не удалось получить данные с API auto.ru: {e}")


def process_mark_element(mark_el: etree.Element) -> AutoruMark:
    """Process mark element and return AutoruMark instance."""

    return AutoruMark(
        code_mark_level=mark_el.find('code').text,
        id_mark_level=mark_el.get('id'),
        name=mark_el.get('name'),
    )


def process_model_element(model_el: etree.Element, mark_instance: AutoruMark) -> AutoruModel:
    """Process model element and return AutoruModel instance."""

    model_name = model_el.get('name').split(',')[0]
    return AutoruModel(
        code_model_level=model_el.find('model').text,
        id_folder=model_el.get('id'),
        mark=mark_instance,
        name=model_name,
    )


def process_generation_element(model_el: etree.Element, model_instance: AutoruModel,
                               session_id: Dict[str, str]) -> AutoruGeneration:
    """Process generation element and return AutoruGeneration instance."""

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
        name=generation_name.strip()
    )


def map_drive_type(gear_type: str) -> str:
    """Map gear type to drive type in Russian."""

    mapping = {
        'ALL_WHEEL_DRIVE': 'Полный',
        'FORWARD_CONTROL': 'Передний',
        'REAR_DRIVE': 'Задний'
    }
    return mapping.get(gear_type, 'Unknown')


def map_transmission_type(transmission: str) -> str:
    """Map transmission type to Russian."""

    mapping = {
        'MECHANICAL': 'Механика',
        'AUTOMATIC': 'Автомат',
        'ROBOT': 'Робот',
        'VARIATOR': 'Вариатор'
    }
    return mapping.get(transmission, 'Unknown')


def map_drive_type_short(drive: str) -> str:
    """Map drive type to short abbreviation."""

    mapping = {
        'Полный': '4WD',
        'Задний': 'RWD',
        'Передний': 'FWD'
    }
    return mapping.get(drive, 'Unknown')


def map_transmission_type_short(transmission: str) -> str:
    """Map transmission type to short abbreviation."""

    mapping = {
        'Механика': 'MT',
        'Автомат': 'AT',
        'Робот': 'AMT',
        'Вариатор': 'CVT'
    }
    return mapping.get(transmission, 'Unknown')


def map_engine_type(engine_type: str) -> str:
    """Map engine type to Russian."""
    mapping = {
        'DIESEL': 'Дизель',
        'ELECTRO': 'Электро',
        'GASOLINE': 'Бензин',
        'HYBRID': 'Гибрид',
        'LPG': 'Газ'
    }
    return mapping.get(engine_type, 'Unknown')


def process_modification_element(modification_el: etree.Element, mark_instance: AutoruMark,
                                 model_instance: AutoruModel, generation_instance: AutoruGeneration,
                                 session_id: Dict[str, str]) -> Union[AutoruModification, None]:
    """Process modification element and return AutoruModification instance."""

    param = (f"{mark_instance.code_mark_level}#"
             f"{model_instance.code_model_level}#"
             f"{generation_instance.id_generation_level}#"
             f"{modification_el.find('configuration_id').text}#"
             f"{modification_el.find('tech_param_id').text}")
    try:
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
        logger.red(f"Error processing modification {modification_el.get('id')}: {e}")
        return None


def process_complectation_element(complectation_el: etree.Element, modification_instance: AutoruModification) -> Union[
    AutoruComplectation, None]:
    """Process complectation element and return AutoruComplectation instance."""
    id_complectation = complectation_el.get('id')

    if not id_complectation:
        logger.yellow(f"Skipping complectation due to missing id_complectation_autoru.")
        return None

    complectation_name = complectation_el.text.strip() if complectation_el.text is not None else ''
    return AutoruComplectation(
        id_complectation_autoru=id_complectation,
        modification=modification_instance,
        name=complectation_name
    )


def parse_xml_file(xml_file: bytes, session_id: Dict[str, str]) -> Dict[
    str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]:
    """Parse XML file and return data to insert."""

    data_to_insert = {
        'marks': [],
        'models': [],
        'generations': [],
        'modifications': [],
        'complectations': []
    }

    # Инициализация времени для отслеживания
    mark_times = []

    root = etree.fromstring(xml_file)
    total_marks = len(root.findall('./mark'))

    for mark_index, mark_el in enumerate(root.iterfind('./mark'), 1):
        mark_start = time.perf_counter()
        mark_instance = process_mark_element(mark_el)
        data_to_insert['marks'].append(mark_instance)
        logger.green(f"Идёт обработка марки {mark_index}/{total_marks}: {mark_instance.name}")

        for model_el in mark_el.iterfind('./folder'):
            model_instance = process_model_element(model_el, mark_instance)
            data_to_insert['models'].append(model_instance)

            generation_instance = process_generation_element(model_el, model_instance, session_id)
            data_to_insert['generations'].append(generation_instance)

            for modification_el in model_el.iterfind('./modification'):
                modification_instance = process_modification_element(modification_el, mark_instance, model_instance,
                                                                     generation_instance, session_id)
                if modification_instance:
                    data_to_insert['modifications'].append(modification_instance)

                    for complectation_el in modification_el.iterfind('./complectations/complectation'):
                        complectation_instance = process_complectation_element(complectation_el,
                                                                               modification_instance)
                        if complectation_instance:
                            data_to_insert['complectations'].append(complectation_instance)

        mark_end = time.perf_counter()
        mark_times.append(mark_end - mark_start)
        logger.blue(f"Завершена обработка марки {mark_index}/{total_marks}: {mark_instance.name}")

        # Расчет и вывод времени на уровне марок
        avg_mark_time = sum(mark_times) / len(mark_times) if mark_times else 0
        remaining_marks = total_marks - mark_index
        estimated_time = avg_mark_time * remaining_marks
        logger.yellow(f"Среднее время на марку: {avg_mark_time:.2f} секунд")
        logger.yellow(f"Ожидаемое время завершения: {estimated_time / 60:.2f} минут")

    return data_to_insert


def bulk_insert_data(data_to_insert: Dict[
    str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]) -> None:
    """Bulk insert data into the database."""
    with transaction.atomic():
        for name, objects in data_to_insert.items():
            if objects:
                model_name = f'Autoru{name.capitalize()[:-1]}'
                model = globals()[model_name]
                model.objects.bulk_create(objects)
                logger.purple(f"Inserted {len(objects)} records into {model_name}")


def clear_tables() -> None:
    """Clear all data from the tables before inserting new data."""
    AutoruMark.objects.all().delete()
    AutoruModel.objects.all().delete()
    AutoruGeneration.objects.all().delete()
    AutoruModification.objects.all().delete()
    AutoruComplectation.objects.all().delete()
    logger.red("All tables cleared")


class Command(BaseCommand):
    help = 'Парсинг данных из XML-файла'

    def handle(self, *args, **kwargs):
        session_id = authenticate(LOGIN, PASSWORD)
        xml_link = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
        response = requests.get(xml_link)
        xml_file = response.content
        total_start = time.perf_counter()
        clear_tables()  # Очистка всех таблиц перед вставкой новых данных
        data_to_insert = parse_xml_file(xml_file, session_id)
        bulk_insert_data(data_to_insert)
        total_end = time.perf_counter()
        logger.green("Process completed successfully")
        logger.green(f"Total time: {total_end - total_start:.2f} seconds")
        minutes = (total_end - total_start) // 60
        logger.green(f"Total time: {minutes} minutes")
