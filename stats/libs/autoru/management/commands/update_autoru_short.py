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

# Получение необходимых данных для аутентификации из переменных окружения
AUTORU_API_KEY = env('AUTORU_API_KEY')
HEADERS_AUTH = {
    'x-authorization': AUTORU_API_KEY,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
LOGIN = env('AUTORU_LOGIN')
PASSWORD = env('AUTORU_PASSWORD')
ENDPOINT = 'https://apiauto.ru/1.0'

# Логгер для вывода сообщений в консоль
logger = ColoredLogger(__name__)


def authenticate(login: str, password: str) -> Dict[str, str]:
    """
    Аутентификация пользователя в API auto.ru и получение session ID.

    :param login: Логин пользователя
    :param password: Пароль пользователя
    :return: Заголовки с session ID для последующих запросов
    """
    auth_url = f'{ENDPOINT}/auth/login'
    login_data = {'login': login, 'password': password}
    response = requests.post(url=auth_url, headers=HEADERS_AUTH, json=login_data)
    response.raise_for_status()  # Проверка на наличие ошибок
    session_id = {'x-session-id': response.json()['session']['id']}
    logger.green("Аутентификация прошла успешно.")
    return session_id


def fetch_generation_name(mark_code: str, model_code: str, generation_id: str, session_id: Dict[str, str]) -> str:
    """
    Получение названия поколения автомобиля через API.

    :param mark_code: Код марки автомобиля
    :param model_code: Код модели автомобиля
    :param generation_id: ID поколения автомобиля
    :param session_id: Заголовки с session ID для аутентификации
    :return: Название поколения автомобиля или 'Unknown', если данные не найдены
    """
    # Формируем параметры для запроса к API
    param = f"{mark_code}#{model_code}#{generation_id}" if generation_id else f"{mark_code}#{model_code}"
    try:
        # Получаем структуру каталога из API
        api_result = fetch_catalog_structure(param, session_id)
        # Проходим по "breadcrumbs" и ищем уровень поколения
        for breadcrumb in api_result.get('breadcrumbs', []):
            if breadcrumb.get('meta_level') == 'GENERATION_LEVEL':
                generation_name = breadcrumb.get('entities', [{}])[0].get('name', 'Unknown')
                logger.green(f"Получено имя поколения из API: {generation_name}")
                return generation_name
        return 'Unknown'
    except Exception as e:
        # В случае ошибки логируем и возвращаем 'Unknown'
        logger.red(f"Ошибка при получении имени поколения: {e}")
        return 'Unknown'


def fetch_catalog_structure(param: str, session_id: Dict[str, str], retries: int = 3) -> Dict:
    """
    Получение структуры каталога автомобилей через API с повторными попытками в случае неудачи.

    :param param: Параметры запроса
    :param session_id: Заголовки с session ID для аутентификации
    :param retries: Количество попыток при неудачных запросах
    :return: Ответ API в формате словаря
    """
    url = f'{ENDPOINT}/search/cars/breadcrumbs'
    headers = {**HEADERS_AUTH, **session_id}
    params = {'bc_lookup': param}

    for attempt in range(retries):
        try:
            # Выполняем запрос к API
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Проверка на наличие ошибок
            return response.json()  # Возвращаем данные в формате JSON
        except requests.RequestException as e:
            logger.red(f"Запрос не удался для параметра: {param}, попытка {attempt + 1}/{retries}")
            if response.status_code == 401:  # Если ошибка авторизации, повторяем аутентификацию
                session_id = authenticate(LOGIN, PASSWORD)
                headers.update(session_id)
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Экспоненциальная задержка перед повторной попыткой
            else:
                raise RuntimeError(f"Не удалось получить данные от API после {retries} попыток: {e}")


def get_existing_records() -> Dict[str, Dict]:
    """
    Получение существующих записей из базы данных для предотвращения дублирования.

    :return: Словарь с существующими записями по категориям (marks, models, generations, modifications, complectations)
    """
    # Сохраняем все существующие записи для последующей проверки на дубликаты
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
    """
    Обработка элемента марки из XML и создание экземпляра AutoruMark.

    :param mark_el: XML элемент, представляющий марку
    :return: Экземпляр модели AutoruMark
    """
    # Извлекаем необходимые атрибуты марки из XML элемента
    mark_name = mark_el.get('name')
    mark_code = mark_el.find('code').text
    mark_id = mark_el.get('id', None)  # Если ID отсутствует, возвращаем None

    return AutoruMark(
        code_mark_level=mark_code,
        id_mark_level=mark_id,
        name=mark_name,
    )


def process_model_element(model_el: etree.Element, mark_instance: AutoruMark) -> AutoruModel:
    """
    Обработка элемента модели из XML и создание экземпляра AutoruModel.

    :param model_el: XML элемент, представляющий модель
    :param mark_instance: Экземпляр марки AutoruMark, к которой относится модель
    :return: Экземпляр модели AutoruModel
    """
    # Извлекаем имя модели, очищаем его от возможных дополнительных данных
    model_name = model_el.get('name').split(',')[0]

    return AutoruModel(
        code_model_level=model_el.find('model').text,
        id_folder=model_el.get('id'),
        mark=mark_instance,
        name=model_name,
    )


def process_generation_element(model_el: etree.Element, model_instance: AutoruModel,
                               session_id: Dict[str, str]) -> AutoruGeneration:
    """
    Обработка элемента поколения из XML и создание экземпляра AutoruGeneration.

    :param model_el: XML элемент, представляющий модель
    :param model_instance: Экземпляр модели AutoruModel, к которой относится поколение
    :param session_id: Заголовки с session ID для аутентификации в API
    :return: Экземпляр модели AutoruGeneration
    """
    # Извлекаем код поколения и пытаемся получить его название
    generation_code = model_el.find('generation').text
    if ',' in model_el.get('name'):
        generation_name = model_el.get('name').split(',', 1)[1]
    else:
        # Если имя поколения отсутствует, запрашиваем его через API
        generation_name = fetch_generation_name(model_instance.mark.code_mark_level,
                                                model_instance.code_model_level,
                                                generation_code, session_id)
    return AutoruGeneration(
        id_generation_level=int(generation_code),
        model=model_instance,
        name=generation_name,
    )


def map_drive_type(gear_type: str) -> str:
    """
    Преобразует тип привода на русском языке.

    :param gear_type: Тип привода на английском языке
    :return: Преобразованное название привода на русском языке
    """
    # Сопоставляем тип привода с русским названием
    mapping = {
        'ALL_WHEEL_DRIVE': 'Полный',
        'FORWARD_CONTROL': 'Передний',
        'REAR_DRIVE': 'Задний'
    }
    return mapping.get(gear_type, 'Неизвестно')


def map_transmission_type(transmission: str) -> str:
    """
    Преобразует тип трансмиссии на русском языке.

    :param transmission: Тип трансмиссии на английском языке
    :return: Преобразованное название трансмиссии на русском языке
    """
    # Сопоставляем тип трансмиссии с русским названием
    mapping = {
        'MECHANICAL': 'Механика',
        'AUTOMATIC': 'Автомат',
        'ROBOT': 'Робот',
        'VARIATOR': 'Вариатор'
    }
    return mapping.get(transmission, 'Неизвестно')


def map_drive_type_short(drive: str) -> str:
    """
    Преобразует тип привода в краткую форму (аббревиатуры).

    :param drive: Полное название привода на русском языке
    :return: Сокращенное название привода (например, '4WD')
    """
    # Сопоставляем тип привода с сокращенным обозначением
    mapping = {
        'Полный': '4WD',
        'Задний': 'RWD',
        'Передний': 'FWD'
    }
    return mapping.get(drive, 'Неизвестно')


def map_transmission_type_short(transmission: str) -> str:
    """
    Преобразует тип трансмиссии в краткую форму (аббревиатуры).

    :param transmission: Полное название трансмиссии на русском языке
    :return: Сокращенное название трансмиссии (например, 'MT')
    """
    # Сопоставляем тип трансмиссии с сокращенным обозначением
    mapping = {
        'Механика': 'MT',
        'Автомат': 'AT',
        'Робот': 'AMT',
        'Вариатор': 'CVT'
    }
    return mapping.get(transmission, 'Неизвестно')


def map_engine_type(engine_type: str) -> str:
    """
    Преобразует тип двигателя на русском языке.

    :param engine_type: Тип двигателя на английском языке
    :return: Преобразованное название двигателя на русском языке
    """
    # Сопоставляем тип двигателя с русским названием
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
    """
    Обработка элемента модификации из XML и создание экземпляра AutoruModification.

    :param modification_el: XML элемент, представляющий модификацию
    :param mark_instance: Экземпляр марки AutoruMark, к которой относится модификация
    :param model_instance: Экземпляр модели AutoruModel, к которой относится модификация
    :param generation_instance: Экземпляр поколения AutoruGeneration, к которому относится модификация
    :param session_id: Заголовки с session ID для аутентификации в API
    :return: Экземпляр модели AutoruModification или None в случае ошибки
    """
    # Формируем параметр для запроса к API
    param = (f"{mark_instance.code_mark_level}#"
             f"{model_instance.code_model_level}#"
             f"{generation_instance.id_generation_level}#"
             f"{modification_el.find('configuration_id').text}#"
             f"{modification_el.find('tech_param_id').text}")
    try:
        # Получаем структуру каталога по модификации через API
        api_result = fetch_catalog_structure(param, session_id)
        tech_params = next(item for item in api_result['breadcrumbs'][0]['entities']
                           if item['id'] == modification_el.find('tech_param_id').text)

        power_hp = power_kw = 0
        battery_capacity = 0

        # Определяем тип двигателя
        engine_type = map_engine_type(tech_params['tech_params']['engine_type'])

        # Если двигатель электрический, то используем мощность в кВт и емкость батареи
        if engine_type == 'Электро':
            power_kw = int(float(tech_params['tech_params'].get('power_kvt', 0)))
            battery_capacity = float(tech_params['tech_params'].get('battery_capacity', 0))
        else:
            power_hp = int(tech_params['tech_params'].get('power', 0))

        # Получаем года выпуска
        years_from = tech_params['tech_params'].get('year_start', None)
        years_to = tech_params['tech_params'].get('year_stop', None)
        if years_to is None or years_to == 0:
            years_to = datetime.now().year

        # Определяем тип привода, коробки передач и объём двигателя
        drive_type = map_drive_type(tech_params['tech_params']['gear_type'])
        drive_type_short = map_drive_type_short(drive_type)
        transmission_type = map_transmission_type(tech_params['tech_params']['transmission'])
        transmission_type_short = map_transmission_type_short(transmission_type)
        engine_volume_liters = round(tech_params['tech_params'].get('displacement', 0) / 1000, 1)
        doors = int(tech_params['tech_params'].get('doors_count', 4))  # По умолчанию 4 двери

        # Формируем короткое название модификации
        short_name = (f"{engine_volume_liters} "
                      f"{power_hp if power_hp else power_kw} "
                      f"{'л.с.' if power_hp else 'кВт'} "
                      f"{drive_type_short} "
                      f"{engine_type} "
                      f"{transmission_type_short}")

        logger.green(f"Сформировано короткое имя модификации: {short_name} для ID: {modification_el.get('id')}")

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
        # В случае ошибки логируем и возвращаем None
        logger.red(f"Ошибка при обработке модификации с ID: {modification_el.get('id')}: {e}")
        return None


def process_complectation_element(complectation_el: etree.Element, modification_instance: AutoruModification) -> Union[
    AutoruComplectation, None]:
    """
    Обработка элемента комплектации из XML и создание экземпляра AutoruComplectation.

    :param complectation_el: XML элемент, представляющий комплектацию
    :param modification_instance: Экземпляр модификации AutoruModification, к которой относится комплектация
    :return: Экземпляр модели AutoruComplectation или None в случае ошибки
    """
    # Извлекаем ID комплектации из XML
    id_complectation = complectation_el.get('id')

    logger.cyan(f"Обработка комплектации с ID: {id_complectation}")

    # Если ID отсутствует, пропускаем этот элемент
    if not id_complectation:
        logger.yellow(f"Пропуск комплектации из-за отсутствия ID.")
        return None

    # Извлекаем название комплектации и создаем экземпляр AutoruComplectation
    complectation_name = complectation_el.text.strip() if complectation_el.text is not None else ''
    logger.green(f"Сформировано имя комплектации: {complectation_name} для ID: {id_complectation}")
    return AutoruComplectation(
        id_complectation_autoru=id_complectation,
        modification=modification_instance,
        name=complectation_name
    )


def log_new_data_counts(new_data: Dict[
    str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]):
    """
    Логирование количества новых созданных объектов в каждой категории.

    :param new_data: Словарь с новыми данными для вставки в базу данных
    """
    # Логируем количество созданных объектов в каждой категории
    for category, items in new_data.items():
        if items:
            logger.green(f"Создано новых {category[:-1]}: {len(items)}")
        else:
            logger.yellow(f"Не создано новых {category[:-1]}")


def parse_and_update(xml_file: bytes, session_id: Dict[str, str]):
    """
    Парсинг XML-файла и обновление базы данных новыми или измененными данными.

    :param xml_file: XML файл в байтовом формате
    :param session_id: Заголовки с session ID для аутентификации в API
    """
    # Получаем существующие записи для предотвращения дублирования
    existing_records = get_existing_records()

    # Инициализируем словарь для хранения новых данных
    new_data = {
        'marks': [],
        'models': [],
        'generations': [],
        'modifications': [],
        'complectations': []
    }

    # Парсим XML файл
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
            # Создаем новую марку
            mark_instance = process_mark_element(mark_el)
            new_data['marks'].append(mark_instance)
            logger.green(f"Создана новая марка: {mark_instance.name}")

        # Обработка моделей
        for model_el in mark_el.iterfind('./folder'):
            model_id = int(model_el.get('id'))

            if model_id in existing_records['models']:
                model_instance = existing_records['models'].get(model_id)
                logger.yellow(f"Модель с ID {model_id} уже существует, пропускаем создание {model_instance.name}")
            else:
                # Создаем новую модель
                model_instance = process_model_element(model_el, mark_instance)
                new_data['models'].append(model_instance)
                logger.green(f"Создана новая модель: {model_instance.name}")

            # Обработка поколений
            generation_id = int(model_el.find('generation').text)

            if generation_id in existing_records['generations']:
                generation_instance = existing_records['generations'].get(generation_id)
                logger.yellow(
                    f"Поколение с ID {generation_id} уже существует, пропускаем создание {generation_instance.name}")
            else:
                # Создаем новое поколение через API
                generation_instance = process_generation_element(model_el, model_instance, session_id)
                new_data['generations'].append(generation_instance)
                logger.green(f"Создано новое поколение: {generation_instance.name}")

            # Обработка модификаций
            for modification_el in model_el.iterfind('./modification'):
                modification_id = int(modification_el.get('id'))

                if modification_id in existing_records['modifications']:
                    modification_instance = existing_records['modifications'].get(modification_id)
                    logger.yellow(
                        f"Модификация с ID {modification_id} уже существует, пропускаем создание {modification_instance.name}")
                else:
                    # Создаем новую модификацию
                    modification_instance = process_modification_element(modification_el, mark_instance, model_instance,
                                                                         generation_instance, session_id)
                    new_data['modifications'].append(modification_instance)
                    logger.green(f"Создана новая модификация: {modification_instance.name}")

                # Обработка комплектаций
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

    # Логируем количество созданных объектов
    log_new_data_counts(new_data)
    # Выполняем массовую вставку новых данных в базу данных
    bulk_insert_data(new_data)


def bulk_insert_data(data_to_insert: Dict[
    str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]) -> None:
    """
    Массовая вставка данных в базу данных с использованием транзакций.

    :param data_to_insert: Словарь с данными для вставки (марки, модели, поколения, модификации, комплектации)
    """
    # Используем атомарные транзакции для сохранения данных
    with transaction.atomic():
        for name, objects in data_to_insert.items():
            if objects:
                # Формируем имя модели для вставки данных
                model_name = f'Autoru{name.capitalize()[:-1]}'
                model = globals()[model_name]
                # Выполняем массовую вставку данных
                model.objects.bulk_create(objects)
                logger.purple(f"Вставлено {len(objects)} записей в {model_name}")


class Command(BaseCommand):
    """
    Django команда для парсинга данных из XML-файла и обновления базы данных.

    Команда выполняет:
    - Аутентификацию в API auto.ru
    - Скачивание XML-файла с данными
    - Парсинг и обновление базы данных новыми данными
    """
    help = 'Парсинг данных из XML-файла и обновление базы данных'

    def handle(self, *args, **kwargs):
        """
        Основная логика выполнения команды.
        - Аутентификация
        - Загрузка XML-файла
        - Парсинг и обновление базы данных
        """
        # Аутентификация в API
        session_id = authenticate(LOGIN, PASSWORD)

        # Скачивание XML-файла с данными
        xml_link = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
        response = requests.get(xml_link)
        xml_file = response.content

        # Засекаем время начала процесса
        total_start = time.perf_counter()

        logger.green("Запуск процесса парсинга и обновления.")

        # Парсинг XML и обновление базы данных
        parse_and_update(xml_file, session_id)

        # Засекаем время окончания процесса
        total_end = time.perf_counter()
        logger.green("Процесс завершен успешно.")
        logger.green(f"Общее время: {total_end - total_start:.2f} секунд")
        minutes = (total_end - total_start) // 60
        logger.green(f"Общее время: {minutes} минут")
