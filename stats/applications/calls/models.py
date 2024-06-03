from django.db import models
from django.utils.translation import gettext_lazy as _

from applications.accounts.models import Client
from libs.services.choices import DriveTypes, EngineTypes
from libs.services.models import BaseModel, Mark, Model, Colors, BodyTypes, ChoiceArrayField


# Create your models here.
class CabinetPrimatel(BaseModel):
    """
    Главный кабинет Примател
    """
    login = models.CharField(max_length=100, unique=True, verbose_name='Логин')
    password = models.CharField(max_length=100, verbose_name='Пароль')
    name = models.CharField(max_length=500, verbose_name='Название')
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'calls_cabinet'
        verbose_name = 'Кабинет Примател'
        verbose_name_plural = 'Кабинеты Примател'


class ClientPrimatel(BaseModel):
    """
    Клиенты Приматела
    """
    login = models.CharField(max_length=100, unique=True, verbose_name='Логин')
    name = models.CharField(max_length=500, blank=True, null=True, verbose_name='Название')
    active = models.BooleanField(default=True, blank=True, null=True, verbose_name='Активный')
    numbers = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Номера')
    cabinet_primatel = models.ForeignKey(CabinetPrimatel, on_delete=models.PROTECT, verbose_name='Кабинет Примател')
    client = models.ForeignKey(Client, blank=True, null=True, on_delete=models.PROTECT, verbose_name='Клиент')

    # Возможная добавка (были в старой телефонии)
    # balance = models.IntegerField(blank=True, null=True, verbose_name='Баланс')
    # price_as_moderation = models.BooleanField(default=False, verbose_name='Цена по Цене М')
    # price_request = models.IntegerField(blank=True, null=True, verbose_name='Цена Заявка')
    # price_request_moderation = models.BooleanField(default=False, verbose_name='Цена Заявка по Цене М')
    # price_used = models.IntegerField(blank=True, null=True, verbose_name='Цена БУ')
    # price_used_moderation = models.BooleanField(default=False, verbose_name='Цена БУ по Цене М')
    # price_avito = models.IntegerField(blank=True, null=True, verbose_name='Цена Авито')
    # price_avito_moderation = models.BooleanField(default=False, verbose_name='Цена Авито по Цене М')
    # price_drom = models.IntegerField(blank=True, null=True, verbose_name='Цена Дром')
    # price_drom_moderation = models.BooleanField(default=False, verbose_name='Цена Дром по Цене М')
    # price_extra = models.IntegerField(blank=True, null=True, verbose_name='Цена Запас')
    # price_extra_moderation = models.BooleanField(default=False, verbose_name='Цена Запас по Цене М')
    # manager = models.ForeignKey(Client, verbose_name='Менеджер')
    # plan = models.IntegerField(blank=True, null=True, verbose_name='План')
    # drom_dealer_id = models.IntegerField(blank=True, null=True, verbose_name='Дром id дилера')
    # autoru_id = models.IntegerField(blank=True, null=True, verbose_name='Авто.ру id')
    # autoru_token = models.CharField(max_length=500, blank=True, null=True, verbose_name='Авто.ру Токен')
    # autoru_login = models.CharField(max_length=100, blank=True, null=True, verbose_name='Авто.ру Логин')
    # autoru_password = models.CharField(max_length=100, blank=True, null=True, verbose_name='Авто.ру Пароль')

    def __str__(self):
        return self.login

    class Meta:
        db_table = 'calls_client_primatel'
        verbose_name = 'Клиент Примател'
        verbose_name_plural = 'Клиенты Примател'


class ClientPrimatelMark(BaseModel):
    """
    Отношение Many-to-Many между ClientPrimatel и Mark
    """
    client_primatel = models.ForeignKey(ClientPrimatel, on_delete=models.CASCADE, verbose_name='Клиент Примател')
    mark = models.ForeignKey(Mark, on_delete=models.CASCADE, verbose_name='Марка')

    def __str__(self):
        return f'{self.client_primatel.name} - {self.mark.mark}'

    class Meta:
        db_table = 'calls_client_primatel_mark'
        verbose_name = 'Клиент-Марка'
        verbose_name_plural = 'Клиент-Марка'


