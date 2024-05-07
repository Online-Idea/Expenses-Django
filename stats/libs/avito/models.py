from applications.mainapp.models import *


class AvitoMark(AbstractMark):
    id_mark_avito = models.IntegerField(verbose_name='id из xml файла авито')

    class Meta:
        db_table = 'avito_mark'
        verbose_name = 'Марка'
        verbose_name_plural = 'Марки'
        ordering = ['name']

    def __str__(self): return self.name


class AvitoModel(AbstractModel):
    id_model_avito = models.IntegerField(verbose_name='id из xml файла авито')
    mark = models.ForeignKey('AvitoMark', on_delete=models.CASCADE, related_name='models',
                             verbose_name='Ссылка на марку')

    class Meta:
        db_table = 'avito_model'
        verbose_name = 'Модель'
        verbose_name_plural = 'Модели'

    def __str__(self): return self.name


class AvitoGeneration(AbstractGeneration):
    id_generation_avito = models.IntegerField(verbose_name='id из xml файла авито')
    model = models.ForeignKey(AvitoModel, on_delete=models.CASCADE, related_name='generations',
                              verbose_name="Ссылка на модель авто")

    class Meta:
        db_table = 'avito_generation'
        verbose_name = 'Поколение'
        verbose_name_plural = 'Поколения'

    def __str__(self): return self.name


class AvitoModification(AbstractModification):
    id_modification_avito = models.IntegerField(verbose_name='id из xml файла авито')
    mark = models.ForeignKey(AvitoMark, on_delete=models.CASCADE,
                             verbose_name="Марка к которой относится модификация")
    model = models.ForeignKey(AvitoModel, on_delete=models.CASCADE,
                              verbose_name="Модель к которой относится модификация")

    generation = models.ForeignKey(AvitoGeneration, on_delete=models.CASCADE, related_name='modifications',
                                   verbose_name="Поколение к которой относится модификация")

    class Meta:
        db_table = 'avito_modification'
        verbose_name = 'Модификация'
        verbose_name_plural = 'Модификации'

    def __str__(self):
        return f'{self.mark} {self.model} {self.generation} {self.short_name}'


class AvitoComplectation(AbstractComplectation):
    id_complectation_avito = models.IntegerField(verbose_name='id из xml файла авито')
    modification = models.ForeignKey(AvitoModification, on_delete=models.CASCADE, related_name='complectations',
                                     verbose_name="Модификация", default=1)

    class Meta:
        db_table = 'avito_complectation'
        verbose_name = 'Комплектация'
        verbose_name_plural = 'Комплектации'

    def __str__(self): return self.name
