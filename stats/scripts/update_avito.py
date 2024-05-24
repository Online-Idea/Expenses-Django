import re
from time import time

import requests
from django.core.management.base import BaseCommand
from lxml import etree
from django.db import transaction
from lxml.etree import Element
from requests import Response
from libs.avito.models import *

# ANSI код для цвета текста

CYAN = '\033[96m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'

# ANSI код для сброса цвета текста
RESET = '\033[0m'

SLASH_CYAN = CYAN + ' | ' + RESET


def procces_modification(**kwargs) -> AvitoModification:
    """
    Обработка данных модификации перед сохранением.

    :param kwargs: Именованные аргументы с данными модификации.
    :return: Созданный экземпляр AvitoModification.
    """
    try:
        if 'engine_volume' in kwargs:
            engine_volume = kwargs['engine_volume']
            if re.match(r'^\d{3,4}$', engine_volume):
                engine_volume = round(int(engine_volume) / 1000, 1)

        if 'drive' in kwargs:
            drive_mapping = {
                AvitoModification.Drive.FRONT: 'FWD',
                AvitoModification.Drive.REAR: 'RWD',
                AvitoModification.Drive.FULL: '4WD'
            }
            drive = drive_mapping[kwargs['drive']]

        if 'transmission' in kwargs:
            transmission = AvitoModification.Transmission.get_name_attr(kwargs['transmission'])

        kwargs['short_name'] = (f'{engine_volume} {kwargs['power']}л.с. {drive} '
                                f'{kwargs['engine_type']} {transmission}')
        # 1.5 181 л.с. 4WD дизель AMT

        return AvitoModification(**kwargs)
    except KeyError as e:
        raise ValueError(f"Отсутствует обязательный аргумент: {e}")



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

def handle(*args, **kwargs) -> None:
    """
    Обработка выполнения команды.

    :param args: Не используется.
    :param kwargs: Аргументы командной строки.
    """
    # xml_link: str = kwargs['xml_link']
    xml_link = 'http://autoload.avito.ru/format/Autocatalog.xml'
    response: Response = requests.get(xml_link)
    xml_file: bytes = response.content
    # удаление старых данных перед парсингом
    clear_database(BaseCommand)

    process_xml_file(BaseCommand, xml_file)

    insert_data(BaseCommand)

    BaseCommand.stdout.write(BaseCommand.style.SUCCESS("Обновление Авито успешно!"))

def clear_database(BaseCommand) -> None:
    """
    Очистка всех записей из каждой таблицы в базе данных.
    """
    general_start = time()
    BaseCommand.stdout.write(RED + f' {"Имя таблицы":<25}' + RESET + SLASH_CYAN +
                      RED + f'{"Кол-во записей":<18}' + RESET + SLASH_CYAN +
                      RED + f'{"Время удаления":<15}' + RESET)
    for model in reversed(BaseCommand.avito_models):
        start = time()  # Время начала удаления записей из текущей модели
        entries = model.objects.all()
        amount_entries = len(entries)
        entries.delete()  # Удаление записей
        duration = f'{round(time() - start, 2)} сек'  # Время удаления записей из текущей модели
        # Вывод информации о количестве удаленных записей с окраской
        BaseCommand.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
        BaseCommand.stdout.write(
            WHITE + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
            WHITE + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
            WHITE + f'{duration:<15}' + RESET)

        # Вывод общего времени удаления всех записей
    BaseCommand.stdout.write(BaseCommand.style.WARNING(f'\nОбщее время очистки: {round(time() - general_start, 2)} сек \n'))

def insert_data(BaseCommand):
    with transaction.atomic():
        general_start = time()
        BaseCommand.stdout.write(GREEN + f' {"Таблица:":<25}' + RESET + SLASH_CYAN +
                                 GREEN + f'{"Кол-во записей":<18}' + RESET + SLASH_CYAN +
                                 GREEN + f'{"Время вставки":<15}' + RESET)
        for model, list_objects in zip(BaseCommand.avito_models, BaseCommand.create_instance.values()):
            start = time()  # Время начала удаления записей из текущей модели
            entries = model.objects.bulk_create(list_objects)
            amount_entries = len(entries)
            duration = f'{round(time() - start, 2)} сек'  # Время удаления записей из текущей модели
            # Вывод информации о количестве удаленных записей с окраской
            BaseCommand.stdout.write(CYAN + f' {"-" * 25} | {"-" * 18} | {"-" * 15}' + RESET)
            BaseCommand.stdout.write(
                WHITE + f' {model.__name__:<25}' + RESET + SLASH_CYAN +
                WHITE + f'{amount_entries:<18}' + RESET + SLASH_CYAN +
                WHITE + f'{duration:<15}' + RESET)

            # Вывод общего времени удаления всех записей
        BaseCommand.stdout.write(BaseCommand.style.WARNING(f'\nОбщее время вставки: {round(time() - general_start, 2)} сек \n'))

def process_xml_file(BaseCommand, xml_file: bytes) -> None:
    """
    Чтение и обработка XML-файла.
    Создаёт экземпляры даных и сохраняет в списки

    :param xml_file: Содержимое XML-файла.
    """
    root: Element = etree.fromstring(xml_file)

    for mark_el in root.iterfind('./Make'):
        mark_instance = AvitoMark(
            id_mark_avito=mark_el.get('id'),
            name=mark_el.get('name'),
        )
        create_instance['marks'].append(mark_instance)

        for model_el in mark_el.iterfind('./Model'):
            model_instance = AvitoModel(
                mark=mark_instance,
                name=model_el.get('name'),
                id_model_avito=model_el.get('id'),
            )

            create_instance['models'].append(model_instance)

            for generation_el in model_el.iterfind('./Generation'):
                generation_instance = AvitoGeneration(
                    model=model_instance,
                    name=generation_el.get('name'),
                    id_generation_avito=generation_el.get('id'),
                )
                create_instance['generations'].append(generation_instance)

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
                    create_instance['modifications'].append(modification_instance)

                    for complectation_el in modification_el.iterfind('./Complectations/Complectation'):
                        complectation_instance = AvitoComplectation(
                            id_complectation_avito=complectation_el.get('id'),
                            modification=modification_instance,
                            name=complectation_el.get('name')
                        )
                        create_instance['complectations'].append(complectation_instance)
def run():
    handle()