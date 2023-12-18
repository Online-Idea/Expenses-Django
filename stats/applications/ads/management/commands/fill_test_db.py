import pandas as pd
from django.db import transaction
from django.core.management.base import BaseCommand
from applications.ads.models import Ad
from libs.services.models import Mark, Model


class Command(BaseCommand):
    help = "Fill test data."

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str, help="Filename format .csv")

    def handle(self, *args, **kwargs):
        filename = kwargs.get("filename")

        self.clear_database()

        df = pd.read_csv(filename, sep=';', header=0, encoding='cp1251')
        ads_to_create = []

        with transaction.atomic():
            for _, row in df.iterrows():
                mark, created = Mark.objects.get_or_create(mark=row['Марка'])
                model, created = Model.objects.get_or_create(model=row['Модель'], mark=mark)

                ad = Ad(
                    mark=mark,
                    model=model,
                    configuration=row['Комплектация'],
                    price=row['Цена'],
                    body_type=row['Кузов'],
                    year=row['Год выпуска'],
                    color=row['Цвет'],
                    description=row['Описание'],
                    vin=row['Исходный VIN'],
                    photo=row['Фото']
                )
                ads_to_create.append(ad)

            Ad.objects.bulk_create(ads_to_create)

        self.stdout.write(self.style.SUCCESS("Database filled with test data"))

    def clear_database(self):
        # Очистка всех записей из каждой таблицы
        Mark.objects.all().delete()
        Model.objects.all().delete()
        Ad.objects.all().delete()
