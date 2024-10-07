from django import forms
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from slugify import slugify

from libs.services import choices
from libs.services.choices import EngineTypes, DriveTypes


# Чтобы PyCharm не подчеркивал objects в MyClass.objects.filter
class BaseModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True


class CustomBooleanField(models.BooleanField):
    def to_python(self, value):
        if value in (True, False):
            return bool(value)
        value = value.lower() if type(value) == str else value
        if value in ('да', 'д', 'yes', 'y'):
            return True
        if value in ('нет', 'н', 'no', 'n'):
            return False
        return super().to_python(value)


# class Client(BaseModel):
#     CALLS = 'звонки'
#     COMMISSION_PERCENT = 'комиссия процент'
#     COMMISSION_SUM = 'комиссия сумма'
#     CHARGE_TYPE_CHOICES = [
#         (CALLS, 'звонки'),
#         (COMMISSION_PERCENT, 'комиссия процент'),
#         (COMMISSION_SUM, 'комиссия сумма'),
#     ]
#     name = models.CharField(max_length=255, verbose_name='Имя')
#     slug = models.SlugField(max_length=300, allow_unicode=True, db_index=True, verbose_name='Slug')
#     manager = models.CharField(max_length=255, null=True, verbose_name='Менеджер')
#     active = models.BooleanField(default='1', verbose_name='Активен')
#     charge_type = models.CharField(max_length=255, choices=CHARGE_TYPE_CHOICES, default='звонки', verbose_name='Тип')
#     commission_size = models.FloatField(null=True, blank=True, verbose_name='Размер комиссии')
#     teleph_id = models.CharField(max_length=255, null=True, blank=True, unique=True, verbose_name='Имя в телефонии')
#     autoru_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id авто.ру')
#     autoru_name = models.CharField(max_length=500, null=True, blank=True, verbose_name='Имя на авто.ру')
#     avito_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id авито')
#     drom_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id drom')
#
#     def __str__(self):
#         return self.name
#
#     def save(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
#         self.slug = slugify(self.name)
#         if not self.slug:
#             slug_str = f'{self.name}'
#             self.slug = slugify(slug_str)
#         slug_exists = Client.objects.filter(~Q(id=self.id), slug=self.slug)
#         if slug_exists.count() > 0:
#             self.slug = f'{self.slug}-2'
#         super(Client, self).save(*args, **kwargs)
#
#     class Meta:
#         verbose_name = 'Клиент'
#         verbose_name_plural = 'Клиенты'
#         ordering = ['name']


class Mark(BaseModel):
    mark = models.CharField(max_length=255, unique=True, verbose_name='Марка')
    teleph = models.CharField(max_length=255, null=True, blank=True, unique=True, verbose_name='Телефония')
    autoru = models.CharField(max_length=255, null=True, blank=True, unique=True, verbose_name='Авто.ру')
    avito = models.CharField(max_length=255, null=True, blank=True, unique=True, verbose_name='Авито')
    drom = models.CharField(max_length=255, null=True, blank=True, unique=True, verbose_name='Drom')
    human_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Народное')

    def __str__(self):
        return self.mark

    class Meta:
        verbose_name = 'Марка'
        verbose_name_plural = 'Марки'
        ordering = ['mark']


class Model(BaseModel):
    mark = models.ForeignKey('Mark', on_delete=models.PROTECT, verbose_name='Марка')
    model = models.CharField(max_length=255, verbose_name='Модель')
    teleph = models.CharField(max_length=255, null=True, blank=True, verbose_name='Телефония')
    autoru = models.CharField(max_length=255, null=True, blank=True, verbose_name='Авто.ру')
    avito = models.CharField(max_length=255, null=True, blank=True, verbose_name='Авито')
    drom = models.CharField(max_length=255, null=True, blank=True, verbose_name='Drom')
    human_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Народное')

    def __str__(self):
        return self.model

    class Meta:
        verbose_name = 'Модель'
        verbose_name_plural = 'Модели'
        ordering = ['model']
        constraints = [
            models.UniqueConstraint(fields=['mark', 'model'], name='unique_mark_model'),
        ]


class Generation(BaseModel):
    mark = models.ForeignKey('Mark', on_delete=models.PROTECT, verbose_name='Марка')
    model = models.ForeignKey('Model', on_delete=models.PROTECT, verbose_name='Модель')
    generation = models.CharField(max_length=255, verbose_name='Поколение')
    # TODO года выпуска добавить
    teleph = models.CharField(max_length=255, null=True, blank=True, verbose_name='Телефония')
    autoru = models.CharField(max_length=255, null=True, blank=True, verbose_name='Авто.ру')
    avito = models.CharField(max_length=255, null=True, blank=True, verbose_name='Авито')
    drom = models.CharField(max_length=255, null=True, blank=True, verbose_name='Drom')
    human_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Народное')

    def __str__(self):
        return self.generation

    class Meta:
        verbose_name = 'Поколение'
        verbose_name_plural = 'Поколения'


