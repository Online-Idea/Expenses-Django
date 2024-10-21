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

# Константы для авторизации в API
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
    """
    Аутентификация и получение session ID для дальнейших запросов.

    :param login: Логин пользователя для API
    :param password: Пароль пользователя для API
    :return: Заголовок с session ID для авторизации в следующих запросах
    """
    auth_url = f'{ENDPOINT}/auth/login'
    login_data = {'login': login, 'password': password}

    # Отправляем запрос на аутентификацию и получаем session ID
    response = requests.post(url=auth_url, headers=HEADERS_AUTH, json=login_data)
    response.raise_for_status()

    # Возвращаем session ID для последующего использования в запросах
    session_id = {'x-session-id': response.json()['session']['id']}
    return session_id


def fetch_generation_name(mark_code: str, model_code: str, generation_id: str, session_id: Dict[str, str]) -> str:
    """
    Извлечение названия поколения через API. Если название не указано, возвращаем временной диапазон.

    :param mark_code: Код марки
    :param model_code: Код модели
    :param generation_id: ID поколения
    :param session_id: Сессия пользователя
    :return: Название поколения или временной диапазон в формате "2020 - 2024"
    """
    # Формируем параметр для API-запроса
    param = f"{mark_code}#{model_code}#{generation_id}" if generation_id else f"{mark_code}#{model_code}"

    try:
        # Получаем структуру каталога из API
        api_result = fetch_catalog_structure(param, session_id)

        # Ищем в структуре нужный уровень данных (GENERATION_LEVEL)
        for breadcrumb in api_result.get('breadcrumbs', []):
            if breadcrumb.get('meta_level') == 'GENERATION_LEVEL':
                generation_entity = breadcrumb.get('entities', [{}])[0]
                generation_name = generation_entity.get('name', '').strip()

                if not generation_name:
                    # Если название поколения не указано, используем временной диапазон
                    super_gen = generation_entity.get('super_gen', {})
                    year_start = super_gen.get('year_from', 'Unknown')
                    year_end = super_gen.get('year_to', 'н.в.')  # Если нет даты окончания, указываем "н.в."
                    generation_name = f"{year_start} - {year_end}"

                return generation_name

        # Если не найдено, возвращаем 'Unknown'
        return 'Unknown'
    except Exception as e:
        # Логируем ошибку и возвращаем 'Unknown'
        logger.red(f"Ошибка при извлечении названия поколения: {e}")
        return 'Unknown'


def fetch_catalog_structure(param: str, session_id: Dict[str, str], retries: int = 3) -> Dict:
    """
    Получение структуры каталога через API с повторными попытками в случае неудачи.

    :param param: Параметры для запроса
    :param session_id: Сессия пользователя
    :param retries: Количество попыток повторить запрос в случае ошибки
    :return: Ответ API в виде словаря
    """
    url = f'{ENDPOINT}/search/cars/breadcrumbs'
    headers = {**HEADERS_AUTH, **session_id}
    params = {'bc_lookup': param}

    for attempt in range(retries):
        try:
            # Выполняем запрос к API
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            # Возвращаем ответ в виде JSON
            return response.json()
        except requests.RequestException as e:
            status_code = None
            # Если доступен статус-код, извлекаем его из ответа
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                logger.yellow(
                    f"Ошибка запроса на попытке {attempt + 1}/{retries}. Статус-код: {status_code}. Ошибка: {e}")
            else:
                logger.red(f"Запрос завершился неудачно на попытке {attempt + 1}/{retries} без ответа: {e}")

            # Если ошибка связана с авторизацией (401), пробуем повторно аутентифицироваться
            if status_code == 401:
                logger.cyan("Ошибка 401: Неавторизованный доступ. Повторная аутентификация...")
                session_id = authenticate(LOGIN, PASSWORD)
                headers.update(session_id)

            # Экспоненциальная задержка перед повтором запроса
            if attempt < retries - 1:
                logger.yellow(f"Повторная попытка через {2 ** attempt} секунд(ы)...")
                time.sleep(2 ** attempt)
            else:
                # Если все попытки исчерпаны, логируем ошибку и выбрасываем исключение
                logger.red(
                    f"Не удалось получить данные после {retries} попыток. Последний статус-код: {status_code}. Ошибка: {e}")
                raise RuntimeError(f"Не удалось получить данные с API auto.ru: {e}")

