from django.core.management.base import BaseCommand
from applications.ads.models import Ad
from libs.services.models import Mark, Model
from django.db import transaction
import pandas as pd
import argparse
from typing import Union


class Command(BaseCommand):
    """
    Команда Django для заполнения базы данных тестовыми данными из CSV файла.
    """

    help = "Заполнение тестовыми данными."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Определение аргументов командной строки.

        :param parser: Парсер для аргументов командной строки.
        """
        parser.add_argument("filename", type=str, help="Имя файла в формате .csv")

    def handle(self, *args, **kwargs) -> None:
        """
        Обработка выполнения команды.

        :param args: Не используется.
        :param kwargs: Аргументы командной строки.

        :raises ValueError: Если произошла ошибка во время обработки данных.
        """
        filename: str = kwargs.get("filename")

        # Очистка существующих данных в базе данных
        self.clear_database()

        # Чтение файла CSV в DataFrame
        df: pd.DataFrame = pd.read_csv(filename, sep=';', header=0, encoding='cp1251')

        ads_to_create = []

        # транзакция для атомарности
        with transaction.atomic():
            # Итерация по строкам DataFrame
            for _, row in df.iterrows():
                # Получение или создание экземпляров Mark и Model
                mark, created = Mark.objects.get_or_create(mark=row['Марка'])
                model, created = Model.objects.get_or_create(model=row['Модель'], mark=mark)

                # Создание экземпляра Ad с данными из файла CSV
                ad = Ad(
                    mark=mark,
                    model=model,
                    configuration=row['Комплектация'],
                    price=row['Цена'],
                    body_type=row['Кузов'],
                    year=row['Год выпуска'],
                    color=row['Цвет'],
                    description=row['Описание'],
                    original_vin=row['Исходный VIN'],
                    vin=row['VIN'],
                    photo=row['Фото'],
                    price_nds=row.get('Цена с НДС'),
                    engine_capacity=self.replace_nan(row.get('Объем двигателя')),
                    power=row.get('Мощность'),
                    engine_type=row.get('Тип двигателя'),
                    transmission=row.get('Коробка передач'),
                    drive=row.get('Привод'),
                    trade_in=self.replace_nan(row.get('Трейд-ин')),
                    credit=self.replace_nan(row.get('Кредит')),
                    insurance=self.replace_nan(row.get('Страховка')),
                    max_discount=row.get('Максималка'),
                    condition=row.get('Состояние'),
                    run=self.replace_nan(row.get('Пробег')),
                    modification_code=row.get('Код модификации'),
                    color_code=row.get('Код цвета'),
                    interior_code=row.get('Код интерьера'),
                    configuration_codes=row.get('Коды опций комплектации'),
                    stickers_autoru=row.get('Стикеры авто.ру'),
                    video=row.get('Ссылка на видео'),
                    configuration_autoru=row.get('Комплектация авто.ру')
                )

                ads_to_create.append(ad)

            # Массовое создание экземпляров Ad для оптимизации записи в базу данных
            Ad.objects.bulk_create(ads_to_create)

        self.stdout.write(self.style.SUCCESS("База данных заполнена тестовыми данными"))

    def clear_database(self) -> None:
        """
        Очистка всех записей из каждой таблицы в базе данных.
        """
        Ad.objects.all().delete()
        Model.objects.all().delete()
        Mark.objects.all().delete()

    def replace_nan(self, value: Union[float, None]) -> Union[float, None]:
        """
        Замена NaN на None для корректного хранения в числовых полях базы данных.

        :param value: Значение для проверки.

        :return: Значение, замененное на None, если оно было NaN.
        """
        return None if pd.isna(value) else value