class BodyTypes(models.TextChoices):
    # TODO заменить JEEP на SUV
    JEEP = 'Внедорожник', 'Внедорожник'
    JEEP_3 = 'Внедорожник 3 дв.' 'Внедорожник 3 дв.'
    JEEP_5 = 'Внедорожник 5 дв.', 'Внедорожник 5 дв.'
    JEEP_COUPE = 'Внедорожник Coupe', 'Внедорожник Coupe'
    JEEP_ESV = 'Внедорожник ESV', 'Внедорожник ESV'
    JEEP_GRAND = 'Внедорожник Grand', 'Внедорожник Grand'
    JEEP_L = 'Внедорожник L', 'Внедорожник L'
    JEEP_LONG = 'Внедорожник Long', 'Внедорожник Long'
    JEEP_X = 'Внедорожник X', 'Внедорожник X'
    CABRIOLET = 'Кабриолет', 'Кабриолет'
    COMPACT = 'Компактвэн', 'Компактвэн'
    COUPE = 'Купе', 'Купе'
    LIFTBACK = 'Лифтбек', 'Лифтбек'
    MICROBUS = 'Микроавтобус', 'Микроавтобус'
    MINIVAN = 'Минивэн', 'Минивэн'
    MINIVAN_LONG = 'Минивэн Long', 'Минивэн Long'
    PICKUP = 'Пикап', 'Пикап'
    ROADSTER = 'Родстер', 'Родстер'
    SEDAN = 'Седан', 'Седан'
    SEDAN_LONG = 'Седан Long', 'Седан Long'
    SEDAN_PULLMAN = 'Седан Pullman', 'Седан Pullman'
    TARGA = 'Тарга', 'Тарга'
    UNIVERSAL = 'Универсал', 'Универсал'
    UNIVERSAL_CROSS = 'Универсал Cross', 'Универсал Cross'
    HATCHBACK = 'Хэтчбек', 'Хэтчбек'
    HATCHBACK_3 = 'Хэтчбек 3 дв.', 'Хэтчбек 3 дв.'
    HATCHBACK_5 = 'Хэтчбек 5 дв.', 'Хэтчбек 5 дв.'
    METAL_VAN = 'Цельнометаллический Фургон', 'Цельнометаллический Фургон'


class Modification(BaseModel):
    code = models.ForeignKey('ModificationCode', related_name='modification_codes', null=True, blank=True,
                             on_delete=models.PROTECT, verbose_name='Коды модификации')
    clients_name = models.CharField(max_length=500, verbose_name='Расшифровка от клиента')
    short_name = models.CharField(max_length=255, editable=False, verbose_name='Короткое название')
    mark = models.ForeignKey('Mark', on_delete=models.PROTECT, verbose_name='Марка')
    model = models.ForeignKey('Model', on_delete=models.PROTECT, verbose_name='Модель')
    generation = models.ForeignKey('Generation', on_delete=models.PROTECT, verbose_name='Поколение')
    complectation = models.ForeignKey('Complectation', related_name='modifications', null=True, blank=True,
                                      on_delete=models.PROTECT, verbose_name='Комплектация')
    body_type = models.CharField(max_length=100, choices=BodyTypes.choices,
                                 verbose_name='Кузов')  # Изменил значение choices
    engine_volume = models.IntegerField(null=True, blank=True, verbose_name='Объём двигателя')
    power = models.IntegerField(verbose_name='Мощность')
    transmission = models.CharField(max_length=100, choices=choices.TRANSMISSION_CHOICES,
                                    verbose_name='Коробка передач')
    engine_type = models.CharField(max_length=100, choices=EngineTypes.choices, verbose_name='Тип двигателя')
    drive = models.CharField(max_length=100, choices=DriveTypes.choices, verbose_name='Привод')
    battery_capacity = models.IntegerField(null=True, blank=True, verbose_name='Ёмкость батареи')
    autoru_modification_id = models.IntegerField(null=True, blank=True, verbose_name='Авто.ру Модификация ID')
    autoru_complectation_id = models.IntegerField(null=True, blank=True, verbose_name='Авто.ру Комплектация ID')
    avito_modification_id = models.IntegerField(null=True, blank=True, verbose_name='Авито Модификация ID')
    avito_complectation_id = models.IntegerField(null=True, blank=True, verbose_name='Авито Комплектация ID')
    load_capacity = models.IntegerField(null=True, blank=True, verbose_name='Грузоподъёмность')

    def save(self, *args, **kwargs):
        if self.engine_volume:
            engine_volume = round(self.engine_volume / 1000, 1)
        else:
            engine_volume = ''
        if self.drive == choices.DRIVE_CHOICES_DICT['передний']:
            drive = 'FWD'
        elif self.drive == choices.DRIVE_CHOICES_DICT['задний']:
            drive = 'RWD'
        elif self.drive == choices.DRIVE_CHOICES_DICT['полный']:
            drive = '4WD'
        transmission = choices.TRANSMISSION_DICT_FLIPPED[self.transmission]
        # TODO настроить вид модификации по такому шаблону: 1.5 181 л.с. 4WD дизель AMT
        self.short_name = f'{engine_volume} {self.power} л.с. {drive} {self.engine_type} {transmission}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.mark} {self.model} {self.generation} {self.short_name} {self.complectation}'

    class Meta:
        verbose_name = 'Модификация'
        verbose_name_plural = 'Модификации'


