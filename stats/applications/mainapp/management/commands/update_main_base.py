from time import time
from django.db import transaction
from django.core.management.base import BaseCommand

from libs.autoru.models import AutoruModel, AutoruGeneration, AutoruModification, AutoruComplectation
from libs.avito.models import AvitoModel, AvitoGeneration, AvitoModification, AvitoComplectation
from applications.ads.models import Ad
from applications.mainapp.models import Mark, Model, Generation, Modification, Complectation
from utils.colored_logger import ColoredLogger

logger = ColoredLogger(__name__)


class Command(BaseCommand):
    help = 'Объединение каталогов Avito и Autoru'

    def handle(self, *args, **kwargs) -> None:
        fill_main_database()
        self.stdout.write(self.style.SUCCESS("Главная база обновлена!"))


def fill_main_database() -> None:


    with transaction.atomic():
        Ad.objects.all().delete()
        Complectation.objects.all().delete()
        Modification.objects.all().delete()
        Generation.objects.all().delete()
        Model.objects.all().delete()
        Mark.objects.all().delete()

    logger.white('База данных очищена')

    avito_models = AvitoModel.objects.select_related('mark').all()
    autoru_models = AutoruModel.objects.select_related('mark').all()

    for avito_model in avito_models:
        mark_name = avito_model.mark.name.strip()
        model_name = avito_model.name.strip()

        mark_instance, _ = Mark.objects.get_or_create(name=mark_name)
        model_instance, _ = Model.objects.get_or_create(name=model_name, mark=mark_instance)

        avito_generations = AvitoGeneration.objects.filter(model=avito_model)
        for avito_generation in avito_generations:
            generation_name = avito_generation.name.strip()
            generation_instance, _ = Generation.objects.get_or_create(name=generation_name, model=model_instance)

            avito_modifications = AvitoModification.objects.filter(generation=avito_generation)
            for avito_modification in avito_modifications:
                modification_instance, _ = Modification.objects.get_or_create(
                    years_from=avito_modification.years_from,
                    years_to=avito_modification.years_to,
                    engine_type=avito_modification.engine_type,
                    transmission=avito_modification.transmission,
                    power_hp=avito_modification.power_hp,
                    power_kw=avito_modification.power_kw,
                    engine_volume=avito_modification.engine_volume,
                    mark=mark_instance,
                    model=model_instance,
                    generation=generation_instance,
                    drive=avito_modification.drive,
                    doors=avito_modification.doors,
                    defaults={
                        'name': avito_modification.name.strip(),
                        'clients_name': avito_modification.clients_name.strip(),
                        'body_type': avito_modification.body_type,
                        'doors': avito_modification.doors,
                        'battery_capacity': avito_modification.battery_capacity,
                        'load_capacity': avito_modification.load_capacity,
                    }
                )

                avito_complectations = AvitoComplectation.objects.filter(modification=avito_modification)
                for avito_complectation in avito_complectations:
                    Complectation.objects.get_or_create(
                        name=avito_complectation.name.strip() if avito_complectation.name is not None else avito_complectation.name,
                        modification=modification_instance
                    )
        print(f'Отработало Авито {mark_name} - {model_name}')
    for autoru_model in autoru_models:
        mark_name = autoru_model.mark.name.strip()
        model_name = autoru_model.name.strip()

        mark_instance, _ = Mark.objects.get_or_create(name=mark_name)
        model_instance, _ = Model.objects.get_or_create(name=model_name, mark=mark_instance)

        autoru_generations = AutoruGeneration.objects.filter(model=autoru_model)
        for autoru_generation in autoru_generations:
            generation_name = autoru_generation.name.strip()
            generation_instance, _ = Generation.objects.get_or_create(name=generation_name, model=model_instance)

            autoru_modifications = AutoruModification.objects.filter(generation=autoru_generation)
            for autoru_modification in autoru_modifications:
                modification_instance, _ = Modification.objects.get_or_create(
                    years_from=autoru_modification.years_from,
                    years_to=autoru_modification.years_to,
                    engine_type=autoru_modification.engine_type,
                    transmission=autoru_modification.transmission,
                    power_hp=autoru_modification.power_hp,
                    power_kw=autoru_modification.power_kw,
                    engine_volume=autoru_modification.engine_volume,
                    mark=mark_instance,
                    model=model_instance,
                    generation=generation_instance,
                    drive=autoru_modification.drive,
                    defaults={
                        'name': autoru_modification.name.strip(),
                        'clients_name': autoru_modification.clients_name.strip(),
                        'body_type': autoru_modification.body_type,
                        'doors': autoru_modification.doors,
                        'battery_capacity': autoru_modification.battery_capacity,
                        'load_capacity': autoru_modification.load_capacity,
                    }
                )

                autoru_complectations = AutoruComplectation.objects.filter(modification=autoru_modification)
                for autoru_complectation in autoru_complectations:
                    Complectation.objects.get_or_create(
                        name=autoru_complectation.name.strip() if autoru_complectation.name is not None else autoru_modification.name,
                        modification=modification_instance
                    )
        print(f'Отработало Авто.ру {mark_name} - {model_name}')
    logger.white('Главная база данных обновлена')
