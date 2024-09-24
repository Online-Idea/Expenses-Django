from time import sleep, time, perf_counter
from itertools import chain

from django.core.management.base import BaseCommand
from django.db import transaction

from libs.autoru.models import *
from utils.colored_logger import ColoredLogger
from libs.avito.models import *
from applications.mainapp.models import Mark, Model, Generation, Modification, Complectation
from applications.ads.models import *

logger = ColoredLogger(__name__)


class Command(BaseCommand):
    """
    Команда Django для импорта данных из XML-файла в базу данных.
    """

    help = 'Импорт данных из XML-файла'

    def handle(self, *args, **kwargs) -> None:
        """
        Обработка выполнения команды.

        :param args: Не используется.
        :param kwargs: Аргументы командной строки.
        """
        start = time()
        fill_main_database()
        end = time()
        print('Finished in {} seconds'.format(end - start))

        self.stdout.write(self.style.SUCCESS("Главная база обновлена!"))


create_instance = {
    'marks': [],
    'models': [],
    'generations': [],
    'modifications': [],
    'complectations': [],
}


def fill_main_database():
    Ad.objects.all().delete()
    Complectation.objects.all().delete()
    Modification.objects.all().delete()
    Generation.objects.all().delete()
    Model.objects.all().delete()
    Mark.objects.all().delete()
    logger.green(f'Clear DB')

    # avito_models = AvitoModel.objects.all()
    # avito_generations = AvitoGeneration.objects.all()
    # avito_modifications = AvitoModification.objects.all()
    # avito_complectations = AvitoComplectation.objects.all()
    #
    # autoru_models = AutoruModel.objects.all()
    # autoru_generations = AutoruGeneration.objects.all()
    # autoru_modifications = AutoruModification.objects.all()
    # autoru_complectations = AutoruComplectation.objects.all()

    # Загрузка данных из Avito и Autoru
    autoru_marks = AutoruMark.objects.all()
    avito_marks = AvitoMark.objects.all()
    unique_marks = {mark.name: mark for mark in avito_marks}
    unique_marks.update({mark.name: mark for mark in autoru_marks})

    logger.white(f'Начался цикл\n')
    amount_unique_marks = len(unique_marks)
    logger.white(f'Кол-во уникальных марок авито и авто.ру: {amount_unique_marks} \n')
    iteration_times = []
    # Создание уникальных записей в базе данных основного приложения
    for indx_mark, mark_name in enumerate(unique_marks):
        iteration_start_time = perf_counter()
        logger.green(f'  {indx_mark + 1}/{amount_unique_marks} марка:')
        logger.green(f'  "{mark_name}" - обрабатывается...')
        mark = Mark(
            name=mark_name
        )
        create_instance['marks'].append(mark)
        models_avito = AvitoModel.objects.filter(mark__name=mark_name)
        models_autoru = AutoruModel.objects.filter(mark__name=mark_name)
        model_for_marks = {instance.name: instance for instance in models_autoru}
        model_for_marks.update({instance.name: instance for instance in models_avito})
        amount_model_for_marks = len(model_for_marks)
        for indx_model, model_name in enumerate(model_for_marks):
            logger.blue(f'        {indx_model + 1}/{amount_model_for_marks} модель:')
            logger.blue(f'  ----- "{model_name}" - обрабатывается...')
            iteration_start_time_model = perf_counter()
            model = Model(
                name=model_name,
                mark=mark
            )
            create_instance['models'].append(model)
            generations_avito = AvitoGeneration.objects.filter(model__name=model_name)
            generations_autoru = AutoruGeneration.objects.filter(model__name=model_name)
            generations_for_model = {instance.name: instance for instance in
                                     generations_autoru}
            generations_for_model.update({instance.name: instance for instance in
                                          generations_avito})
            amount_generation_for_model = len(generations_for_model)
            for indx_generation, generation_name in enumerate(generations_for_model):
                iteration_start_time_generation = perf_counter()
                logger.cyan(f'               {indx_generation + 1}/{amount_generation_for_model} поколение:')
                logger.cyan(f'        ------ "{generation_name}" - обрабатывается...')
                generation = Generation(
                    name=generation_name,
                    model=model
                )
                create_instance['generations'].append(generation)

                modifications_avito = AvitoModification.objects.filter(generation__name=generation_name)
                modifications_autoru = AutoruModification.objects.filter(generation__name=generation_name)
                modifications_for_generation = {instance.name: instance for instance in
                                                modifications_autoru}
                modifications_for_generation.update({instance.name: instance for instance in
                                                     modifications_avito})
                for modification_name in modifications_for_generation:

                    modification_obj = modifications_for_generation[modification_name]
                    modification = Modification(
                        name=modification_obj.name,
                        years_from=modification_obj.years_from,
                        years_to=modification_obj.years_to,
                        clients_name=modification_obj.clients_name,
                        drive=modification_obj.drive,
                        engine_type=modification_obj.engine_type,
                        transmission=modification_obj.transmission,
                        power=modification_obj.power,
                        engine_volume=modification_obj.engine_volume,
                        body_type=modification_obj.body_type,
                        doors=modification_obj.doors,
                        battery_capacity=modification_obj.battery_capacity,
                        load_capacity=modification_obj.load_capacity,
                        mark=mark,
                        model=model,
                        generation=generation
                    )
                    create_instance['modifications'].append(modification)

                    complectations_avito = AvitoComplectation.objects.filter(modification__name=modification_name)
                    complectations_autoru = AutoruComplectation.objects.filter(modification__name=modification_name)
                    complectations_for_modification = {instance.name: instance for instance in
                                                       complectations_autoru}
                    complectations_for_modification.update({instance.name: instance for instance in
                                                            complectations_avito})
                    for complectation_name in complectations_for_modification:
                        create_instance['complectations'].append(Complectation(
                            name=complectation_name,
                            modification=modification
                        ))
                iteration_end_time_generation = perf_counter()
                time_generation = iteration_end_time_generation - iteration_start_time_generation
                logger.cyan(f'        ------ Обработка поколения: "{generation_name}" - завершена!')
                logger.cyan(f'        ------ Время обработки: {time_generation:.2f} сек.\n')
            iteration_end_time_model = perf_counter()
            time_model = iteration_end_time_model - iteration_start_time_model
            logger.magenta(f'  ----- Обработка модели: "{model_name}" - завершена!')
            logger.magenta(f'  ----- Время обработки: {time_model:.2f} сек.\n')
        iteration_end_time = perf_counter()
        iteration_time = iteration_end_time - iteration_start_time
        iteration_times.append(iteration_time)
        logger.green(f'  Обработка марки: "{mark_name}" - завершена!')
        logger.green(
            f'  Время обработки '
            f'{int(iteration_time // 60)} мин. {int(iteration_time % 60)} сек.\n')
        average_time = sum(iteration_times) / (indx_mark + 1)
        logger.red(f'Всего обработанно марок: {indx_mark + 1}')
        logger.red(f"Среднее время итерации: {average_time:.2f} секунд")
        amount_unique_marks -= 1
        logger.red(f'Осталось марок: {amount_unique_marks} \n\n ')

    with transaction.atomic():
        Mark.objects.bulk_create(create_instance['marks'])
        Model.objects.bulk_create(create_instance['models'])
        Generation.objects.bulk_create(create_instance['generations'])
        Modification.objects.bulk_create(create_instance['modifications'])
        Complectation.objects.bulk_create(create_instance['complectations'])


