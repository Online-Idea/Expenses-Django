from django.db import models

from applications.calls.models import Call
from libs.services.models import BaseModel, Mark, Model
from applications.accounts.models import Client


class AutoruCall(BaseModel):
    call = models.ForeignKey(Call, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Звонок')
    ad_id = models.CharField(max_length=255, null=True, verbose_name='id объявления')
    vin = models.CharField(max_length=17, null=True, verbose_name='VIN')
    client = models.ForeignKey(Client, to_field='autoru_id', on_delete=models.PROTECT, verbose_name='id клиента')
    num_from = models.CharField(max_length=255, verbose_name='Исходящий')
    num_to = models.CharField(max_length=255, verbose_name='Входящий')
    datetime = models.DateTimeField(verbose_name='Дата и время')
    duration = models.IntegerField(verbose_name='Длительность')
    mark = models.CharField(max_length=255, null=True, verbose_name='Марка')
    model = models.CharField(max_length=255, null=True, verbose_name='Модель')
    billing_state = models.CharField(max_length=255, null=True, verbose_name='Статус оплаты')
    billing_cost = models.FloatField(null=True, verbose_name='Стоимость')

    def __str__(self):
        return f'{self.client} | {self.num_from} | {self.datetime} | {self.duration}'

    class Meta:
        db_table = 'autoru_autoru_call'
        verbose_name = 'Авто.ру звонки'
        verbose_name_plural = 'Авто.ру звонки'
        ordering = ['datetime']


class AutoruProduct(BaseModel):
    ad_id = models.CharField(max_length=255, null=True, verbose_name='id объявления')
    vin = models.CharField(max_length=17, null=True, blank=True, verbose_name='VIN')
    client = models.ForeignKey(Client, to_field='autoru_id', on_delete=models.CASCADE, verbose_name='id клиента')
    date = models.DateField(verbose_name='Дата')
    mark = models.CharField(max_length=255, null=True, verbose_name='Марка')
    model = models.CharField(max_length=255, null=True, verbose_name='Модель')
    product = models.CharField(max_length=255, verbose_name='Услуга')
    sum = models.FloatField(verbose_name='Стоимость')
    count = models.IntegerField(verbose_name='Количество')

    def __str__(self):
        return f'{self.client} | {self.date} | {self.product}'

    class Meta:
        db_table = 'autoru_autoru_product'
        verbose_name = 'Авто.ру услуги'
        verbose_name_plural = 'Авто.ру услуги'
        ordering = ['date']


class AutoruCatalog(BaseModel):
    mark_id = models.IntegerField(blank=True, null=True, verbose_name='Марка id')
    mark_name = models.CharField(max_length=500, verbose_name='Марка имя')
    mark_code = models.CharField(max_length=500, verbose_name='Марка код')
    folder_id = models.IntegerField(verbose_name='folder_id')
    folder_name = models.CharField(max_length=500, verbose_name='folder_name')
    model_id = models.IntegerField(blank=True, null=True, verbose_name='Модель id')
    model_name = models.CharField(max_length=500, verbose_name='Модель имя')
    model_code = models.CharField(max_length=500, verbose_name='Модель код')
    generation_id = models.IntegerField(verbose_name='Поколение id')
    generation_name = models.CharField(max_length=500, verbose_name='Поколение имя')
    modification_id = models.IntegerField(verbose_name='Модификация id')
    modification_name = models.CharField(max_length=500, verbose_name='Модификация имя')
    configuration_id = models.IntegerField(verbose_name='configuration_id')
    tech_param_id = models.IntegerField(verbose_name='tech_param_id')
    body_type = models.CharField(max_length=500, verbose_name='Кузов')
    years = models.CharField(max_length=500, verbose_name='Года выпуска')
    complectation_id = models.IntegerField(blank=True, null=True, verbose_name='Комплектация id')
    complectation_name = models.CharField(max_length=500, blank=True, null=True, verbose_name='Комплектация имя')
    my_mark_id = models.ForeignKey(Mark, on_delete=models.PROTECT)
    my_model_id = models.ForeignKey(Model, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.mark_name} | {self.folder_name} | {self.modification_name} | {self.complectation_name}'

    class Meta:
        db_table = 'autoru_autoru_catalog'
        verbose_name = 'Авто.ру Каталог'
        verbose_name_plural = 'Авто.ру Каталог'


class AutoruRegion(BaseModel):
    autoru_region_id = models.IntegerField(verbose_name='Авто.ру регион id')
    name = models.CharField(max_length=500, verbose_name='Название региона')
    path = models.CharField(max_length=500)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'autoru_autoru_region'
        verbose_name = 'Авто.ру Регион'
        verbose_name_plural = 'Авто.ру Регионы'