class SipPrimatel(BaseModel):
    """
    Sip это наш телефон в Примателе
    """
    client_primatel = models.ForeignKey(ClientPrimatel, on_delete=models.CASCADE, verbose_name='Клиент Примател')
    sip_login = models.CharField(max_length=100, verbose_name='Sip логин')

    def __str__(self):
        return f'{self.client_primatel.name} | {self.sip_login}'

    class Meta:
        db_table = 'calls_sip_primatel'
        verbose_name = 'Sip Примател'
        verbose_name_plural = 'Sip Примател'


class TargetChoice(models.TextChoices):
    YES = 'Да', _('Да')
    NO = 'Нет', _('Нет')
    TO_MODERATION = 'На модерацию', _('На модерацию')
    PM_YES = 'ПМ - Целевой', _('ПМ - Целевой')
    PM_NO = 'ПМ - Нецелевой', _('ПМ - Нецелевой')


class ModerationChoice(models.TextChoices):
    M = 'М', _('М')
    MZ = 'М(З)', _('М(З)')
    MB = 'М(Б)', _('М(Б)')
    USED = 'БУ', _('БУ')
    AUTORU_USED = 'Авто.ру БУ', _('Авто.ру БУ')
    REQUEST = 'Заявка', _('Заявка')
    DROM = 'Дром', _('Дром')
    AVITO = 'Авито', _('Авито')
    AVITO_USED = 'Авито БУ', _('Авито БУ')
    EXTRA = 'Запас', _('Запас')
    RESOURCES = 'Доп. ресурсы', _('Доп. ресурсы')

    @classmethod
    def get_site_name_by_choice(cls, choice):
        """
        Возвращает общее имя площадки
        :param choice:
        :return:
        """
        if choice in [cls.M, cls.MZ, cls.MB, cls.AUTORU_USED]:
            return 'Автору'
        elif choice in [cls.AVITO, cls.AVITO_USED]:
            return 'Авито'
        elif choice in [cls.USED, cls.REQUEST, cls.DROM, cls.EXTRA, cls.RESOURCES]:
            return choice
        else:
            raise ValueError(f'Неизвестная модерация {choice}')


class CallManager(models.Manager):

    def clean_phone_numbers(self, number: str):
        """
        Чистит номера телефонов от лишних символов
        :param number:
        :return:
        """
        return number.replace('+', '')

    def create(self, *args, **kwargs):
        kwargs['num_from'] = self.clean_phone_numbers(kwargs['num_from'])
        kwargs['num_to'] = self.clean_phone_numbers(kwargs['num_to'])
        kwargs['num_redirect'] = self.clean_phone_numbers(kwargs['num_redirect'])
        return super().create(*args, **kwargs)

    def save(self, *args, **kwargs):
        if args:
            instance = args[0]
        else:
            instance = kwargs['instance']
        instance.num_from = self.clean_phone_numbers(instance.num_from)
        instance.num_to = self.clean_phone_numbers(instance.num_to)
        instance.num_redirect = self.clean_phone_numbers(instance.num_redirect)
        return super().save(*args, **kwargs)


