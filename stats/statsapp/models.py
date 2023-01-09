import json
from django.db import models
from django.db.models import Q
from slugify import slugify


# Create your models here.
class Clients(models.Model):
    CALLS = 'звонки'
    COMMISSION_PERCENT = 'комиссия процент'
    COMMISSION_SUM = 'комиссия сумма'
    CHARGE_TYPE_CHOICES = [
        (CALLS, 'звонки'),
        (COMMISSION_PERCENT, 'комиссия процент'),
        (COMMISSION_SUM, 'комиссия сумма'),
    ]
    name = models.CharField(max_length=255, verbose_name='Имя')
    slug = models.SlugField(max_length=300, allow_unicode=True, db_index=True, verbose_name='Slug')
    manager = models.CharField(max_length=255, null=True, verbose_name='Менеджер')
    active = models.BooleanField(default='1', verbose_name='Активен')
    charge_type = models.CharField(max_length=255, choices=CHARGE_TYPE_CHOICES, default='звонки', verbose_name='Тип')
    commission_size = models.FloatField(null=True, blank=True, verbose_name='Размер комиссии')
    teleph_id = models.CharField(max_length=255, null=True, blank=True, unique=True, verbose_name='Имя в телефонии')
    autoru_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id авто.ру')
    avito_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id авито')
    drom_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id drom')

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        self.slug = slugify(self.name)
        if not self.slug:
            slug_str = f'{self.name}'
            self.slug = slugify(slug_str)
        slug_exists = Clients.objects.filter(~Q(id=self.id), slug=self.slug)
        if slug_exists.count() > 0:
            self.slug = f'{self.slug}-2'
        super(Clients, self).save(*args, **kwargs)

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


class ConverterTask(models.Model):
    client = models.ForeignKey(to='Clients', on_delete=models.SET_NULL, null=True, verbose_name='Клиент')
    name = models.CharField(max_length=500, verbose_name='Название')
    stock = models.URLField(verbose_name='Сток')
    active = models.BooleanField(default=True, verbose_name='Активна')
    photos_folder = models.ForeignKey(to='PhotoFolder', on_delete=models.SET_NULL, null=True,
                                      verbose_name='Папка с фото')
    front = models.IntegerField(default=10, verbose_name='Начало')
    back = models.IntegerField(default=10, verbose_name='Конец')
    interior = models.IntegerField(default=10, verbose_name='Фото интерьеров', blank=True, null=True)
    salon_only = models.BooleanField(verbose_name='Только фото салона', default=False)
    template = models.URLField(verbose_name='Шаблон')
    stock_fields = models.ForeignKey(to='StockFields', on_delete=models.CASCADE, verbose_name='Поля стока')
    configuration = models.ForeignKey(to='Configuration', on_delete=models.SET_NULL, blank=True, null=True,
                                      verbose_name='Конфигурация')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Задача конвертера'
        verbose_name_plural = 'Задачи конвертера'
        ordering = ['name']


class StockFields(models.Model):
    name = models.CharField(max_length=500, verbose_name='Название')
    car_tag = models.CharField(max_length=500, verbose_name='Тег автомобиля')
    modification_code = models.CharField(max_length=500, blank=True, null=True, verbose_name='Код модификации')
    color_code = models.CharField(max_length=500, blank=True, null=True, verbose_name='Код цвета')
    interior_code = models.CharField(max_length=500, blank=True, null=True, verbose_name='Код интерьера')
    options_code = models.CharField(max_length=500, blank=True, null=True, verbose_name='Опции и пакеты')
    price = models.CharField(max_length=500, blank=True, null=True, verbose_name='Цена')
    year = models.CharField(max_length=500, blank=True, null=True, verbose_name='Год выпуска')
    vin = models.CharField(max_length=500, blank=True, null=True, verbose_name='Исходный VIN')
    id_from_client = models.CharField(max_length=500, blank=True, null=True, verbose_name='ID от клиента')
    modification_explained = models.CharField(max_length=500, blank=True, null=True, verbose_name='Расш. модификации')
    color_explained = models.CharField(max_length=500, blank=True, null=True, verbose_name='Расш. цвета')
    interior_explained = models.CharField(max_length=500, blank=True, null=True, verbose_name='Расш. интерьера')
    description = models.CharField(max_length=500, blank=True, null=True, verbose_name='Описание')
    trade_in = models.CharField(max_length=500, blank=True, null=True, verbose_name='Трейд-ин')
    credit = models.CharField(max_length=500, blank=True, null=True, verbose_name='Кредит')
    insurance = models.CharField(max_length=500, blank=True, null=True, verbose_name='Страховка')
    max_discount = models.CharField(max_length=500, blank=True, null=True, verbose_name='Максималка')
    availability = models.CharField(max_length=500, blank=True, null=True, verbose_name='Наличие')
    run = models.CharField(max_length=500, blank=True, null=True, verbose_name='Пробег')
    images = models.CharField(max_length=500, blank=True, null=True, verbose_name='Фото клиента')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Поля стока'
        verbose_name_plural = 'Поля стоков'
        ordering = ['name']


class PhotoFolder(models.Model):
    folder = models.CharField(max_length=500, unique=True, verbose_name='Папка с фото')

    def __str__(self):
        return self.folder

    class Meta:
        verbose_name = 'Папка с фото'
        verbose_name_plural = 'Папки с фото'
        ordering = ['folder']


class Configuration(models.Model):
    DEFAULT = json.dumps([{"file": [{"column": "mark"}], "base": [{"column": "mark"}]},
                          {"file": [{"column": "model"}], "base": [{"column": "model"}]},
                          {"file": [{"column": "complectation"}], "base": [{"column": "complectation"}],
                           "intersection": True, "ifExists": True},
                          {"file": [{"column": "body"}], "base": [{"column": "body"}]},
                          {"file": [{"column": "color"}], "base": [{"column": "color"}]}])

    converter_id = models.IntegerField(unique=True, verbose_name='id в конвертере')
    name = models.CharField(max_length=500, verbose_name='Название')
    configuration = models.JSONField(verbose_name='Настройки')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Конфигурация'
        verbose_name_plural = 'Конфигурации'
        ordering = ['name']