"""
Лучшее время 44 сек
"""


# class Command(BaseCommand):
#     """
#     Команда Django для импорта данных из XML-файла в базу данных.
#     """
#
#     help = 'Импорт данных из XML-файла'
#
#     def handle(self, *args, **kwargs) -> None:
#         """
#         Обработка выполнения команды.
#
#         :param args: Не используется.
#         :param kwargs: Аргументы командной строки.
#         """
#         start = time()
#         fill_main_database()
#         end = time()
#         print('Finished in {} seconds'.format(end - start))
#
#         self.stdout.write(self.style.SUCCESS("Главная база обновлена!"))
#
#
# create_instance = {
#     'marks': [],
#     'models': [],
#     'generations': [],
#     'modifications': [],
#     'complectations': [],
# }
#
#
# def fill_main_database():
#     Ad.objects.all().delete()
#     Complectation.objects.all().delete()
#     Modification.objects.all().delete()
#     Generation.objects.all().delete()
#     Model.objects.all().delete()
#     Mark.objects.all().delete()
#     print('Clear db')
#
#     avito_models = AvitoModel.objects.all()
#     avito_generations = AvitoGeneration.objects.all()
#     avito_modifications = AvitoModification.objects.all()
#     avito_complectations = AvitoComplectation.objects.all()
#
#     autoru_models = AutoruModel.objects.all()
#     autoru_generations = AutoruGeneration.objects.all()
#     autoru_modifications = AutoruModification.objects.all()
#     autoru_complectations = AutoruComplectation.objects.all()
#
#     # Загрузка данных из Avito и Autoru
#     autoru_marks = AutoruMark.objects.all()
#     avito_marks = AvitoMark.objects.all()
#     unique_marks = {mark.name: mark for mark in avito_marks}
#     unique_marks.update({mark.name: mark for mark in autoru_marks})
#
#     logger.white(f'Начался цикл\n')
#     amount_unique_marks = len(unique_marks)
#     logger.white(f'Кол-во уникальных марок авито и авто.ру: {amount_unique_marks} \n')
#     iteration_times = []
#     # Создание уникальных записей в базе данных основного приложения
#     for indx_mark, mark_name in enumerate(unique_marks):
#         iteration_start_time = perf_counter()
#         logger.green(f'  {indx_mark + 1}/{amount_unique_marks} марка: "{mark_name}" - обрабатывается...')
#         mark = Mark(
#             name=mark_name
#         )
#         create_instance['marks'].append(mark)
#         models_avito = avito_models.filter(mark__name=mark_name)
#         models_autoru = autoru_models.filter(mark__name=mark_name)
#         model_for_marks = {instance.name: instance for instance in models_autoru}
#         model_for_marks.update({instance.name: instance for instance in models_avito})
#         amount_model_for_marks = len(model_for_marks)
#         for indx_model, model_name in enumerate(model_for_marks):
#             logger.magenta(
#                 f'        {indx_model + 1}/{amount_model_for_marks} модель: "{model_name}" - обрабатывается...')
#             iteration_start_time_model = perf_counter()
#             model = Model(
#                 name=model_name,
#                 mark=mark
#             )
#             create_instance['models'].append(model)
#             generations_avito = avito_generations.filter(model__name=model_name)
#             generations_autoru = autoru_generations.filter(model__name=model_name)
#             generations_for_model = {instance.name: instance for instance in
#                                      chain(generations_autoru, generations_avito)}
#
#             amount_generation_for_model = len(generations_for_model)
#             for indx_generation, generation_name in enumerate(generations_for_model):
#                 iteration_start_time_generation = perf_counter()
#                 logger.cyan(
#                     f'               {indx_generation + 1}/{amount_generation_for_model} '
#                     f'поколение: "{generation_name}" - обрабатывается...')
#                 generation = Generation(
#                     name=generation_name,
#                     model=model
#                 )
#                 create_instance['generations'].append(generation)
#
#                 modifications_avito = avito_modifications.filter(generation__name=generation_name)
#                 modifications_autoru = autoru_modifications.filter(generation__name=generation_name)
#                 modifications_for_generation = {instane.name: instane for instane in
#                                                 chain(modifications_avito, modifications_autoru)}
#                 for modification_name in modifications_for_generation:
#
#                     modification_obj = modifications_for_generation[modification_name]
#                     modification = Modification(
#                         name=modification_obj.name,
#                         years_from=modification_obj.years_from,
#                         years_to=modification_obj.years_to,
#                         clients_name=modification_obj.clients_name,
#                         drive=modification_obj.drive,
#                         engine_type=modification_obj.engine_type,
#                         transmission=modification_obj.transmission,
#                         power=modification_obj.power,
#                         engine_volume=modification_obj.engine_volume,
#                         body_type=modification_obj.body_type,
#                         doors=modification_obj.doors,
#                         battery_capacity=modification_obj.battery_capacity,
#                         load_capacity=modification_obj.load_capacity,
#                         mark=mark,
#                         model=model,
#                         generation=generation
#                     )
#                     create_instance['modifications'].append(modification)
#
#                     complectations_avito = avito_complectations.filter(modification__name=modification_name)
#                     complectations_autoru = autoru_complectations.filter(modification__name=modification_name)
#                     complectations_for_modification = {instane.name: instane for instane in
#                                                        chain(complectations_avito, complectations_autoru)}
#                     for complectation_name in complectations_for_modification:
#                         create_instance['complectations'].append(Complectation(
#                             name=complectation_name,
#                             modification=modification
#                         ))
#                 iteration_end_time_generation = perf_counter()
#                 time_generation = iteration_end_time_generation - iteration_start_time_generation
#                 logger.cyan(
#                     f'               {indx_generation + 1}/{amount_generation_for_model}. '
#                     f'Обработка поколения "{generation_name}" для модели '
#                     f'{logger.magenta(f'"{model_name}"', return_value=True)} - завершена!')
#                 logger.cyan(f'               Обработалось за: {time_generation:.2f} сек.\n')
#             iteration_end_time_model = perf_counter()
#             time_model = iteration_end_time_model - iteration_start_time_model
#             logger.magenta(
#                 f'        {indx_model + 1}/{amount_model_for_marks}. '
#                 f'Обработка модели "{model_name}" для марки '
#                 f'{logger.green(f'"{mark_name}"', return_value=True)} - завершена!')
#             logger.magenta(f'        Время: {time_model:.2f} сек.\n')
#         iteration_end_time = perf_counter()
#         iteration_time = iteration_end_time - iteration_start_time
#         iteration_times.append(iteration_time)
#         logger.green(f'  {indx_mark + 1}/{amount_unique_marks}. Обработка марки "{mark_name}" - завершена!')
#         logger.green(
#             f'  Время '
#             f'{int(iteration_time // 60)} мин. {int(iteration_time % 60)} сек.\n')
#         average_time = sum(iteration_times) / (indx_mark + 1)
#         logger.red(f'Всего обработанно марок: {indx_mark + 1}')
#         logger.red(f"Среднее время итерации: {average_time:.2f} секунд")
#         amount_unique_marks -= 1
#         logger.red(f'Осталось марок: {amount_unique_marks} \n\n ')
#
#     with transaction.atomic():
#         Mark.objects.bulk_create(create_instance['marks'])
#         Model.objects.bulk_create(create_instance['models'])
#         Generation.objects.bulk_create(create_instance['generations'])
#         Modification.objects.bulk_create(create_instance['modifications'])
#         Complectation.objects.bulk_create(create_instance['complectations'])