def map_body_type(gear_type: str) -> str:
    """
    Преобразует тип привода из английского обозначения в русское.

    :param gear_type: Тип кузова (например, 'ALL_WHEEL_DRIVE')
    :return: Преобразованное название привода на русском (например, 'Полный')
    """
    # Маппинг типов привода на русский язык
    mapping = {
        'Внедорожник': 'Внедорожник',
        'FORWARD_CONTROL': 'Передний',
        'REAR_DRIVE': 'Задний'
    }
    # Возвращаем соответствующий тип привода или 'Unknown', если тип не найден
    return mapping.get(gear_type, 'Unknown')


def map_drive_type(gear_type: str) -> str:
    """
    Преобразует тип привода из английского обозначения в русское.

    :param gear_type: Тип привода (например, 'ALL_WHEEL_DRIVE')
    :return: Преобразованное название привода на русском (например, 'Полный')
    """
    # Маппинг типов привода на русский язык
    mapping = {
        'ALL_WHEEL_DRIVE': 'Полный',
        'FORWARD_CONTROL': 'Передний',
        'REAR_DRIVE': 'Задний'
    }
    # Возвращаем соответствующий тип привода или 'Unknown', если тип не найден
    return mapping.get(gear_type, 'Unknown')


def map_transmission_type(transmission: str) -> str:
    """
    Преобразует тип трансмиссии из английского обозначения в русское.

    :param transmission: Тип трансмиссии (например, 'MECHANICAL')
    :return: Преобразованное название трансмиссии на русском (например, 'Механика')
    """
    # Маппинг типов трансмиссий на русский язык
    mapping = {
        'MECHANICAL': 'Механика',
        'AUTOMATIC': 'Автомат',
        'ROBOT': 'Робот',
        'VARIATOR': 'Вариатор'
    }
    # Возвращаем соответствующий тип трансмиссии или 'Unknown', если тип не найден
    return mapping.get(transmission, 'Unknown')


def map_drive_type_short(drive: str) -> str:
    """
    Преобразует тип привода на сокращенное обозначение.

    :param drive: Полное название привода на русском (например, 'Полный')
    :return: Сокращенное обозначение привода (например, '4WD')
    """
    # Маппинг типов привода на сокращенные обозначения
    mapping = {
        'Полный': '4WD',
        'Задний': 'RWD',
        'Передний': 'FWD'
    }
    # Возвращаем сокращенное обозначение или 'Unknown', если тип не найден
    return mapping.get(drive, 'Unknown')


def map_transmission_type_short(transmission: str) -> str:
    """
    Преобразует тип трансмиссии на сокращенное обозначение.

    :param transmission: Полное название трансмиссии на русском (например, 'Механика')
    :return: Сокращенное обозначение трансмиссии (например, 'MT')
    """
    # Маппинг типов трансмиссий на сокращенные обозначения
    mapping = {
        'Механика': 'MT',
        'Автомат': 'AT',
        'Робот': 'AMT',
        'Вариатор': 'CVT'
    }
    # Возвращаем сокращенное обозначение или 'Unknown', если тип не найден
    return mapping.get(transmission, 'Unknown')


def map_engine_type(engine_type: str) -> str:
    """
    Преобразует тип двигателя из английского обозначения в русское.

    :param engine_type: Тип двигателя (например, 'DIESEL')
    :return: Преобразованное название двигателя на русском (например, 'Дизель')
    """
    # Маппинг типов двигателей на русский язык
    mapping = {
        'DIESEL': 'Дизель',
        'ELECTRO': 'Электро',
        'GASOLINE': 'Бензин',
        'HYBRID': 'Гибрид',
        'LPG': 'Газ'
    }
    # Возвращаем соответствующий тип двигателя или 'Unknown', если тип не найден
    return mapping.get(engine_type, 'Unknown')


