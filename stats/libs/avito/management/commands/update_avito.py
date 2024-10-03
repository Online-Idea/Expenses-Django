import re
from time import time
import requests
from django.core.management.base import BaseCommand
from lxml import etree
from django.db import transaction
from lxml.etree import Element
from requests import Response
from libs.avito.models import AvitoMark, AvitoModel, AvitoGeneration, AvitoModification, AvitoComplectation
from utils.colored_logger import ColoredLogger
from utils.clear_space import clear_space

# ANSI коды для цветного текста в консоли
CYAN = '\033[96m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
RESET = '\033[0m'

# Разделитель с цветом
SLASH_CYAN = CYAN + ' | ' + RESET


def process_name(name: str) -> str:
    """
    Обрабатывает имя, заменяя сокращения на полные формы.

    :param name: Имя для обработки
    :return: Обработанное имя
    """
    if 'hyb' in name:
        return name.replace('hyb', ' Hybrid')
    return name


def clear_generation_name(name: str) -> str:
    """
    Очищает имя поколения, удаляя годы и нормализуя римские цифры.

    :param name: Имя поколения
    :return: Очищенное имя
    """
    # Удаляем годы в формате (2016—2020)
    name = re.sub(r'\s*\(\d{4}—\d{4}\)', '', name).strip().title()
    # Нормализуем римские цифры
    name = normalize_roman_numerals(name)
    return name


def normalize_roman_numerals(name: str) -> str:
    """
    Нормализует некорректные римские цифры в имени.

    :param name: Имя для нормализации
    :return: Имя с нормализованными римскими цифрами
    """
    # Словарь для замены некорректных римских цифр
    roman_numerals = {
        'Ii': 'II',
        'Iii': 'III',
        'Iv': 'IV',
        'Vi': 'VI',
        'Vii': 'VII',
        'Viii': 'VIII',
        'Ix': 'IX'
    }
    # Замена некорректных римских цифр
    for incorrect, correct in roman_numerals.items():
        name = re.sub(incorrect, correct, name, flags=re.IGNORECASE)
    return name


def procces_modification(**kwargs) -> AvitoModification:
    """
    Обрабатывает данные модификации перед сохранением в базу данных.

    :param kwargs: Именованные аргументы с данными модификации.
    :return: Экземпляр AvitoModification, готовый для сохранения.
    :raises ValueError: Если отсутствует обязательный аргумент.
    """
    try:
        # Проверка и преобразование объема двигателя
        if 'engine_volume' in kwargs:
            engine_volume = kwargs['engine_volume']
            if re.match(r'^\d{3,4}$', engine_volume):
                engine_volume = round(int(engine_volume) / 1000, 1)

        # Преобразование типа привода в краткую форму (например, 'FWD', 'RWD', '4WD')
        if 'drive' in kwargs:
            drive_mapping = {
                AvitoModification.Drive.FRONT: 'FWD',
                AvitoModification.Drive.REAR: 'RWD',
                AvitoModification.Drive.FULL: '4WD'
            }
            drive = drive_mapping[kwargs['drive']]

        # Получение краткой формы названия трансмиссии
        if 'transmission' in kwargs:
            transmission_mapping = {
                'Автомат': 'AT',
                'Робот': 'RWD',
                'Вариатор': 'CVT',
                'Механика': 'MT'
            }
            transmission = transmission_mapping[kwargs['transmission']]

        # Определение мощности в зависимости от типа двигателя
        engine_type = kwargs.get('engine_type')
        if engine_type == 'Электро':
            kwargs['power_kw'] = kwargs['power']
            kwargs['power_hp'] = 0  # Электродвигатель - мощность в л.с. отсутствует
        else:
            kwargs['power_hp'] = kwargs['power']
            kwargs['power_kw'] = 0  # Неэлектродвигатель - мощность в кВт отсутствует
            kwargs['battery_capacity'] = 0  # Емкость батареи не нужна для неэлектродвигателей

        # Формирование краткого названия модификации (например, '2.0 150 л.с. FWD Бензин AT')
        kwargs['short_name'] = (f'{engine_volume} {kwargs["power_hp"] if kwargs["power_hp"] else kwargs["power_kw"]} '
                                f'{"л.с." if kwargs["power_hp"] else "кВт"} {drive} '
                                f'{kwargs["engine_type"]} {transmission}')

        # Преобразование имени для клиентов и для базы данных
        kwargs['clients_name'] = process_name(kwargs['name'])
        kwargs['name'] = process_name(kwargs['name'])

        # Удаление лишнего поля power, чтобы избежать конфликта
        del kwargs['power']
        return AvitoModification(**kwargs)
    except KeyError as e:
        raise ValueError(f"Отсутствует обязательный аргумент: {e}")


