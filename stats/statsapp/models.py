from django.db import models


# Create your models here.
class Clients(models.Model):
    name = models.CharField(max_length=255, verbose_name='Имя')
    manager = models.CharField(max_length=255, null=True, verbose_name='Менеджер')
    active = models.BooleanField(default='1', verbose_name='Активен')
    teleph_id = models.CharField(max_length=255, null=True, unique=True, verbose_name='Имя в телефонии')
    autoru_id = models.IntegerField(null=True, unique=True, verbose_name='id авто.ру')
    avito_id = models.IntegerField(null=True, unique=True, verbose_name='id авито')
    drom_id = models.IntegerField(null=True, unique=True, verbose_name='id drom')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Клиенты'
        verbose_name_plural = 'Клиенты'
        ordering = ['name']


class Marks(models.Model):
    mark = models.CharField(max_length=255, unique=True, verbose_name='Марка')
    teleph = models.CharField(max_length=255, null=True, unique=True, verbose_name='Телефония')
    autoru = models.CharField(max_length=255, null=True, unique=True, verbose_name='Авто.ру')
    avito = models.CharField(max_length=255, null=True, unique=True, verbose_name='Авито')
    drom = models.CharField(max_length=255, null=True, unique=True, verbose_name='Drom')
    human_name = models.CharField(max_length=255, null=True, verbose_name='Народное')

    def __str__(self):
        return self.mark

    class Meta:
        verbose_name = 'Марки'
        verbose_name_plural = 'Марки'
        ordering = ['mark']


class Models(models.Model):
    mark = models.ForeignKey('Marks', on_delete=models.PROTECT, verbose_name='Марка')
    model = models.CharField(max_length=255, verbose_name='Модель')
    teleph = models.CharField(max_length=255, null=True, verbose_name='Телефония')
    autoru = models.CharField(max_length=255, null=True, verbose_name='Авто.ру')
    avito = models.CharField(max_length=255, null=True, verbose_name='Авито')
    drom = models.CharField(max_length=255, null=True, verbose_name='Drom')
    human_name = models.CharField(max_length=255, null=True, verbose_name='Народное')

    def __str__(self):
        return self.model

    class Meta:
        verbose_name = 'Модели'
        verbose_name_plural = 'Модели'
        ordering = ['model']


class AutoruCalls(models.Model):
    ad_id = models.CharField(max_length=255, null=True, verbose_name='id объявления')
    vin = models.CharField(max_length=17, null=True, verbose_name='VIN')
    client = models.ForeignKey('Clients', to_field='autoru_id', on_delete=models.PROTECT, verbose_name='id клиента')
    source = models.CharField(max_length=255, verbose_name='Исходящий')
    target = models.CharField(max_length=255, verbose_name='Входящий')
    datetime = models.DateTimeField(verbose_name='Дата и время')
    duration = models.IntegerField(verbose_name='Длительность')
    mark = models.CharField(max_length=255, null=True, verbose_name='Марка')
    model = models.CharField(max_length=255, null=True, verbose_name='Модель')
    billing_state = models.CharField(max_length=255, null=True, verbose_name='Статус оплаты')
    billing_cost = models.FloatField(null=True, verbose_name='Стоимость')

    def __str__(self):
        return f'{self.client} | {self.source} | {self.datetime} | {self.duration}'

    class Meta:
        verbose_name = 'Авто.ру звонки'
        verbose_name_plural = 'Авто.ру звонки'
        ordering = ['datetime']


class AutoruProducts(models.Model):
    ad_id = models.CharField(max_length=255, null=True, verbose_name='id объявления')
    vin = models.CharField(max_length=17, null=True, verbose_name='VIN')
    client = models.ForeignKey('Clients', to_field='autoru_id', on_delete=models.PROTECT, verbose_name='id клиента')
    date = models.DateField(verbose_name='Дата')
    mark = models.CharField(max_length=255, null=True, verbose_name='Марка')
    model = models.CharField(max_length=255, null=True, verbose_name='Модель')
    product = models.CharField(max_length=255, verbose_name='Услуга')
    sum = models.FloatField(verbose_name='Стоимость')
    count = models.IntegerField(verbose_name='Количество')
    total = models.FloatField(verbose_name='Сумма')

    def __str__(self):
        return f'{self.client} | {self.date} | {self.product}'

    class Meta:
        verbose_name = 'Авто.ру услуги'
        verbose_name_plural = 'Авто.ру услуги'
        ordering = ['date']


class TelephCalls(models.Model):
    client = models.ForeignKey('Clients', to_field='teleph_id', on_delete=models.PROTECT, verbose_name='id клиента')
    datetime = models.DateTimeField(verbose_name='Дата и время')
    num_from = models.CharField(max_length=255, verbose_name='Исходящий')
    mark = models.CharField(max_length=255, null=True, verbose_name='Марка')
    model = models.CharField(max_length=255, null=True, verbose_name='Модель')
    target = models.CharField(max_length=255, null=True, verbose_name='Входящий')
    moderation = models.CharField(max_length=255, null=True, verbose_name='Модерация')
    call_price = models.FloatField(null=True, verbose_name='Стоимость')
    price_autoru = models.FloatField(null=True, verbose_name='Стоимость авто.ру')
    price_drom = models.FloatField(null=True, verbose_name='Стоимость drom')

    def __str__(self):
        return f'{self.client} | {self.num_from} | {self.datetime}'

    class Meta:
        verbose_name = 'Телефония звонки'
        verbose_name_plural = 'Телефония звонки'
        ordering = ['datetime']
