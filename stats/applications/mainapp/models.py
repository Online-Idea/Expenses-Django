from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime


class Colors(models.TextChoices):
    BEIGE = 'бежевый', _('бежевый')
    WHITE = 'белый', _('белый')
    BRONZE = 'бронзовый', _('бронзовый')
    CHERRY = 'вишнёвый', _('вишнёвый')
    LIGHTBLUE = 'голубой', _('голубой')
    YELLOW = 'жёлтый', _('жёлтый')
    GREEN = 'зелёный', _('зелёный')
    GOLD = 'золотистый', _('золотистый')
    INDIVIDUAL_COLOR = 'индивидуальная окраска', _('индивидуальная окраска')
    BROWN = 'коричневый', _('коричневый')
    RED = 'красный', _('красный')
    ORANGE = 'оранжевый', _('оранжевый')
    PURPLE = 'пурпурный', _('пурпурный')
    SILVER = 'серебристый', _('серебристый')
    GRAY = 'серый', _('серый')
    BLUE = 'синий', _('синий')
    VIOLET = 'фиолетовый', _('фиолетовый')
    BLACK = 'чёрный', _('чёрный')


class BodyTypes(models.TextChoices):
    JEEP = 'Внедорожник', _('Внедорожник')
    JEEP_3 = 'Внедорожник 3 дв.', _('Внедорожник 3 дв.')
    JEEP_5 = 'Внедорожник 5 дв.', _('Внедорожник 5 дв.')
    JEEP_COUPE = 'Внедорожник Coupe', _('Внедорожник Coupe')
    JEEP_ESV = 'Внедорожник ESV', _('Внедорожник ESV')
    JEEP_GRAND = 'Внедорожник Grand', _('Внедорожник Grand')
    JEEP_L = 'Внедорожник L', _('Внедорожник L')
    JEEP_LONG = 'Внедорожник Long', _('Внедорожник Long')
    JEEP_X = 'Внедорожник X', _('Внедорожник X')
    CABRIOLET = 'Кабриолет', _('Кабриолет')
    COMPACT = 'Компактвэн', _('Компактвэн')
    COUPE = 'Купе', _('Купе')
    LIFTBACK = 'Лифтбек', _('Лифтбек')
    MICROBUS = 'Микроавтобус', _('Микроавтобус')
    MINIVAN = 'Минивэн', _('Минивэн')
    MINIVAN_LONG = 'Минивэн Long', _('Минивэн Long')
    PICKUP = 'Пикап', _('Пикап')
    ROADSTER = 'Родстер', _('Родстер')
    SEDAN = 'Седан', _('Седан')
    SEDAN_LONG = 'Седан Long', _('Седан Long')
    SEDAN_PULLMAN = 'Седан Pullman', _('Седан Pullman')
    TARGA = 'Тарга', _('Тарга')
    UNIVERSAL = 'Универсал', _('Универсал')
    UNIVERSAL_CROSS = 'Универсал Cross', _('Универсал Cross')
    HATCHBACK = 'Хэтчбек', _('Хэтчбек')
    HATCHBACK_3 = 'Хэтчбек 3 дв.', _('Хэтчбек 3 дв.')
    HATCHBACK_5 = 'Хэтчбек 5 дв.', _('Хэтчбек 5 дв.')
    METAL_VAN = 'Цельнометаллический Фургон', _('Цельнометаллический Фургон')


# Чтобы PyCharm не подчеркивал objects в MyClass.objects.filter
class BaseModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True


class BaseField(BaseModel):
    teleph = models.CharField(max_length=64, null=True, blank=True, verbose_name='Телефония')
    autoru = models.CharField(max_length=64, null=True, blank=True, verbose_name='Авто.ру')
    avito = models.CharField(max_length=64, null=True, blank=True, verbose_name='Авито')
    drom = models.CharField(max_length=64, null=True, blank=True, verbose_name='Drom')
    human_name = models.CharField(max_length=64, null=True, blank=True, verbose_name='Народное')

    class Meta:
        abstract = True


class AbstractMark(BaseModel):
    name = models.CharField(max_length=64, unique=True, verbose_name='Название марки')

    class Meta:
        abstract = True


class AbstractModel(BaseModel):
    name = models.CharField(max_length=64, verbose_name='Название модели')

    class Meta:
        abstract = True


class AbstractGeneration(BaseModel):
    name = models.CharField(max_length=64, verbose_name='Название поколения')

    class Meta:
        abstract = True


