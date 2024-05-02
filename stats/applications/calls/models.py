from django.db import models
from django.utils.translation import gettext_lazy as _

from applications.accounts.models import Client
from libs.services.choices import DriveTypes, EngineTypes
from libs.services.models import BaseModel, Mark, Model, Colors, BodyTypes


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
    main_mark = models.ForeignKey(Mark, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Марка')
    price = models.IntegerField(blank=True, null=True, verbose_name='Общая цена')
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


class Call(BaseModel):
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

    call_id = models.CharField(max_length=500, blank=True, null=True, verbose_name='id звонка')
    datetime = models.DateTimeField(verbose_name='Дата и время')
    num_from = models.CharField(max_length=30, verbose_name='Исходящий')
    num_to = models.CharField(max_length=30, verbose_name='Входящий')
    duration = models.IntegerField(verbose_name='Длительность')
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Марка')
    model = models.ForeignKey(Model, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Модель')
    target = models.CharField(max_length=100, blank=True, null=True, choices=TargetChoice.choices,
                              verbose_name='Целевой')
    other_comments = models.CharField(max_length=500, blank=True, null=True, verbose_name='Остальные комментарии')
    client_primatel = models.ForeignKey(ClientPrimatel, on_delete=models.PROTECT, verbose_name='Клиент Примател')
    sip_primatel = models.ForeignKey(SipPrimatel, on_delete=models.PROTECT, verbose_name='Sip')
    client_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя клиента')
    manager_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя менеджера')
    moderation = models.CharField(max_length=100, blank=True, null=True, choices=ModerationChoice.choices,
                                  verbose_name='М')
    price = models.IntegerField(blank=True, null=True, verbose_name='Стоимость автомобиля')
    status = models.CharField(max_length=100, blank=True, null=True, choices=StatusChoice.choices,
                              verbose_name='Статус звонка')
    call_price = models.IntegerField(blank=True, null=True, verbose_name='Стоимость звонка')
    manual_call_price = models.BooleanField(default=False, verbose_name='Ручное редактирование стоимости звонка')
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

    def __str__(self):
        return f'{self.client_primatel.name} | {self.num_from} | {self.datetime}'

    class Meta:
        db_table = 'calls_call'
        verbose_name = 'Звонок'
        verbose_name_plural = 'Звонки'