def process_mark_element(mark_el: etree.Element) -> AutoruMark:
    """
    Обрабатывает элемент XML марки и возвращает экземпляр AutoruMark.

    :param mark_el: XML элемент марки
    :return: Экземпляр модели AutoruMark
    """
    return AutoruMark(
        code_mark_level=mark_el.find('code').text,
        id_mark_level=mark_el.get('id'),
        name=mark_el.get('name'),
    )


def process_model_element(model_el: etree.Element, mark_instance: AutoruMark) -> AutoruModel:
    """
    Обрабатывает элемент XML модели и возвращает экземпляр AutoruModel.

    :param model_el: XML элемент модели
    :param mark_instance: Экземпляр марки AutoruMark
    :return: Экземпляр модели AutoruModel
    """
    model_name = model_el.get('name').split(',')[0]  # Извлекаем имя модели без дополнительных данных
    return AutoruModel(
        code_model_level=model_el.find('model').text,
        id_folder=model_el.get('id'),
        mark=mark_instance,
        name=model_name,
    )


def process_generation_element(model_el: etree.Element, model_instance: AutoruModel,
                               session_id: Dict[str, str]) -> AutoruGeneration:
    """
    Обрабатывает элемент XML поколения и возвращает экземпляр AutoruGeneration.

    :param model_el: XML элемент модели
    :param model_instance: Экземпляр модели AutoruModel
    :param session_id: Сессия пользователя для запросов к API
    :return: Экземпляр поколения AutoruGeneration
    """
    generation_code = model_el.find('generation').text
    # Если в названии модели указано поколение, извлекаем его
    if ',' in model_el.get('name'):
        generation_name = model_el.get('name').split(',', 1)[1]
    else:
        # Иначе получаем поколение через API
        generation_name = fetch_generation_name(model_instance.mark.code_mark_level,
                                                model_instance.code_model_level,
                                                generation_code, session_id)
    return AutoruGeneration(
        id_generation_level=int(generation_code),
        model=model_instance,
        name=generation_name.strip()
    )


