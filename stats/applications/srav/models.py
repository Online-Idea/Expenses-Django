from django.db import models

from libs.services.models import BaseModel, Mark, Model, Client, CustomBooleanField


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