class AbstractModification(BaseModel):
    class Transmission(models.TextChoices):
        AT = 'Автомат', _('Автомат')
        AMT = 'Робот', _('Робот')
        CVT = 'Вариатор', _('Вариатор')
        MT = 'Механика', _('Механика')

        # Обратный словарь для получения напзвания атрибута по значению
        @classmethod
        def get_name_attr(cls, value: str) -> str:
            """
            Метод класса для получения напзвания атрибута по значению value

            :param value: Значение атрибута
            :return название атрибута
            """
            return next(attr for attr, val in cls.__members__.items() if val == value)

    class EngineType(models.TextChoices):
        BENZIN = 'Бензин', _('Бензин')
        DIESEL = 'Дизель', _('Дизель')
        HYBRID = 'Гибрид', _('Гибрид')
        ELECTRO = 'Электро', _('Электро')

    class Drive(models.TextChoices):
        FRONT = 'Передний', _('Передний')
        REAR = 'Задний', _('Задний')
        FULL = 'Полный', _('Полный')

    name = models.CharField(max_length=100, verbose_name="Название модификации")

    years_from = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(datetime.now().year)],
                                     verbose_name="Годы от")
    years_to = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(datetime.now().year)],
                                   verbose_name="Год до")
    clients_name = models.CharField(max_length=512, null=True, blank=True,
                                    verbose_name='Расшифровка от клиента')
    short_name = models.CharField(max_length=124, editable=False,
                                  verbose_name='Короткое название')
    drive = models.CharField(max_length=64, choices=Drive.choices,
                             verbose_name='Привод')
    engine_type = models.CharField(max_length=64, choices=EngineType.choices,
                                   verbose_name='Тип двигателя')
    transmission = models.CharField(max_length=64, choices=Transmission.choices,
                                    verbose_name='Коробка передач')
    power = models.IntegerField(verbose_name='Мощность')
    engine_volume = models.FloatField(null=True, blank=True,
                                      verbose_name='Объём двигателя')
    body_type = models.CharField(max_length=64, choices=BodyTypes.choices,
                                 verbose_name='Кузов')
    doors = models.IntegerField(null=True, blank=True,
                                verbose_name='Количество дверей')
    battery_capacity = models.IntegerField(null=True, blank=True,
                                           verbose_name='Ёмкость батареи')
    load_capacity = models.IntegerField(null=True, blank=True,
                                        verbose_name='Грузоподъёмность')

    # autoru_modification_id = models.IntegerField(null=True, blank=True, verbose_name='Авто.ру Модификация ID')
    # autoru_complectation_id = models.IntegerField(null=True, blank=True, verbose_name='Авто.ру Комплектация ID')
    # avito_modification_id = models.IntegerField(null=True, blank=True, verbose_name='Авито Модификация ID')
    # avito_complectation_id = models.IntegerField(null=True, blank=True, verbose_name='Авито Комплектация ID')

    class Meta:
        abstract = True


class AbstractComplectation(BaseModel):
    name = models.CharField(max_length=100,
                            verbose_name="Название комплектации")

    class Meta:
        abstract = True


class Mark(AbstractMark, BaseField):
    class Meta:
        verbose_name = 'Марка'
        verbose_name_plural = 'Марки'
        ordering = ['name']

    def __str__(self): return self.name


class Model(AbstractModel, BaseField):
    mark = models.ForeignKey('Mark', on_delete=models.CASCADE, related_name='models',
                             verbose_name='Ссылка на марку')

    class Meta:
        verbose_name = 'Модель'
        verbose_name_plural = 'Модели'

    def __str__(self): return self.name


class Generation(AbstractGeneration, BaseField):
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='generations',
                              verbose_name="Ссылка на модель авто")

    class Meta:
        verbose_name = 'Поколение'
        verbose_name_plural = 'Поколения'

    def __str__(self): return self.name


class Modification(AbstractModification):
    mark = models.ForeignKey(Mark, on_delete=models.CASCADE,
                             verbose_name="Марка к которой относится модификация")
    model = models.ForeignKey(Model, on_delete=models.CASCADE,
                              verbose_name="Модель к которой относится модификация")

    generation = models.ForeignKey(Generation, on_delete=models.CASCADE, related_name='modifications',
                                   verbose_name="Поколение к которой относится модификация")

    class Meta:
        verbose_name = 'Модификация'
        verbose_name_plural = 'Модификации'

    def save(self, *args, **kwargs):
        if self.engine_volume:
            engine_volume = round(self.engine_volume / 1000, 1)
        else:
            engine_volume = ''
        if self.drive == Modification.Drive.FRONT:
            drive = 'FWD'
        elif self.drive == Modification.Drive.REAR:
            drive = 'RWD'
        elif self.drive == Modification.Drive.FULL:
            drive = '4WD'
        transmission = Modification.Transmission[self.transmission].label
        # TODO настроить вид модификации по такому шаблону: 1.5 181 л.с. 4WD дизель AMT
        self.short_name = f'{engine_volume} {self.power} л.с. {drive} {self.engine_type} {transmission}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.mark} {self.model} {self.generation} {self.short_name}'


class Complectation(AbstractComplectation):
    modification = models.ForeignKey(Modification, on_delete=models.CASCADE, related_name='complectations',
                                     verbose_name="Модификация")

    class Meta:
        verbose_name = 'Комплектация'
        verbose_name_plural = 'Комплектации'

    def __str__(self): return self.name


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
