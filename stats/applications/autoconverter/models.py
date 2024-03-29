import json

from django.db import models

from libs.services.models import BaseModel, Client


class ConverterTask(BaseModel):
    STOCK_SOURCE_CHOICES = [
        ('Ссылка', 'Ссылка'),
        ('POST-запрос', 'POST-запрос'),
    ]
    client = models.ForeignKey(to=Client, on_delete=models.SET_NULL, null=True, verbose_name='Клиент')
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
    stock_fields = models.ForeignKey(to='StockFields', on_delete=models.PROTECT, verbose_name='Поля стока')
    configuration = models.ForeignKey(to='Configuration', on_delete=models.SET_NULL, blank=True, null=True,
                                      verbose_name='Конфигурация')
    notifications_email = models.CharField(max_length=500, blank=True, null=True, verbose_name='Почта для уведомлений')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'autoconverter_converter_task'
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
        'id_from_client': ('ID от клиента', 10),
        'trade_in': ('Трейд-ин', 11),
        'credit': ('Кредит', 12),
        'insurance': ('Страховка', 13),
        'max_discount': ('Максималка', 14),
        'images': ('Фото клиента', 15),
        'modification_explained': ('Расш. модификации', 16),
        'color_explained': ('Расш. цвета', 17),
        'interior_explained': ('Расш. интерьера', 18),
        'run': ('Пробег', 19),
        'description': ('Описание', 20),
    }
    multi_tags_help = """
        Если тег с детьми и нужно значение детей то пиши тег/дети, например options/option.
        Если тег с детьми и из детей нужен атрибут то пиши тег/дети@атрибут, например options/option@code.
        Если тег несколько раз повторяется и нужно значение то пиши тег, например option.
        Если тег несколько раз повторяется и из него нужен атрибут то пиши тег@атрибут, например option@code.
    """

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
        db_table = 'autoconverter_stock_fields'
        verbose_name = 'Поля стока'
        verbose_name_plural = 'Поля стоков'
        ordering = ['name']


class PhotoFolder(BaseModel):
    folder = models.CharField(max_length=500, unique=True, verbose_name='Папка с фото')

    def __str__(self):
        return self.folder

    class Meta:
        db_table = 'autoconverter_photo_folder'
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
        db_table = 'autoconverter_converter_logs_bot_data'
        verbose_name = 'Логи конвертера'
        verbose_name_plural = 'Логи конвертера'
        ordering = ['chat_id']


class ConverterFilter(BaseModel):
    CONTAINS = 'in'
    NOT_CONTAINS = 'not in'
    EQUALS = '=='
    NOT_EQUALS = '!='
    GREATER_THAN = '>'
    LESS_THAN = '<'
    STARTS_WITH = 'starts_with'
    NOT_STARTS_WITH = 'not_starts_with'
    ENDS_WITH = 'ends_with'
    NOT_ENDS_WITH = 'not_ends_with'
    CONDITION_CHOICES = [
        (CONTAINS, 'содержит'),
        (NOT_CONTAINS, 'не содержит'),
        (EQUALS, 'равно'),
        (NOT_EQUALS, 'не равно'),
        (GREATER_THAN, 'больше'),
        (LESS_THAN, 'меньше'),
        (STARTS_WITH, 'начинается с'),
        (NOT_STARTS_WITH, 'не начинается с'),
        (ENDS_WITH, 'заканчивается на'),
        (NOT_ENDS_WITH, 'не заканчивается на'),
    ]
    value_help_text = 'Для фильтрации по нескольким значениям пиши каждое между `` и разделяй запятыми.' \
                      ' Например: `E (W/S213)`, `CLS (C257)`'

    converter_task = models.ForeignKey(to='ConverterTask', verbose_name='Задача конвертера', on_delete=models.PROTECT)
    field = models.CharField(max_length=500, verbose_name='Поле')
    condition = models.CharField(max_length=500, choices=CONDITION_CHOICES, verbose_name='Условие')
    value = models.CharField(max_length=500, help_text=value_help_text, verbose_name='Значение')

    def __str__(self):
        return f'{self.field} {self.condition} {self.value}'

    class Meta:
        db_table = 'autoconverter_converter_filter'
        verbose_name = 'Фильтр конвертера'
        verbose_name_plural = 'Фильтры конвертера'
        ordering = ['field']


class ConverterExtraProcessing(BaseModel):
    # Различные изменения прайса по условию
    SOURCE_CHOICES = [
        ('Сток', 'Сток'),
        ('Прайс', 'Прайс')
    ]
    new_value_help = 'Если одно значение для всех то пиши его, если из другого столбца то пиши имя столбца' \
                     'в формате: %col:"имя_столбца"'

    converter_task = models.ForeignKey(to='ConverterTask', verbose_name='Задача конвертера', on_delete=models.PROTECT)
    source = models.CharField(max_length=500, choices=SOURCE_CHOICES, verbose_name='Источник')
    price_column_to_change = models.CharField(max_length=500, verbose_name='Столбец прайса в котором менять')
    new_value = models.CharField(max_length=5000, help_text=new_value_help, verbose_name='Новое значение')

    def __str__(self):
        return f'{self.converter_task.name} {self.source} -> {self.price_column_to_change} {self.new_value}'

    class Meta:
        db_table = 'autoconverter_converter_extra_processing'
        verbose_name = 'Обработка прайса'
        verbose_name_plural = 'Обработка прайса'


class Conditional(BaseModel):
    converter_extra_processing = models.ForeignKey(ConverterExtraProcessing, on_delete=models.PROTECT)
    field = models.CharField(max_length=500, help_text=StockFields.multi_tags_help, verbose_name='Поле')
    condition = models.CharField(max_length=500, choices=ConverterFilter.CONDITION_CHOICES, verbose_name='Условие')
    value = models.CharField(max_length=500, help_text=ConverterFilter.value_help_text, verbose_name='Значение')

    def __str__(self):
        return f'{self.converter_extra_processing} {self.field} {self.condition} {self.value}'

    class Meta:
        verbose_name = 'Условие'
        verbose_name_plural = 'Условия'
