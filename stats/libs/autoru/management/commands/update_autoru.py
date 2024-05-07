import re
from time import time
from typing import List, Union

import requests
from django.core.management.base import BaseCommand
from lxml import etree
from django.db import transaction
from lxml.etree import Element
from requests import Response
from libs.autoru.models import *

CYAN = '\033[96m'  # ANSI код для белого цвета текста
GREEN = '\033[92m'
WHITE = '\033[97m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'  # ANSI код для сброса цвета текста

SLASH_CYAN = CYAN + ' | ' + RESET


def procces_folder(**kwargs) -> AutoruModel:
    """
    Обработка данных модели перед сохранением.

    :param kwargs: Именованные аргументы с данными тега <folder>.
    :return: Созданный экземпляр AutoruModel.
    """
    try:
        if kwargs.get('name', False):
            if kwargs['name'].find(',') != -1:
                name_model, generation = kwargs['name'].split(',')
                print(name_model + ' | ' + generation)
            else:
                print(kwargs['name'])
                name_model = kwargs['name']
    except KeyError as e:
        print('Ошибка ключа: ', e)


def procces_modification(**kwargs) -> AutoruModification:
    """
    Обработка данных модификации перед сохранением.

    :param kwargs: Именованные аргументы с данными модификации.
    :return: Созданный экземпляр Modification.
    """
    try:
        if 'engine_volume' in kwargs:
            engine_volume = kwargs['engine_volume']
            if re.match(r'^\d{3,4}$', engine_volume):
                engine_volume = round(int(engine_volume) / 1000, 1)

        if 'drive' in kwargs:
            drive_mapping = {
                AutoruModification.Drive.FRONT: 'FWD',
                AutoruModification.Drive.REAR: 'RWD',
                AutoruModification.Drive.FULL: '4WD'
            }
            drive = drive_mapping[kwargs['drive']]

        if 'transmission' in kwargs:
            transmission = AutoruModification.Transmission.get_name_attr(kwargs['transmission'])

        kwargs['short_name'] = (f'{engine_volume} {kwargs['power']}л.с. {drive} '
                                f'{kwargs['engine_type']} {transmission}')
        # 1.5 181 л.с. 4WD дизель AMT

        return AutoruModification(**kwargs)
    except KeyError as e:
        raise ValueError(f"Отсутствует обязательный аргумент: {e}")


class Command(BaseCommand):
    """
    Команда Django для импорта данных из XML-файла в базу данных.
    """

    help = 'Импорт данных из XML-файла'

    avito_models = [
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

        self.process_xml_file(xml_file)

        self.insert_data()

        self.stdout.write(self.style.SUCCESS("Обновление Авито успешно!"))

    def clear_database(self) -> None:
        """
        Очистка всех записей из каждой таблицы в базе данных.
        """
        general_start = time()
        self.stdout.write(CYAN + f' {"Имя таблицы":<25} | {"Кол-во записей":<18} | {"Время удаления":<15}' + RESET)
        for model in reversed(self.avito_models):
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
        with transaction.atomic():
            general_start = time()
            self.stdout.write(CYAN + f' {"Имя таблицы":<25} | {"Кол-во записей":<18} | {"Время вставки":<15}' + RESET)
            for model, list_objects in zip(self.avito_models, self.create_instance.values()):
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
        root: Element = etree.fromstring(xml_file)

        for mark_el in root.iterfind('./mark'):
            mark_instance = AutoruMark(
                code_mark_autoru=mark_el.find('code'),
                name=mark_el.get('name'),
            )
            self.create_instance['marks'].append(mark_instance)

            for model_el in mark_el.iterfind('./folder'):
                model_instance = procces_folder(
                    id_model_autoru=model_el.get('id'),
                    mark=mark_instance,
                    name=model_el.get('name'),
                )
                self.create_instance['models'].append(model_instance)

                for generation_el in model_el.iterfind('./Generation'):
                    generation_name: str = generation_el.get('name')
                    generation_instance = AutoruGeneration(
                        id_generation_avito=generation_el.get('id'),
                        model=model_instance,
                        name=generation_name,
                    )
                    self.create_instance['generations'].append(generation_instance)

                    for modification_el in generation_el.iterfind('./Modification'):
                        modification_instance = procces_modification(
                            id_modification_avito=modification_el.get('id'),
                            mark=mark_instance,
                            model=model_instance,
                            generation=generation_instance,
                            years_from=modification_el.find('YearFrom').text,
                            years_to=modification_el.find('YearTo').text,
                            name=modification_el.get('name'),
                            engine_type=modification_el.find('FuelType').text,
                            drive=modification_el.find('DriveType').text,
                            transmission=modification_el.find('Transmission').text,
                            power=modification_el.find('Power').text,
                            engine_volume=modification_el.find('EngineSize').text,
                            body_type=modification_el.find('BodyType').text,
                            doors=modification_el.find('Doors').text
                        )
                        self.create_instance['modifications'].append(modification_instance)

                        for complectation_el in modification_el.iterfind('./Complectations/Complectation'):
                            complectation_instance = AutoruComplectation(
                                id_complectation_avito=complectation_el.get('id'),
                                modification=modification_instance,
                                name=complectation_el.get('name')
                            )
                            self.create_instance['complectations'].append(complectation_instance)
