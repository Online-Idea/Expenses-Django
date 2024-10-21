from django.db.models import ForeignKey

from applications.mainapp.models import *
from django.db import models


class AvitoMark(AbstractMark):
    """
    Модель для хранения информации о марках автомобилей Avito.
    """
    id_mark_avito = models.IntegerField(verbose_name='id марки из xml файла авито')

    class Meta:
        db_table = 'avito_mark'
        verbose_name = 'Марка'
        verbose_name_plural = 'Марки'
        ordering = ['name']

    def __str__(self) -> str:
        """
        Возвращает строковое представление марки.

        :return: Название марки.
        """
        return self.name


class AvitoModel(AbstractModel):
    """
    Модель для хранения информации о моделях автомобилей Avito.
    """
    id_model_avito = models.IntegerField(verbose_name='id модели из xml файла авито')
    mark = models.ForeignKey('AvitoMark', on_delete=models.CASCADE, related_name='models',
                                           verbose_name='Ссылка на соответствующую марку автомобиля')

    class Meta:
        db_table = 'avito_model'
        verbose_name = 'Модель'
        verbose_name_plural = 'Модели'

    def __str__(self) -> str:
        """
        Возвращает строковое представление модели.

        :return: Название модели.
        """
        return self.name


class AvitoGeneration(AbstractGeneration):
    """
    Модель для хранения информации о поколениях автомобилей Avito.
    """
    id_generation_avito = models.IntegerField(verbose_name='id поколения из xml файла авито')
    model = models.ForeignKey(AvitoModel, on_delete=models.CASCADE, related_name='generations',
                                            verbose_name="Ссылка на соответствующую модель автомобиля")

    class Meta:
        db_table = 'avito_generation'
        verbose_name = 'Поколение'
        verbose_name_plural = 'Поколения'

    def __str__(self) -> str:
        """
        Возвращает строковое представление поколения.

        :return: Название поколения.
        """
        return self.name


class AvitoModification(AbstractModification):
    """
    Модель для хранения информации о модификациях автомобилей Avito.
    """
    id_modification_avito: int = models.IntegerField(verbose_name='id из xml файла авито')
    mark = models.ForeignKey(AvitoMark, on_delete=models.CASCADE,
                                           verbose_name="Марка к которой относится модификация")
    model = models.ForeignKey(AvitoModel, on_delete=models.CASCADE,
                                            verbose_name="Модель к которой относится модификация")
    generation = models.ForeignKey(AvitoGeneration, on_delete=models.CASCADE, related_name='modifications',
                                                 verbose_name="Поколение к которой относится модификация")
    mainapp_modification = models.ForeignKey(Modification, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Модификация')

    class Meta:
        db_table = 'avito_modification'
        verbose_name = 'Модификация'
        verbose_name_plural = 'Модификации'

    def __str__(self) -> str:
        """
        Возвращает строковое представление модификации.

        :return: Строка, включающая марку, модель, поколение и краткое название модификации.
        """
        return f'{self.mark} {self.model} {self.generation} {self.short_name}'


class AvitoComplectation(AbstractComplectation):
    """
    Модель для хранения информации о комплектациях автомобилей Avito.
    """
    id_complectation_avito: int = models.IntegerField(verbose_name='id комплектации из xml файла авито')
    modification: ForeignKey = models.ForeignKey(AvitoModification, on_delete=models.CASCADE, related_name='complectations',
                                                   verbose_name="Ссылка на соответствующую модификацию автомобиля", default=1)

    class Meta:
        db_table = 'avito_complectation'
        verbose_name = 'Комплектация'
        verbose_name_plural = 'Комплектации'

    def __str__(self) -> str:
        """
        Возвращает строковое представление комплектации.

        :return: Название комплектации.
        """
        return self.name
