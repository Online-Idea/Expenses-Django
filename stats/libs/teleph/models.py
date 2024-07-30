from django.db import models

from libs.services.models import BaseModel
from applications.accounts.models import Client


class TelephCall(BaseModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='id клиента')
    datetime = models.DateTimeField(verbose_name='Дата и время')
    num_from = models.CharField(max_length=255, verbose_name='Исходящий')
    mark = models.CharField(max_length=255, null=True, verbose_name='Марка')
    model = models.CharField(max_length=255, null=True, verbose_name='Модель')
    target = models.CharField(max_length=255, null=True, verbose_name='Входящий')
    moderation = models.CharField(max_length=255, null=True, verbose_name='Модерация')
    call_price = models.FloatField(null=True, verbose_name='Стоимость')
    price_autoru = models.FloatField(null=True, verbose_name='Стоимость авто.ру')
    price_drom = models.FloatField(null=True, verbose_name='Стоимость drom')
    call_status = models.CharField(max_length=1000, null=True, verbose_name='Статус звонка')
    price_of_car = models.IntegerField(null=True, verbose_name='Цена автомобиля')
    color = models.CharField(max_length=500, null=True, verbose_name='Цвет')
    body = models.CharField(max_length=500, null=True, verbose_name='Кузов')
    drive_unit = models.CharField(max_length=500, null=True, verbose_name='Привод')
    engine = models.CharField(max_length=500, null=True, verbose_name='Двигатель')
    equipment = models.CharField(max_length=500, null=True, verbose_name='Комплектация')
    comment = models.CharField(max_length=1000, null=True, verbose_name='Остальные комментарии')

    def __str__(self):
        return f'{self.client} | {self.num_from} | {self.datetime}'

    class Meta:
        db_table = 'teleph_teleph_call'
        verbose_name = 'Телефония звонки'
        verbose_name_plural = 'Телефония звонки'
        ordering = ['datetime']