# class Command(BaseCommand):
#     """
#     Команда Django для импорта данных из XML-файла в базу данных.
#     """
#
#     help = 'Импорт данных из XML-файла'
#
#     def handle(self, *args, **kwargs) -> None:
#         """
#         Обработка выполнения команды.
#
#         :param args: Не используется.
#         :param kwargs: Аргументы командной строки.
#         """
#         # start = time()
#         fill_main_database()
#         # end = time()
#         # print('Finished in {} seconds'.format(end - start))
#
#         self.stdout.write(self.style.SUCCESS("Главная база обновлена!"))
#
#
# create_instance = {
#     'marks': [],
#     'models': [],
#     'generations': [],
#     'modifications': [],
#     'complectations': [],
# }
#
#
# def fill_main_database():
#     start = time()
#
#     Ad.objects.all().delete()
#     Complectation.objects.all().delete()
#     Modification.objects.all().delete()
#     Generation.objects.all().delete()
#     Model.objects.all().delete()
#     Mark.objects.all().delete()
#     print('Clear db')
#
#     avito_models = AvitoModel.objects.all()
#     avito_generations = AvitoGeneration.objects.all()
#     avito_modifications = AvitoModification.objects.all()
#     avito_complectations = AvitoComplectation.objects.all()
#
#     autoru_models = AutoruModel.objects.all()
#     autoru_generations = AutoruGeneration.objects.all()
#     autoru_modifications = AutoruModification.objects.all()
#     autoru_complectations = AutoruComplectation.objects.all()
#
#     # Загрузка данных из Avito и Autoru
#     autoru_marks = AutoruMark.objects.all()
#     avito_marks = AvitoMark.objects.all()
#     unique_marks = {mark.name: mark for mark in avito_marks}
#     unique_marks.update({mark.name: mark for mark in autoru_marks})
#
#     logger.white(f'Начался цикл\n')
#     amount_unique_marks = len(unique_marks)
#     logger.white(f'Кол-во уникальных марок авито и авто.ру: {amount_unique_marks} \n')
#     iteration_times = []
#     # Создание уникальных записей в базе данных основного приложения
#     for indx_mark, mark_name in enumerate(unique_marks):
#         iteration_start_time = perf_counter()
#         logger.green(f'  {indx_mark + 1}/{amount_unique_marks} марка: "{mark_name}" - обрабатывается...')
#         mark = Mark(
#             name=mark_name
#         )
#         create_instance['marks'].append(mark)
#         models_avito = avito_models.filter(mark__name=mark_name)
#         models_autoru = autoru_models.filter(mark__name=mark_name)
#         model_for_marks = {instance.name: instance for instance in models_autoru}
#         model_for_marks.update({instance.name: instance for instance in models_avito})
#         amount_model_for_marks = len(model_for_marks)
#         for indx_model, model_name in enumerate(model_for_marks):
#             logger.magenta(
#                 f'        {indx_model + 1}/{amount_model_for_marks} модель: "{model_name}" - обрабатывается...')
#             iteration_start_time_model = perf_counter()
#             model = Model(
#                 name=model_name,
#                 mark=mark
#             )
#             create_instance['models'].append(model)
#             generations_avito = avito_generations.filter(model__name=model_name)
#             generations_autoru = autoru_generations.filter(model__name=model_name)
#             generations_for_model = {instance.name: instance for instance in
#                                      generations_autoru}
#             generations_for_model.update({instance.name: instance for instance in
#                                           generations_avito})
#
#             amount_generation_for_model = len(generations_for_model)
#             for indx_generation, generation_name in enumerate(generations_for_model):
#                 iteration_start_time_generation = perf_counter()
#                 logger.cyan(
#                     f'               {indx_generation + 1}/{amount_generation_for_model} '
#                     f'поколение: "{generation_name}" - обрабатывается...')
#                 generation = Generation(
#                     name=generation_name,
#                     model=model
#                 )
#                 create_instance['generations'].append(generation)
#
#                 modifications_avito = avito_modifications.filter(generation__name=generation_name)
#                 modifications_autoru = autoru_modifications.filter(generation__name=generation_name)
#                 modifications_for_generation = {instance.name: instance for instance in
#                                                 modifications_autoru}
#                 modifications_for_generation.update({instance.name: instance for instance in
#                                                      modifications_avito})
#                 for modification_name in modifications_for_generation:
#
#                     modification_obj = modifications_for_generation[modification_name]
#                     modification = Modification(
#                         name=modification_obj.name,
#                         years_from=modification_obj.years_from,
#                         years_to=modification_obj.years_to,
#                         clients_name=modification_obj.clients_name,
#                         drive=modification_obj.drive,
#                         engine_type=modification_obj.engine_type,
#                         transmission=modification_obj.transmission,
#                         power=modification_obj.power,
#                         engine_volume=modification_obj.engine_volume,
#                         body_type=modification_obj.body_type,
#                         doors=modification_obj.doors,
#                         battery_capacity=modification_obj.battery_capacity,
#                         load_capacity=modification_obj.load_capacity,
#                         mark=mark,
#                         model=model,
#                         generation=generation
#                     )
#                     create_instance['modifications'].append(modification)
#
#                     complectations_avito = avito_complectations.filter(modification__name=modification_name)
#                     complectations_autoru = autoru_complectations.filter(modification__name=modification_name)
#                     complectations_for_modification = {instance.name: instance for instance in
#                                                        complectations_autoru}
#                     complectations_for_modification.update({instance.name: instance for instance in
#                                                             complectations_avito})
#                     for complectation_name in complectations_for_modification:
#                         create_instance['complectations'].append(Complectation(
#                             name=complectation_name,
#                             modification=modification
#                         ))
#                 iteration_end_time_generation = perf_counter()
#                 time_generation = iteration_end_time_generation - iteration_start_time_generation
#                 logger.cyan(
#                     f'               {indx_generation + 1}/{amount_generation_for_model}. '
#                     f'Обработка поколения: "{generation_name}" для модели: '
#                     f'{logger.magenta(f'"{model_name}"', return_value=True)} - завершена!')
#                 logger.cyan(f'               Время: {logger.red(f'{time_generation:.2f}  сек.', return_value=True)}\n')
#             iteration_end_time_model = perf_counter()
#             time_model = iteration_end_time_model - iteration_start_time_model
#             logger.magenta(
#                 f'        {indx_model + 1}/{amount_model_for_marks}. '
#                 f'Обработка модели: "{model_name}" для марки: '
#                 f'{logger.green(f'"{mark_name}"', return_value=True)} - завершена!')
#             logger.magenta(f'        Время: {logger.red(f'{time_model:.2f} сек.', return_value=True)}\n')
#         iteration_end_time = perf_counter()
#         iteration_time = iteration_end_time - iteration_start_time
#         iteration_times.append(iteration_time)
#         logger.green(f'  {indx_mark + 1}/{amount_unique_marks}. Обработка марки: "{mark_name}" - завершена!')
#         logger.green(
#             f'  Время: '
#             f'{int(iteration_time // 60)} мин. {int(iteration_time % 60)} сек.\n')
#         average_time = sum(iteration_times) / (indx_mark + 1)
#         logger.red(f'Всего обработанно марок: {indx_mark + 1}')
#         logger.red(f'Текущее общее время: {(time() - start) // 60} мин')
#         logger.red(f"Среднее время итерации: {average_time:.2f} секунд")
#         logger.red(f'Осталось марок: {amount_unique_marks - (indx_mark + 1)} \n\n ')
#
#     with transaction.atomic():
#         Mark.objects.bulk_create(create_instance['marks'])
#         Model.objects.bulk_create(create_instance['models'])
#         Generation.objects.bulk_create(create_instance['generations'])
#         Modification.objects.bulk_create(create_instance['modifications'])
#         Complectation.objects.bulk_create(create_instance['complectations'])
