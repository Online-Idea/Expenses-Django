from django.db import models

from libs.services.models import BaseModel, Mark, Model, CustomBooleanField
from applications.accounts.models import Client


class AutoruParsedAd(BaseModel):
    datetime = models.DateTimeField(verbose_name='Дата и время', db_index=True)
    region = models.CharField(max_length=500, verbose_name='Регион', db_index=True)
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, db_index=True)
    model = models.ForeignKey(Model, on_delete=models.PROTECT)
    complectation = models.CharField(null=True, blank=True, max_length=500, verbose_name='Комплектация')
    modification = models.CharField(null=True, blank=True, max_length=500, verbose_name='Модификация')
    year = models.IntegerField(verbose_name='Год')
    dealer = models.CharField(max_length=500, verbose_name='Имя дилера', db_index=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, null=True, blank=True)
    price_with_discount = models.IntegerField(verbose_name='Цена со скидками')
    price_no_discount = models.IntegerField(verbose_name='Цена без скидок')
    with_nds = models.BooleanField(verbose_name='Цена с НДС')
    position_actual = models.IntegerField(verbose_name='Позиция по актуальности')
    position_total = models.IntegerField(verbose_name='Позиция общая')
    link = models.CharField(max_length=1000, verbose_name='Ссылка')
    condition = models.CharField(max_length=500, verbose_name='Состояние/пробег')
    in_stock = models.CharField(max_length=500, verbose_name='Наличие')
    services = models.CharField(max_length=500, null=True, blank=True, verbose_name='Услуги')
    tags = models.CharField(max_length=500, null=True, blank=True, verbose_name='Стикеры')
    photos = models.IntegerField(verbose_name='Количество фото')

    def __str__(self):
        return f'{self.mark} | {self.model} | {self.complectation} | {self.dealer}'

    class Meta:
        db_table = 'srav_autoru_parsed_ad'
        verbose_name = 'Спарсенное объявление авто.ру'
        verbose_name_plural = 'Спарсенные объявления авто.ру'


class SravPivot(BaseModel):
    autoru_parsed_ad = models.ForeignKey(AutoruParsedAd, on_delete=models.CASCADE)
    position_price = models.IntegerField(verbose_name='Позиция по цене')
    in_stock_count = models.IntegerField(verbose_name='В наличии')
    for_order_count = models.IntegerField(verbose_name='Под заказ')

    def __str__(self):
        return f'{self.autoru_parsed_ad} | {self.position_price}'

    class Meta:
        db_table = 'srav_srav_pivot'
        verbose_name = 'Сравнительная'
        verbose_name_plural = 'Сравнительная'


def fill_mark_from_autoru_parsed_ad():
    """
    Наполняет уникальными Марками из AutoruParsedAd. Только для первичного заполнения UniqueAutoruParsedAdMark
    :return:
    """
    mark_values = AutoruParsedAd.objects.values_list('mark', flat=True).distinct()
    marks_objs = Mark.objects.filter(id__in=mark_values)
    new_objs = [UniqueAutoruParsedAdMark(mark=mark) for mark in marks_objs]
    UniqueAutoruParsedAdMark.objects.bulk_create(new_objs)


class UniqueAutoruParsedAdMark(BaseModel):
    """
    Эта модель для уникальных Марок которые есть в AutoruParsedAd. Т.к. записей в AutoruParsedAd становится много,
    то уходит много времени на то чтобы собрать уникальные значения для формы на сайте.
    """
    mark = models.OneToOneField(Mark, on_delete=models.CASCADE, verbose_name='Марка')

    def __str__(self):
        return f'{self.mark}'

    class Meta:
        db_table = 'srav_unique_autoru_parsed_ad_mark'
        verbose_name = 'Уникальная Марка из спарсенных объявлений авто.ру'
        verbose_name_plural = 'Уникальные Марки из спарсенных объявлений авто.ру'


def fill_region_from_autoru_parsed_ad():
    """
    Наполняет уникальными Регионами из AutoruParsedAd. Только для первичного заполнения UniqueAutoruParsedAdRegion
    :return:
    """
    regions_values = AutoruParsedAd.objects.values_list('region', flat=True).distinct()
    new_objs = [UniqueAutoruParsedAdRegion(region=region) for region in regions_values]
    UniqueAutoruParsedAdRegion.objects.bulk_create(new_objs)


class UniqueAutoruParsedAdRegion(BaseModel):
    """
    Эта модель для уникальных Регионов которые есть в AutoruParsedAd. Т.к. записей в AutoruParsedAd становится много,
    то уходит много времени на то чтобы собрать уникальные значения для формы на сайте.
    """
    region = models.CharField(max_length=500, unique=True, verbose_name='Регион')

    def __str__(self):
        return f'{self.region}'

    class Meta:
        db_table = 'srav_unique_autoru_parsed_ad_region'
        verbose_name = 'Уникальный Регион из спарсенных объявлений авто.ру'
        verbose_name_plural = 'Уникальные Регионы из спарсенных объявлений авто.ру'


def fill_dealer_from_autoru_parsed_ad():
    """
    Наполняет уникальными Дилерами из AutoruParsedAd. Только для первичного заполнения UniqueAutoruParsedAdDealer
    :return:
    """
    dealer_values = AutoruParsedAd.objects.values_list('dealer', flat=True).distinct()
    new_objs = [UniqueAutoruParsedAdDealer(dealer=dealer) for dealer in dealer_values]
    UniqueAutoruParsedAdDealer.objects.bulk_create(new_objs)


class UniqueAutoruParsedAdDealer(BaseModel):
    """
    Эта модель для уникальных Дилеров которые есть в AutoruParsedAd. Т.к. записей в AutoruParsedAd становится много,
    то уходит много времени на то чтобы собрать уникальные значения для формы на сайте.
    """
    dealer = models.CharField(max_length=500, unique=True, verbose_name='Имя дилера')

    def __str__(self):
        return f'{self.dealer}'

    class Meta:
        db_table = 'srav_unique_autoru_parsed_ad_dealer'
        verbose_name = 'Уникальный Дилер из спарсенных объявлений авто.ру'
        verbose_name_plural = 'Уникальные Дилеры из спарсенных объявлений авто.ру'
