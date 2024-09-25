from pprint import pprint
from time import sleep, time, perf_counter
from itertools import chain

from django.core.management.base import BaseCommand
from django.db import transaction

from libs.autoru.models import *
from utils.colored_logger import ColoredLogger
from libs.avito.models import *
from applications.mainapp.models import Mark, Model, Generation, Modification, Complectation
from applications.ads.models import *
from applications.mainapp.models import Modification

class Command(BaseCommand):
    """
    Команда Django для импорта данных из XML-файла в базу данных.
    """

    help = 'Объединение каталогов Avito и Autoru'

    def handle(self, *args, **kwargs) -> None:
        """
        Обработка выполнения команды.

        :param args: Не используется.
        :param kwargs: Аргументы командной строки (исполняется без аргументов).
        """
        from django.db.models import Count
        def find_duplicate_generations():
            # Группируем по всем полям, кроме name из Generation
            duplicates = (
                Generation.objects.values(
                    'model__mark__name',
                    'model__name',
                    'modifications__years_from',
                    'modifications__years_to',
                    'modifications__drive',
                    'modifications__engine_type',
                    'modifications__transmission',
                    'modifications__power_hp',
                    # 'modifications__power_kw',
                    'modifications__engine_volume',
                    'modifications__body_type',
                    'modifications__doors',
                    'modifications__battery_capacity'
                )
                .annotate(name_count=Count('name'))
                .filter(name_count__gt=1)
                .order_by(
                    'model__mark__name',
                    'model__name',
                    'modifications__years_from',
                    'modifications__years_to',
                    'modifications__drive',
                    'modifications__engine_type',
                    'modifications__transmission',
                    'modifications__power_hp',
                    # 'modifications__power_kw',
                    'modifications__engine_volume',
                    'modifications__body_type',
                    'modifications__doors',
                    'modifications__battery_capacity'
                )
            )

            # Заголовок таблицы
            header = (
                f"{'ID':<5} {'Название':<30} {'Марка':<15} {'Модель':<15} "
                f"{'Годы':<15} {'Привод':<10} {'Тип двигателя':<15} {'Коробка передач':<20} "
                f"{'Мощность л.с.':<10} {'Мощность кВт.':<10} {'Объём двигателя':<15} {'Тип кузова':<15} "
                f"{'Количество дверей':<20} {'Ёмкость батареи':<20} {'Примечание':<10}"
            )
            print(header)
            print("=" * len(header))
            counter = 0
            for duplicate in duplicates:
                generation_duplicates = Generation.objects.filter(
                    model__mark__name=duplicate['model__mark__name'],
                    model__name=duplicate['model__name'],
                    modifications__years_from=duplicate['modifications__years_from'],
                    modifications__years_to=duplicate['modifications__years_to'],
                    modifications__drive=duplicate['modifications__drive'],
                    modifications__engine_type=duplicate['modifications__engine_type'],
                    modifications__transmission=duplicate['modifications__transmission'],
                    modifications__power_hp=duplicate['modifications__power_hp'],
                    # modifications__power_kw=duplicate['modifications__power_kw'],
                    modifications__engine_volume=duplicate['modifications__engine_volume'],
                    modifications__body_type=duplicate['modifications__body_type'],
                    modifications__doors=duplicate['modifications__doors'],
                    modifications__battery_capacity=duplicate['modifications__battery_capacity']
                ).values(
                    'id',
                    'name',
                    'model__mark__name',
                    'model__name',
                    'modifications__years_from',
                    'modifications__years_to',
                    'modifications__drive',
                    'modifications__engine_type',
                    'modifications__transmission',
                    'modifications__power_hp',
                    # 'modifications__power_kw',
                    'modifications__engine_volume',
                    'modifications__body_type',
                    'modifications__doors',
                    'modifications__battery_capacity'
                )
                counter += 1
                print(f"\n{counter}. Дубликаты для {duplicate['model__mark__name']} - {duplicate['model__name']}:")

                for gen in generation_duplicates:
                    print(
                        f"{gen['id']:<5} {gen['name']:<30} {gen['model__mark__name']:<15} {gen['model__name']:<15} "
                        f"{gen['modifications__years_from']} - {gen['modifications__years_to']:<5} "
                        f"{gen['modifications__drive']:<10} {gen['modifications__engine_type']:<15} "
                        f"{gen['modifications__transmission']:<20} {gen['modifications__power_hp']:<10} "
                        # f"{gen['modifications__transmission']:<20} {gen['modifications__power_hp']:<10} {gen['modifications__power_kw']:<10} "
                        f"{gen['modifications__engine_volume'] if gen['modifications__engine_volume'] is not None else '':<15} "
                        f"{gen['modifications__body_type']:<15} "
                        f"{gen['modifications__doors'] if gen['modifications__doors'] is not None else '':<20} "
                        f"{gen['modifications__battery_capacity'] if gen['modifications__battery_capacity'] is not None else '':<20} "
                        f"{'Дубликат':<10}"
                    )

        # Вызов функции для поиска и вывода дублей
        find_duplicate_generations()




