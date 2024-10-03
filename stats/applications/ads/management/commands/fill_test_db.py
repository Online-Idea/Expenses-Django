from datetime import datetime
from random import randint

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


from applications.accounts.models import Client, AccountClient
from applications.ads.models import Ad, Salon
from applications.mainapp.models import Mark, Model
from django.db import transaction
import pandas as pd
import argparse
from typing import Union
from faker import Faker
from django.utils import timezone
fake = Faker()




def replace_nan(value: Union[float, None]) -> Union[float, None]:
    """
    Замена NaN на None для корректного хранения в числовых полях базы данных.

    :param value: Значение для проверки.

    :return: Значение, замененное на None, если оно было NaN.
    """
    return None if pd.isna(value) else value


def capital_name(value: Union[str, None]) -> str:
    if value is not None and isinstance(value, str):
        return value.capitalize()


def divide_volume(value: Union[int, None]) -> Union[float, None]:
    if value is not None and isinstance(value, (int, float)):
        return round(value / 1000, 1)


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
            self.create_fake_salons(3)
            salons = Salon.objects.all()
            # Итерация по строкам DataFrame
            for _, row in df.iterrows():
                # Получение или создание экземпляров Mark и Model
                mark_instance, created = Mark.objects.get_or_create(name=row['Марка'])
                model_instance, created = Model.objects.get_or_create(name=row['Модель'], mark=mark_instance)
                # Создание экземпляра Ad с данными из файла CSV
                ad = Ad(
                    salon=salons[randint(0, len(salons) - 1)],
                    mark=mark_instance,
                    model=model_instance,
                    complectation=row['Комплектация'],
                    price=row['Цена'],
                    body_type=capital_name(row['Кузов']),
                    year=row['Год выпуска'],
                    color=capital_name(row['Цвет']),
                    description=row['Описание'],
                    original_vin=row['Исходный VIN'],
                    vin=replace_nan(row['VIN']),
                    photo=row['Фото'],
                    price_nds=capital_name(replace_nan(row['Цена с НДС'])),
                    engine_capacity=divide_volume(replace_nan(row['Объем двигателя'])),
                    power=row['Мощность'],
                    engine_type=capital_name(row['Тип двигателя']),
                    transmission=capital_name(row['Коробка передач']),
                    drive=capital_name(row['Привод']),
                    trade_in=replace_nan(row['Трейд-ин']),
                    credit=replace_nan(row['Кредит']),
                    insurance=replace_nan(row['Страховка']),
                    max_discount=row['Максималка'],
                    condition=capital_name(row['Состояние']),
                    run=replace_nan(row['Пробег']),
                    modification_code=row['Код модификации'],
                    complectation_code=row['Код комплектации'],
                    color_code=row['Код цвета'],
                    interior_code=row['Код интерьера'],
                    configuration_codes=row['Коды опций комплектации'],
                    stickers_autoru=replace_nan(row['Стикеры (авто.ру)']),
                    video=replace_nan(row['Ссылка на видео']),
                    configuration_autoru=row['Авто.ру Комплектация'],
                    telephone=row['Номер телефона'],
                    availability=capital_name(row['Наличие']),
                    id_model_autoru=replace_nan(row['ID модели авто.ру']),
                    id_modification_autoru=replace_nan(row['ID модификации авто.ру']),
                    modification_autoru=replace_nan(row['Модификация авто.ру']),
                    status=capital_name(row['Статус продажи']),
                    id_client=replace_nan(row['ID от клиента']),
                )
                ad.modification = ad.get_modification_display()
                ads_to_create.append(ad)

            Ad.objects.bulk_create(ads_to_create)

        self.stdout.write(self.style.SUCCESS("База данных обновлена"))

    def clear_database(self) -> None:
        """
        Очистка всех записей из каждой таблицы в базе данных.
        """
        Ad.objects.all().delete()
        Salon.objects.all().delete()
        # Model.objects.all().delete()
        # Mark.objects.all().delete()
        self.stdout.write(self.style.NOTICE("Старые данные удалены"))

    @staticmethod
    def create_fake_salons(amount: int) -> list:
        email = "admin@test.ru"
        User = get_user_model()
        account = User.objects.get(email=email)
        client = Client.objects.get(slug='admin')
        AccountClient.objects.create(account=account, client=client)

        # client = Client.objects.create(
        #     name=fake.first_name(),
        #     email=fake.email(),
        #     slug=fake.slug(),
        #     manager=fake.first_name(),
        #     charge_type=fake.random_element(),
        #     commission_size=fake.random_element(),
        #     teleph_id=fake.random_digit(),
        #     autoru_id=fake.random_digit(),
        #     avito_id=fake.random_digit(),
        #     drom_id=fake.random_digit(),
        #     is_staff=fake.boolean(),
        #     is_active=fake.boolean(),
        #     autoru_name=fake.random_element(),
        #     username=fake.first_name(),
        #     date_joined=fake.date(),
        # )

        for _ in range(amount):
            Salon.objects.create(
                client=client,
                name=fake.first_name(),
                price_url=fake.url(),
                datetime_updated=timezone.now(),
                working_hours=fake.date(),
                city=fake.city(),
                address=fake.address(),
                telephone=fake.phone_number(),
            )