class Call(BaseModel):
    objects = CallManager()

    class StatusChoice(models.TextChoices):
        DISCUSSING_PRICE_AND_AUTO = 'Обсуждают цену и авто', _('Обсуждают цену и авто')
        LEAVES_PHONE_FOR_CALLBACK = 'Оставляет номер для перезвона', _('Оставляет номер для перезвона')
        NO_ONE_PICKED_UP = 'Никто не взял трубку', _('Никто не взял трубку')
        REDIRECTED_BUT_SALES_DIDNT_PICKUP = 'Перевели, но Отдел продаж не взял трубку', _(
            'Перевели, но Отдел продаж не взял трубку')
        REPEAT_CALL = 'Повторный звонок', _('Повторный звонок')
        CALLBACK_CLIENT_DIDNT_PICKUP = 'Обратный звонок. Клиент не взял трубку', _(
            'Обратный звонок. Клиент не взял трубку')
        CLIENT_ASKS_FOR_CALLBACK = 'Клиент просит перезвонить', _('Клиент просит перезвонить')
        CALLCENTER_DIDNT_PICKUP = 'КЦ не взял трубку', _('КЦ не взял трубку')
        CALL_ABOUT_USED = 'Звонок по БУ', _('Звонок по БУ')
        CALL_ABOUT_TECHNICAL_INSPECTION = 'Звонок по ТО', _('Звонок по ТО')
        CALL_ABOUT_PARTS = 'Запчасти', _('Запчасти')
        DISCONNECTED = 'Сорвался', _('Сорвался')
        CANT_HEAR_CLIENT = 'Не слышно клиента', _('Не слышно клиента')
        WRONG_NUMBER = 'Ошибочный звонок', _('Ошибочный звонок')
        OTHER = 'Другое', _('Другое')

    # Когда и от кого
    datetime = models.DateTimeField(verbose_name='Дата и время')
    num_from = models.CharField(max_length=30, verbose_name='Исходящий')
    num_to = models.CharField(max_length=30, verbose_name='Входящий')
    num_redirect = models.CharField(max_length=30, verbose_name='Номер переадресации')
    duration = models.IntegerField(verbose_name='Длительность')

    # Марка и Модель
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Марка')
    model = models.ForeignKey(Model, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Модель')

    # Статус и стоимость
    target = models.CharField(max_length=100, blank=True, null=True, choices=TargetChoice.choices,
                              verbose_name='Целевой')
    moderation = models.CharField(max_length=100, blank=True, null=True, choices=ModerationChoice.choices,
                                  verbose_name='М')
    call_price = models.IntegerField(blank=True, null=True, verbose_name='Стоимость звонка')
    manual_call_price = models.BooleanField(default=False, verbose_name='Ручное редактирование стоимости звонка')
    status = models.CharField(max_length=100, blank=True, null=True, choices=StatusChoice.choices,
                              verbose_name='Статус звонка')

    # Остальная информация из разговора
    other_comments = models.CharField(max_length=500, blank=True, null=True, verbose_name='Остальные комментарии')
    client_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя клиента')
    manager_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя менеджера')

    # Характеристики автомобиля
    car_price = models.IntegerField(blank=True, null=True, verbose_name='Стоимость автомобиля')
    color = models.CharField(max_length=100, blank=True, null=True, choices=Colors.choices, verbose_name='Цвет')
    body = models.CharField(max_length=100, blank=True, null=True, choices=BodyTypes.choices, verbose_name='Кузов')
    drive = models.CharField(max_length=100, blank=True, null=True, choices=DriveTypes.choices, verbose_name='Привод')
    engine = models.CharField(max_length=100, blank=True, null=True, choices=EngineTypes.choices,
                              verbose_name='Двигатель')
    # TODO когда будет готова модель Комплектации, поменять здесь на ForeignKey
    complectation = models.CharField(max_length=500, blank=True, null=True, verbose_name='Комплектация')

    attention = models.BooleanField(default=False, verbose_name='Обратить внимание')
    city = models.CharField(max_length=500, blank=True, null=True, verbose_name='Город')
    record = models.URLField(blank=True, null=True, verbose_name='Ссылка на запись звонка')

    # Данные Примател
    primatel_call_id = models.CharField(max_length=500, blank=True, null=True, verbose_name='id звонка Примател')
    client_primatel = models.ForeignKey(ClientPrimatel, on_delete=models.PROTECT, verbose_name='Клиент Примател')
    sip_primatel = models.ForeignKey(SipPrimatel, on_delete=models.PROTECT, verbose_name='Sip')

    # Данные колтач
    calltouch_data = models.ForeignKey('CalltouchData', blank=True, null=True, on_delete=models.SET_NULL,
                                       verbose_name='Данные Calltouch')

    def __str__(self):
        return f'{self.client_primatel.name} | {self.num_from} | {self.datetime}'

    class Meta:
        db_table = 'calls_call'
        verbose_name = 'Звонок'
        verbose_name_plural = 'Звонки'


class ChargeTypeChoice(models.TextChoices):
    MAIN = 'Общая', _('Общая')
    MODERATION = 'Модерация', _('Модерация')
    MARK = 'Марка', _('Марка')
    MODEL = 'Модель', _('Модель')


class CallPriceSetting(BaseModel):
    client_primatel = models.ForeignKey(ClientPrimatel, on_delete=models.CASCADE, verbose_name='Клиент Примател',
                                        related_name='call_price_settings')
    charge_type = models.CharField(max_length=255, choices=ChargeTypeChoice.choices, verbose_name='Тип')
    moderation = ChoiceArrayField(models.CharField(
        max_length=255, choices=ModerationChoice.choices, default=list
    ), verbose_name='Модерация')
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Марка')
    model = models.ForeignKey(Model, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Модель')
    price = models.IntegerField(verbose_name='Стоимость звонка')

    def __str__(self):
        return f'{self.client_primatel.name} | {self.charge_type} | {self.price}'

    # TODO при сохранении нужно проверять по charge_type чтобы остальные поля были верно заполнены.
    #  Например если charge_type Модель то должны быть заполнены moderation, mark, model
    #  А если charge_type Марка то должны быть заполнены moderation, mark и пустая model

    class Meta:
        db_table = 'calls_call_price_setting'
        verbose_name = 'Настройка стоимости звонка'
        verbose_name_plural = 'Настройки стоимости звонка'


class CalltouchSetting(BaseModel):
    client_primatel = models.ForeignKey(ClientPrimatel, on_delete=models.CASCADE, verbose_name='Клиент Примател',
                                        related_name='calltouch_settings')
    active = models.BooleanField(default=True, verbose_name='Активно')
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, verbose_name='Марка')
    site_id = models.CharField(max_length=10, verbose_name='siteId')
    token = models.CharField(max_length=500, verbose_name='token')

    def __str__(self):
        return f'{self.client_primatel.name} | {self.mark.mark} | {self.site_id}'

    class Meta:
        db_table = 'calls_calltouch_setting'
        verbose_name = 'Настройка Calltouch'
        verbose_name_plural = 'Настройки Calltouch'


class CalltouchData(BaseModel):
    calltouch_call_id = models.CharField(max_length=100, verbose_name='id звонка в Calltouch')
    timestamp = models.IntegerField(verbose_name='timestamp')
    datetime = models.DateTimeField(verbose_name='Дата и время')
    num_from = models.CharField(max_length=30, verbose_name='Исходящий')
    num_to = models.CharField(max_length=30, verbose_name='Входящий')
    duration = models.IntegerField(verbose_name='Длительность')
    site_id = models.CharField(max_length=10, verbose_name='siteId')
    call_tags = models.JSONField(default=list, blank=True, null=True, verbose_name='Теги')
    site_name = models.CharField(max_length=100, verbose_name='Аккаунт Calltouch')
    source = models.CharField(max_length=100, verbose_name='Источник')
    successful = models.BooleanField(verbose_name='Успешный')
    target = models.BooleanField(verbose_name='Целевой')
    unique = models.BooleanField(verbose_name='Уникальный')
    unique_target = models.BooleanField(verbose_name='Уникальный целевой')

    def __str__(self):
        return f'{self.site_name} | {self.num_from} | {self.num_to} | {self.datetime}'

    class Meta:
        db_table = 'calls_calltouch_data'
        verbose_name = 'Данные Calltouch'
        verbose_name_plural = 'Данные Calltouch'