def process_modification_element(modification_el: etree.Element, mark_instance: AutoruMark,
                                 model_instance: AutoruModel, generation_instance: AutoruGeneration,
                                 session_id: Dict[str, str]) -> Union[AutoruModification, None]:
    """
    Обрабатывает элемент XML модификации и возвращает экземпляр AutoruModification.

    :param modification_el: XML элемент модификации
    :param mark_instance: Экземпляр марки AutoruMark
    :param model_instance: Экземпляр модели AutoruModel
    :param generation_instance: Экземпляр поколения AutoruGeneration
    :param session_id: Сессия пользователя для запросов к API
    :return: Экземпляр модификации AutoruModification или None в случае ошибки
    """
    # Формируем параметры для запроса к API по модификации
    param = (f"{mark_instance.code_mark_level}#"
             f"{model_instance.code_model_level}#"
             f"{generation_instance.id_generation_level}#"
             f"{modification_el.find('configuration_id').text}#"
             f"{modification_el.find('tech_param_id').text}")

    try:
        # Получаем структуру каталога через API
        api_result = fetch_catalog_structure(param, session_id)

        # Извлекаем технические параметры модификации
        tech_params = next(item for item in api_result['breadcrumbs'][0]['entities']
                           if item['id'] == modification_el.find('tech_param_id').text)

        # Инициализация параметров мощности и ёмкости батареи
        power_hp = power_kw = 0
        battery_capacity = 0

        # Определяем тип двигателя
        engine_type = map_engine_type(tech_params['tech_params']['engine_type'])

        if engine_type == 'Электро':
            # Для электродвигателей используем мощность в кВт и ёмкость батареи
            power_kw = int(float(tech_params['tech_params'].get('power_kvt', 0)))
            battery_capacity = float(tech_params['tech_params'].get('battery_capacity', 0))
        else:
            # Для остальных типов двигателей используем мощность в лошадиных силах
            power_hp = int(tech_params['tech_params'].get('power', 0))

        # Определяем года начала и окончания производства
        years_from = tech_params['tech_params'].get('year_start', None)
        years_to = tech_params['tech_params'].get('year_stop', None)
        if years_to is None or years_to == 0:
            years_to = datetime.now().year  # Если нет даты окончания, используем текущий год

        # Определяем тип привода, коробки передач и объём двигателя
        drive_type = map_drive_type(tech_params['tech_params']['gear_type'])
        drive_type_short = map_drive_type_short(drive_type)
        transmission_type = map_transmission_type(tech_params['tech_params']['transmission'])
        transmission_type_short = map_transmission_type_short(transmission_type)
        engine_volume_liters = round(tech_params['tech_params'].get('displacement', 0) / 1000, 1)

        configuration = next(item for item in api_result['breadcrumbs'][1]['entities']
                             if item['id'] == modification_el.find('configuration_id').text)
        doors = configuration['configuration']['doors_count']

        # Формируем короткое название модификации
        short_name = (f"{engine_volume_liters} "
                      f"{power_hp if power_hp else power_kw} "
                      f"{'л.с.' if power_hp else 'кВт'} "
                      f"{drive_type_short} "
                      f"{engine_type} "
                      f"{transmission_type_short}")

        # Возвращаем экземпляр модификации
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
    """
    Обрабатывает элемент XML комплектации и возвращает экземпляр AutoruComplectation.

    :param complectation_el: XML элемент комплектации
    :param modification_instance: Экземпляр модификации, к которой принадлежит комплектация
    :return: Экземпляр модели AutoruComplectation или None, если ID комплектации отсутствует
    """
    # Извлекаем ID комплектации из XML
    id_complectation = complectation_el.get('id')

    # Если ID комплектации отсутствует, пропускаем этот элемент
    if not id_complectation:
        logger.yellow(f"Пропущена комплектация из-за отсутствия id_complectation_autoru.")
        return None

    # Извлекаем название комплектации и создаем экземпляр AutoruComplectation
    complectation_name = complectation_el.text.strip() if complectation_el.text is not None else ''
    return AutoruComplectation(
        id_complectation_autoru=id_complectation,
        modification=modification_instance,
        name=complectation_name
    )


def parse_xml_file(xml_file: bytes, session_id: Dict[str, str]) -> Dict[
    str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]:
    """
    Парсит XML файл и возвращает данные для вставки в базу данных.

    :param xml_file: XML файл в байтовом формате
    :param session_id: Сессия пользователя для запросов к API
    :return: Словарь с данными для вставки (марки, модели, поколения, модификации, комплектации)
    """
    # Инициализация словаря для хранения данных, которые будут вставлены в базу данных
    data_to_insert = {
        'marks': [],
        'models': [],
        'generations': [],
        'modifications': [],
        'complectations': []
    }

    # Инициализация переменной для отслеживания времени обработки марок
    mark_times = []

    # Парсим XML файл и получаем корневой элемент
    root = etree.fromstring(xml_file)
    total_marks = len(root.findall('./mark'))  # Общее количество марок в XML

    # Итерация по каждой марке
    for mark_index, mark_el in enumerate(root.iterfind('./mark'), 1):
        mark_start = time.perf_counter()  # Начало отсчета времени обработки марки

        # Обрабатываем элемент марки и добавляем его в список для вставки
        mark_instance = process_mark_element(mark_el)
        data_to_insert['marks'].append(mark_instance)
        logger.green(f"Идёт обработка марки {mark_index}/{total_marks}: {mark_instance.name}")

        # Итерация по моделям внутри марки
        for model_el in mark_el.iterfind('./folder'):
            model_instance = process_model_element(model_el, mark_instance)
            data_to_insert['models'].append(model_instance)

            # Обрабатываем поколение модели и добавляем его в список для вставки
            generation_instance = process_generation_element(model_el, model_instance, session_id)
            data_to_insert['generations'].append(generation_instance)

            # Итерация по модификациям внутри модели
            for modification_el in model_el.iterfind('./modification'):
                modification_instance = process_modification_element(modification_el, mark_instance, model_instance,
                                                                     generation_instance, session_id)
                if modification_instance:
                    data_to_insert['modifications'].append(modification_instance)

                    # Итерация по комплектациям внутри модификации
                    for complectation_el in modification_el.iterfind('./complectations/complectation'):
                        complectation_instance = process_complectation_element(complectation_el, modification_instance)
                        if complectation_instance:
                            data_to_insert['complectations'].append(complectation_instance)

        # Завершаем отсчет времени обработки марки
        mark_end = time.perf_counter()
        mark_times.append(mark_end - mark_start)
        logger.blue(f"Завершена обработка марки {mark_index}/{total_marks}: {mark_instance.name}")

        # Расчет среднего времени на обработку одной марки и оценка оставшегося времени
        avg_mark_time = sum(mark_times) / len(mark_times) if mark_times else 0
        remaining_marks = total_marks - mark_index
        estimated_time = avg_mark_time * remaining_marks
        logger.yellow(f"Среднее время на марку: {avg_mark_time:.2f} секунд")
        logger.yellow(f"Ожидаемое время завершения: {estimated_time / 60:.2f} минут")

    return data_to_insert