class Complectation(BaseModel):
    # TODO убрать всё до поколения включительно
    # mark = models.ForeignKey('Mark', on_delete=models.PROTECT, verbose_name='Марка')
    # model = models.ForeignKey('Model', on_delete=models.PROTECT, verbose_name='Модель')
    # generation = models.ForeignKey('Generation', on_delete=models.PROTECT, verbose_name='Поколение')
    modification = models.ForeignKey('Modification', related_name='complectations',
                                     on_delete=models.PROTECT, verbose_name='Модификация')
    complectation = models.CharField(max_length=255, verbose_name='Комплектация')
    teleph = models.CharField(max_length=255, null=True, blank=True, verbose_name='Телефония')
    autoru = models.CharField(max_length=255, null=True, blank=True, verbose_name='Авто.ру')
    avito = models.CharField(max_length=255, null=True, blank=True, verbose_name='Авито')
    drom = models.CharField(max_length=255, null=True, blank=True, verbose_name='Drom')
    human_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Народное')

    def __str__(self):
        return self.complectation

    class Meta:
        verbose_name = 'Комплектация'
        verbose_name_plural = 'Комплектации'


class ModificationCode(BaseModel):
    code = models.CharField(max_length=500, verbose_name='Код')
    modification = models.ForeignKey('Modification', on_delete=models.PROTECT, verbose_name='Модификация')
    complectation = models.ForeignKey('Complectation', on_delete=models.PROTECT, verbose_name='Комплектация')

    def __str__(self):
        return self.modificaiton.short_name

    class Meta:
        db_table = 'services_modification_code'
        verbose_name = 'Код модификации'
        verbose_name_plural = 'Коды модификации'


class Colors(models.TextChoices):
    BEIGE = 'бежевый', 'бежевый'
    WHITE = 'белый', 'белый'
    BRONZE = 'бронзовый', 'бронзовый'
    CHERRY = 'вишнёвый', 'вишнёвый'
    LIGHTBLUE = 'голубой', 'голубой'
    YELLOW = 'жёлтый', 'жёлтый'
    GREEN = 'зелёный', 'зелёный'
    GOLD = 'золотистый', 'золотистый'
    INDIVIDUAL_COLOR = 'индивидуальная окраска', 'индивидуальная окраска'
    BROWN = 'коричневый', 'коричневый'
    RED = 'красный', 'красный'
    ORANGE = 'оранжевый', 'оранжевый'
    PURPLE = 'пурпурный', 'пурпурный'
    SILVER = 'серебристый', 'серебристый'
    GRAY = 'серый', 'серый'
    BLUE = 'синий', 'синий'
    VIOLET = 'фиолетовый', 'фиолетовый'
    BLACK = 'чёрный', 'чёрный'


class _TypedMultipleChoiceField(forms.TypedMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.pop('base_field', None)
        kwargs.pop('max_length', None)
        super().__init__(*args, **kwargs)


class ChoiceArrayField(ArrayField):
    """
    Кастомное поле для множественного выбора
    """

    def formfield(self, **kwargs):
        defaults = {
            'form_class': _TypedMultipleChoiceField,
            'choices': self.base_field.choices,
            'coerce': self.base_field.to_python,
            # 'widget': forms.CheckboxSelectMultiple,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)