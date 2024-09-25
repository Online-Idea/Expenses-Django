import re
from time import time

import requests
from django.core.management.base import BaseCommand
from lxml import etree
from django.db import transaction
from lxml.etree import Element
from requests import Response
from libs.avito.models import *
from utils.colored_logger import ColoredLogger
from utils.clear_space import clear_space

# ANSI код для цвета текста
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


def process_name(name):
    if 'hyb' in name:
        return name.replace('hyb', ' Hybrid')
    return name


def clear_generation_name(name):
    # Удаляет годы в формате (2016—2020) из названия поколения
    name = re.sub(r'\s*\(\d{4}—\d{4}\)', '', name).strip().title()
    # Нормализует римские цифры
    name = normalize_roman_numerals(name)
    return name


def normalize_roman_numerals(name):
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
    # Замена некорректных римских цифр на корректные
    for incorrect, correct in roman_numerals.items():
        name = re.sub(incorrect, correct, name, flags=re.IGNORECASE)
    return name


def procces_modification(**kwargs) -> AvitoModification:
    """
    Обработка данных модификации перед сохранением.

    :param kwargs: Именованные аргументы с данными модификации.
    :return: Созданный экземпляр AvitoModification.
    """
    try:
        # Проверка и преобразование объема двигателя
        if 'engine_volume' in kwargs:
            engine_volume = kwargs['engine_volume']
            if re.match(r'^\d{3,4}$', engine_volume):
                engine_volume = round(int(engine_volume) / 1000, 1)

        # Преобразование типа привода
        if 'drive' in kwargs:
            drive_mapping = {
                AvitoModification.Drive.FRONT: 'FWD',
                AvitoModification.Drive.REAR: 'RWD',
                AvitoModification.Drive.FULL: '4WD'
            }
            drive = drive_mapping[kwargs['drive']]

        # Получение названия трансмиссии
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
            kwargs['power_hp'] = 0  # Обнуляем мощность в л.с., если двигатель электрический
        else:
            kwargs['power_hp'] = kwargs['power']
            kwargs['power_kw'] = 0  # Обнуляем мощность в кВт, если двигатель не электрический
            kwargs['battery_capacity'] = 0

        # Формирование краткого названия модификации
        kwargs['short_name'] = (f'{engine_volume} {kwargs["power_hp"] if kwargs["power_hp"] else kwargs["power_kw"]} '
                                f'{"л.с." if kwargs["power_hp"] else "кВт"} {drive} '
                                f'{kwargs["engine_type"]} {transmission}')

        kwargs['clients_name'] = process_name(kwargs['name'])
        kwargs['name'] = process_name(kwargs['name'])
        del kwargs['power']
        return AvitoModification(**kwargs)
    except KeyError as e:
        raise ValueError(f"Отсутствует обязательный аргумент: {e}")


class Command(BaseCommand):
    """
    Команда Django для импорта данных из XML-файла в базу данных.
    """

    help = 'Импорт данных из XML-файла'

    avito_models = [
        AvitoMark,
        AvitoModel,
        AvitoGeneration,
        AvitoModification,
        AvitoComplectation,
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
        :param kwargs: Аргументы командной строки.
        """
        # Ссылка на XML-файл Avito
        xml_link: str = 'http://autoload.avito.ru/format/Autocatalog.xml'
        response: Response = requests.get(xml_link)
        xml_file: bytes = response.content

        # Удаление старых данных перед парсингом
        self.clear_database()

        # Обработка XML-файла
        self.process_xml_file(xml_file)

        # Вставка новых данных в базу данных
        self.insert_data()

        self.stdout.write(self.style.SUCCESS("Обновление каталога Авито успешно!"))

    def clear_database(self) -> None:
        """
        Очистка всех записей из каждой таблицы в базе данных.
        """
        general_start = time()
        self.stdout.write(RED + f' {"Имя таблицы":<25}' + RESET + SLASH_CYAN +
                          RED + f'{"Кол-во записей":<18}' + RESET + SLASH_CYAN +
                          RED + f'{"Время удаления":<15}' + RESET)

        for model in reversed(self.avito_models):
            start = time()  # Время начала удаления записей из текущей модели
            entries = model.objects.all()
            amount_entries = len(entries)
            entries.delete()  # Удаление записей
            duration = f'{round(time() - start, 2)} сек'  # Время удаления записей из текущей модели

            # Вывод информации о количестве удаленных записей с окраской
            self.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
            self.stdout.write(
                WHITE + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
                WHITE + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
                WHITE + f'{duration:<15}' + RESET)

        # Вывод общего времени удаления всех записей
        self.stdout.write(self.style.WARNING(f'\nОбщее время очистки: {round(time() - general_start, 2)} сек \n'))

    def insert_data(self) -> None:
        """
        Вставка новых данных в базу данных.
        """
        with transaction.atomic():
            general_start = time()
            self.stdout.write(GREEN + f' {"Таблица:":<25}' + RESET + SLASH_CYAN +
                              GREEN + f'{"Кол-во записей":<18}' + RESET + SLASH_CYAN +
                              GREEN + f'{"Время вставки":<15}' + RESET)

            for model, list_objects in zip(self.avito_models, self.create_instance.values()):
                start = time()  # Время начала вставки записей в текущую модель
                entries = model.objects.bulk_create(list_objects)
                amount_entries = len(entries)
                duration = f'{round(time() - start, 2)} сек'  # Время вставки записей в текущую модель

                # Вывод информации о количестве вставленных записей с окраской
                self.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
                self.stdout.write(
                    WHITE + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
                    WHITE + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
                    WHITE + f'{duration:<15}' + RESET)

            # Вывод общего времени вставки всех записей
            self.stdout.write(self.style.WARNING(f'\nОбщее время вставки: {round(time() - general_start, 2)} сек \n'))

    def process_xml_file(self, xml_file: bytes) -> None:
        """
        Чтение и обработка XML-файла.

        :param xml_file: Содержимое XML-файла.
        """
        root: Element = etree.fromstring(xml_file)

        # Обработка каждого элемента марки
        for mark_el in root.iterfind('./Make'):
            mark_instance = AvitoMark(
                id_mark_avito=mark_el.get('id'),
                name=mark_el.get('name'),
            )
            self.create_instance['marks'].append(mark_instance)

            # Обработка каждой модели для данной марки
            for model_el in mark_el.iterfind('./Model'):
                model_instance = AvitoModel(
                    mark=mark_instance,
                    name=model_el.get('name'),
                    id_model_avito=model_el.get('id'),
                )
                self.create_instance['models'].append(model_instance)

                # Обработка каждого поколения для данной модели
                for generation_el in model_el.iterfind('./Generation'):
                    generation_instance = AvitoGeneration(
                        model=model_instance,
                        name=clear_generation_name(generation_el.get('name')),
                        id_generation_avito=generation_el.get('id'),
                    )
                    self.create_instance['generations'].append(generation_instance)

                    # Обработка каждой модификации для данного поколения
                    for modification_el in generation_el.iterfind('./Modification'):
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

                        # Обработка каждой комплектации для данной модификации
                        for complectation_el in modification_el.iterfind('./Complectations/Complectation'):
                            complectation_instance = AvitoComplectation(
                                id_complectation_avito=complectation_el.get('id'),
                                modification=modification_instance,
                                name=complectation_el.get('name')
                            )
                            self.create_instance['complectations'].append(complectation_instance)