class Command(BaseCommand):
    """
    Django команда для импорта данных из XML-файла в базу данных.

    Команда скачивает XML-файл, очищает старые данные в базе, обрабатывает новый файл и вставляет обновленные данные.
    """
    help = 'Импорт данных из XML-файла'

    # Модели, которые будут использоваться для вставки данных
    avito_models = [
        AvitoMark,
        AvitoModel,
        AvitoGeneration,
        AvitoModification,
        AvitoComplectation,
    ]

    # Словарь для хранения новых объектов перед их вставкой в базу данных
    create_instance = {
        'marks': [],
        'models': [],
        'generations': [],
        'modifications': [],
        'complectations': [],
    }

    def handle(self, *args, **kwargs) -> None:
        """
        Основной метод команды. Выполняет импорт данных.

        :param args: Аргументы командной строки (не используются).
        :param kwargs: Именованные аргументы командной строки (не используются).
        """
        # URL-адрес для загрузки XML-файла
        xml_link: str = 'http://autoload.avito.ru/format/Autocatalog.xml'
        response: Response = requests.get(xml_link)
        xml_file: bytes = response.content

        # Очистка старых данных из базы данных перед вставкой новых
        self.clear_database()

        # Обработка и парсинг XML-файла
        self.process_xml_file(xml_file)

        # Вставка новых данных в базу данных
        self.insert_data()

        # Вывод успешного завершения команды
        self.stdout.write(self.style.SUCCESS("Обновление каталога Авито успешно!"))

    def clear_database(self) -> None:
        """
        Очистка всех записей из каждой таблицы в базе данных.
        """
        # Засекаем общее время очистки базы данных
        general_start = time()
        # Заголовки таблиц для вывода в консоль
        self.stdout.write(RED + f' {"Имя таблицы":<25}' + RESET + SLASH_CYAN +
                          RED + f'{"Кол-во записей":<18}' + RESET + SLASH_CYAN +
                          RED + f'{"Время удаления":<15}' + RESET)

        # Удаляем записи в обратном порядке, чтобы избежать проблем с зависимостями
        for model in reversed(self.avito_models):
            start = time()  # Засекаем время начала удаления записей для текущей модели
            entries = model.objects.all()
            amount_entries = len(entries)
            entries.delete()  # Удаляем все записи
            duration = f'{round(time() - start, 2)} сек'  # Засекаем время удаления

            # Выводим информацию о количестве удаленных записей
            self.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
            self.stdout.write(
                WHITE + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
                WHITE + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
                WHITE + f'{duration:<15}' + RESET)

        # Выводим общее время очистки базы данных
        self.stdout.write(self.style.WARNING(f'\nОбщее время очистки: {round(time() - general_start, 2)} сек \n'))

    def insert_data(self) -> None:
        """
        Вставка новых данных в базу данных с использованием транзакций.
        """
        # Используем атомарные транзакции для вставки данных
        with transaction.atomic():
            general_start = time()  # Засекаем общее время вставки данных
            # Заголовки таблиц для вывода в консоль
            self.stdout.write(GREEN + f' {"Таблица:":<25}' + RESET + SLASH_CYAN +
                              GREEN + f'{"Кол-во записей":<18}' + RESET + SLASH_CYAN +
                              GREEN + f'{"Время вставки":<15}' + RESET)

            # Вставляем данные для каждой модели
            for model, list_objects in zip(self.avito_models, self.create_instance.values()):
                start = time()  # Засекаем время вставки для текущей модели
                entries = model.objects.bulk_create(list_objects)
                amount_entries = len(entries)
                duration = f'{round(time() - start, 2)} сек'  # Засекаем время вставки

                # Выводим информацию о количестве вставленных записей
                self.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
                self.stdout.write(
                    WHITE + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
                    WHITE + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
                    WHITE + f'{duration:<15}' + RESET)

            # Выводим общее время вставки данных
            self.stdout.write(self.style.WARNING(f'\nОбщее время вставки: {round(time() - general_start, 2)} сек \n'))

    def process_xml_file(self, xml_file: bytes) -> None:
        """
        Чтение и обработка XML-файла, создание объектов для вставки в базу данных.

        :param xml_file: Содержимое XML-файла в байтовом формате.
        """
        root: Element = etree.fromstring(xml_file)

        # Проход по каждому элементу марки
        for mark_el in root.iterfind('./Make'):
            # Создание объекта марки
            mark_instance = AvitoMark(
                id_mark_avito=mark_el.get('id'),
                name=mark_el.get('name'),
            )
            self.create_instance['marks'].append(mark_instance)

            # Проход по каждой модели внутри марки
            for model_el in mark_el.iterfind('./Model'):
                # Создание объекта модели
                model_instance = AvitoModel(
                    mark=mark_instance,
                    name=model_el.get('name'),
                    id_model_avito=model_el.get('id'),
                )
                self.create_instance['models'].append(model_instance)

                # Проход по каждому поколению внутри модели
                for generation_el in model_el.iterfind('./Generation'):
                    # Создание объекта поколения
                    generation_instance = AvitoGeneration(
                        model=model_instance,
                        name=clear_generation_name(generation_el.get('name')),
                        id_generation_avito=generation_el.get('id'),
                    )
                    self.create_instance['generations'].append(generation_instance)

                    # Проход по каждой модификации внутри поколения
                    for modification_el in generation_el.iterfind('./Modification'):
                        # Создание объекта модификации через обработку данных
                        modification_instance = procces_modification(
                            mark=mark_instance,
                            model=model_instance,
                            generation=generation_instance,
                            name=modification_el.get('name'),
                            id_modification_avito=modification_el.get('id'),
                            years_from=modification_el.find('YearFrom').text,
                            years_to=modification_el.find('YearTo').text,
                            engine_type=modification_el.find('FuelType').text,
                            drive=modification_el.find('DriveType').text,
                            transmission=modification_el.find('Transmission').text,
                            power=modification_el.find('Power').text,
                            engine_volume=modification_el.find('EngineSize').text,
                            body_type=modification_el.find('BodyType').text,
                            doors=modification_el.find('Doors').text
                        )
                        self.create_instance['modifications'].append(modification_instance)

                        # Проход по каждой комплектации внутри модификации
                        for complectation_el in modification_el.iterfind('./Complectations/Complectation'):
                            # Создание объекта комплектации
                            complectation_instance = AvitoComplectation(
                                id_complectation_avito=complectation_el.get('id'),
                                modification=modification_instance,
                                name=complectation_el.get('name')
                            )
                            self.create_instance['complectations'].append(complectation_instance)
