from django.db import models

from libs.services.models import BaseModel, Client, Model, Mark, BodyTypeChoice, Colors


# TODO доделать эту если придут мысли что ещё добавить
class Salon(BaseModel):
    client = models.ManyToManyField(Client)
    name = models.CharField(max_length=255, verbose_name='Название')
    price_url = models.CharField(max_length=2000, verbose_name='Ссылка на прайс')
    datetime_updated = models.DateTimeField(verbose_name='Время последнего обновления')
    # дописать


class Ad(BaseModel):
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, related_name='ads', verbose_name='Марка')
    model = models.ForeignKey(Model, on_delete=models.PROTECT, related_name='ads', verbose_name='Модель')
    configuration = models.CharField(max_length=255, verbose_name='Комплектация')
    price = models.IntegerField(verbose_name='Цена')
    body_type = models.CharField(max_length=64, choices=BodyTypeChoice.choices, verbose_name='Кузов')
    year = models.IntegerField(verbose_name='Год выпуска')
    color = models.CharField(max_length=64, choices=Colors.choices, verbose_name='Цвет')
    description = models.CharField(blank=True, max_length=10500, verbose_name='Описание')
    vin = models.CharField(max_length=17, blank=True, verbose_name='Описание')
    photo = models.CharField(max_length=10500, blank=True, verbose_name='Ссылка на фото')

    def __str__(self):
        return f'{self.mark} | {self.model} | {self.price} | {self.vin}'

    class Meta:
        db_table = 'ads_ad'
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