def bulk_insert_data(data_to_insert: Dict[
    str, List[Union[AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation]]]) -> None:
    """
    Выполняет массовую вставку данных в базу данных.

    :param data_to_insert: Словарь с данными для вставки (марки, модели, поколения, модификации, комплектации)
    """
    # Осуществляем вставку данных в атомарной транзакции для обеспечения целостности данных
    with transaction.atomic():
        for name, objects in data_to_insert.items():
            if objects:
                model_name = f'Autoru{name.capitalize()[:-1]}'  # Формируем название модели на основе ключа
                model = globals()[model_name]  # Получаем модель из глобального пространства имен
                model.objects.bulk_create(objects)  # Выполняем массовую вставку объектов
                logger.purple(f"Inserted {len(objects)} records into {model_name}")


def clear_tables() -> None:
    """
    Очищает все таблицы перед вставкой новых данных.

    Удаляет все записи из таблиц: AutoruMark, AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation.
    """
    AutoruMark.objects.all().delete()
    AutoruModel.objects.all().delete()
    AutoruGeneration.objects.all().delete()
    AutoruModification.objects.all().delete()
    AutoruComplectation.objects.all().delete()
    logger.red("Все таблицы очищены")


class Command(BaseCommand):
    """
    Команда для парсинга данных из XML-файла и вставки их в базу данных.
    """

    help = 'Парсинг данных из XML-файла и сохранение их в базе данных.'

    def handle(self, *args, **kwargs):
        """
        Основная логика команды.
        - Выполняется аутентификация.
        - Загружается и парсится XML-файл.
        - Очистка таблиц базы данных.
        - Вставка данных через bulk_create.
        """
        # Аутентификация и получение session_id
        session_id = authenticate(LOGIN, PASSWORD)

        # Скачивание XML-файла с данными
        xml_link = 'https://auto-export.s3.yandex.net/auto/price-list/catalog/cars.xml'
        response = requests.get(xml_link)
        xml_file = response.content

        # Засекаем общее время выполнения процесса
        total_start = time.perf_counter()

        # Очистка всех таблиц перед вставкой новых данных
        clear_tables()

        # Парсинг XML файла и получение данных для вставки
        data_to_insert = parse_xml_file(xml_file, session_id)

        # Вставка данных в базу
        bulk_insert_data(data_to_insert)

        # Логирование общего времени выполнения
        total_end = time.perf_counter()
        logger.green("Process completed successfully")
        logger.green(f"Total time: {total_end - total_start:.2f} seconds")
        minutes = (total_end - total_start) // 60
        logger.green(f"Total time: {minutes} minutes")
