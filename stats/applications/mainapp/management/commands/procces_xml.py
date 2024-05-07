import re
from typing import List

import requests
from django.core.management.base import BaseCommand
from lxml import etree
from django.db import transaction
from lxml.etree import Element

from applications.ads.models import Ad
from applications.mainapp.models import Mark, Model, Generation, Modification, Complectation


def procces_modification(**kwargs) -> Modification:
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
                Modification.Drive.FRONT: 'FWD',
                Modification.Drive.REAR: 'RWD',
                Modification.Drive.FULL: '4WD'
            }
            drive = drive_mapping[kwargs['drive']]

        if 'transmission' in kwargs:
            transmission = Modification.Transmission.get_name_attr(kwargs['transmission'])

        kwargs['short_name'] = (f'{engine_volume} {kwargs['power']}л.с. {drive} '
                                f'{kwargs['engine_type']} {transmission}')
        # 1.5 181 л.с. 4WD дизель AMT

        return Modification(**kwargs)
    except KeyError as e:
        raise ValueError(f"Отсутствует обязательный аргумент: {e}")


class Command(BaseCommand):
    """
    Команда Django для импорта данных из XML-файла в базу данных.
    """

    help = 'Импорт данных из XML-файла'

    def add_arguments(self, parser) -> None:
        """
        Определение аргументов командной строки.

        :param parser: Парсер для аргументов командной строки.
        """
        parser.add_argument('xml_link', type=str, help='Path to XML file')

    def handle(self, *args, **kwargs) -> None:
        """
        Обработка выполнения команды.

        :param args: Не используется.
        :param kwargs: Аргументы командной строки.
        """
        xml_file: str = kwargs['xml_link']
        # url = 'http://autoload.avito.ru/format/Autocatalog.xml'
        response = requests.get(xml_file)
        xml_file: bytes = response.content
        # удаление старых данных перед парсингом
        self.clear_database()

        process_xml_file(xml_file)

        self.stdout.write(self.style.SUCCESS("База данных по Авито - обновлена"))

    def clear_database(self) -> None:
        """
        Очистка всех записей из каждой таблицы в базе данных.
        """
        # Удаление всех записей из связанных таблиц в обратном порядке
        Ad.objects.all().delete()
        Complectation.objects.all().delete()
        Modification.objects.all().delete()
        Generation.objects.all().delete()
        Model.objects.all().delete()
        # Удаление всех записей из таблицы Mark
        Mark.objects.all().delete()
        self.stdout.write(self.style.NOTICE("Старые данные удаленны"))


def process_xml_file(xml_file: bytes) -> None:
    """
    Обработка XML-файла и сохранение данных в базе данных.

    :param xml_file: Содержимое XML-файла.
    """
    root: Element = etree.fromstring(xml_file)
    marks_to_create: List[Mark] = []
    models_to_create: List[Model] = []
    generations_to_create: List[Generation] = []
    modifications_to_create: List[Modification] = []
    complectations_to_create: List[Complectation] = []

    for mark_el in root.iterfind('./Make'):
        mark_name: str = mark_el.get('name')
        mark_instance = Mark(
            avito=mark_name,
            name=mark_name,
            teleph=mark_name,
            autoru=mark_name,
            drom=mark_name,
            human_name=mark_name
        )
        marks_to_create.append(mark_instance)

        for model_el in mark_el.iterfind('./Model'):
            model_name: str = model_el.get('name')
            model_instance = Model(
                mark=mark_instance,
                avito=model_name,
                name=model_name,
                teleph=model_name,
                autoru=model_name,
                drom=model_name,
                human_name=model_name
            )
            models_to_create.append(model_instance)
            for generation_el in model_el.iterfind('./Generation'):
                generation_name: str = generation_el.get('name')
                generation_instance = Generation(
                    model=model_instance,
                    avito=generation_name,
                    name=generation_name,
                    teleph=generation_name,
                    autoru=generation_name,
                    drom=generation_name,
                    human_name=generation_name
                )
                generations_to_create.append(generation_instance)
                for modification_el in generation_el.iterfind('./Modification'):
                    modification_instance = procces_modification(
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
                    modifications_to_create.append(modification_instance)
                    for complectation_el in modification_el.iterfind('./Complectations/Complectation'):
                        complectation_instance = Complectation(
                            modification=modification_instance,
                            name=complectation_el.get('name')
                        )
                        complectations_to_create.append(complectation_instance)

    with transaction.atomic():
        Mark.objects.bulk_create(marks_to_create)
        Model.objects.bulk_create(models_to_create)
        Generation.objects.bulk_create(generations_to_create)
        Modification.objects.bulk_create(modifications_to_create)
        Complectation.objects.bulk_create(complectations_to_create)
