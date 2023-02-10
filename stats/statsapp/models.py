import json
from django.db import models
from django.db.models import Q
from slugify import slugify


# Чтобы PyCharm не подчеркивал objects в MyClass.objects.filter
class BaseModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True


class Clients(BaseModel):
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


class Marks(BaseModel):
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


class Models(BaseModel):
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


class AutoruCalls(BaseModel):
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


class AutoruProducts(BaseModel):
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


class TelephCalls(BaseModel):
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


class ConverterTask(BaseModel):
    STOCK_SOURCE_CHOICES = [
        ('Ссылка', 'Ссылка'),
        ('POST-запрос', 'POST-запрос'),
    ]
    client = models.ForeignKey(to='Clients', on_delete=models.SET_NULL, null=True, verbose_name='Клиент')
    name = models.CharField(max_length=500, verbose_name='Название')
    stock_source = models.CharField(max_length=500, choices=STOCK_SOURCE_CHOICES, verbose_name='Источник стока')
    stock_url = models.URLField(blank=True, null=True, verbose_name='Ссылка стока')
    stock_post_host = models.URLField(blank=True, null=True, verbose_name='POST-запрос Хост')
    stock_post_login = models.CharField(max_length=500, blank=True, null=True, verbose_name='POST-запрос Логин')
    stock_post_password = models.CharField(max_length=500, blank=True, null=True, verbose_name='POST-запрос Пароль')
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


class StockFields(BaseModel):
    TEMPLATE_COL = {  # Номер столбца для xlsx шаблона
        # 'имя поля из StockFields': ('имя столбца для шаблона', номер столбца для шаблона)
        'modification_code': ('Код модификации', 0),
        'complectation_code': ('Код комплектации', 1),
        'color_code': ('Код цвета', 2),
        'interior_code': ('Код интерьера', 3),
        'options_code': ('Опции и пакеты', 4),
        'price': ('Цена', 5),
        'price_sale_1': ('Цена по акции 1', 6),
        'price_sale_2': ('Цена по акции 2', 7),
        'year': ('Год', 8),
        'vin': ('Исходный VIN', 9),
        'id_from_client':  ('ID от клиента', 10),
        'trade_in':  ('Трейд-ин', 11),
        'credit':  ('Кредит', 12),
        'insurance':  ('Страховка', 13),
        'max_discount':  ('Максималка', 14),
        'images':  ('Фото клиента', 15),
        'modification_explained':  ('Расш. модификации', 16),
        'color_explained':  ('Расш. цвета', 17),
        'interior_explained':  ('Расш. интерьера', 18),
        'run': ('Пробег', 19),
    }
    multi_tags_help = 'Если тег с детьми и нужно значение детей то пиши тег/дети, например options/option. ' \
                      'Если тег с детьми и из детей нужен атрибут то пиши тег/дети@атрибут, например options/option@code. ' \
                      'Если тег несколько раз повторяется и нужно значение то пиши тег, например option. ' \
                      'Если тег несколько раз повторяется и из него нужен атрибут то пиши тег@атрибут, например option@code.'

    name = models.CharField(max_length=500, verbose_name='Название')
    encoding = models.CharField(max_length=500, default='UTF-8', verbose_name='Кодировка')
    car_tag = models.CharField(max_length=500, blank=True, null=True, verbose_name='Тег автомобиля')
    modification_code = models.CharField(max_length=500, blank=True, null=True, verbose_name='Код модификации')
    color_code = models.CharField(max_length=500, blank=True, null=True, verbose_name='Код цвета')
    interior_code = models.CharField(max_length=500, blank=True, null=True, verbose_name='Код интерьера')
    options_code = models.CharField(max_length=500, blank=True, null=True, verbose_name='Опции и пакеты',
                                    help_text=multi_tags_help)
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
    images = models.CharField(max_length=500, blank=True, null=True, verbose_name='Фото клиента',
                              help_text=multi_tags_help)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Поля стока'
        verbose_name_plural = 'Поля стоков'
        ordering = ['name']


class PhotoFolder(BaseModel):
    folder = models.CharField(max_length=500, unique=True, verbose_name='Папка с фото')

    def __str__(self):
        return self.folder

    class Meta:
        verbose_name = 'Папка с фото'
        verbose_name_plural = 'Папки с фото'
        ordering = ['folder']


class Configuration(BaseModel):
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


class ConverterLogsBotData(BaseModel):
    chat_id = models.CharField(max_length=500, verbose_name='id чата в телеграме')

    def __str__(self):
        return self.chat_id

    class Meta:
        verbose_name = 'Логи конвертера'
        verbose_name_plural = 'Логи конвертера'
        ordering = ['chat_id']
