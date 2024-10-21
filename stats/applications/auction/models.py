from django.db import models

from libs.services.models import BaseModel
from applications.mainapp.models import Mark, Model
from applications.accounts.models import Client


class AutoruAuctionHistory(BaseModel):
    datetime = models.DateTimeField(verbose_name='Дата и время')
    autoru_region = models.CharField(max_length=500, verbose_name='Регион')
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT)
    model = models.ForeignKey(Model, on_delete=models.PROTECT)
    position = models.IntegerField(verbose_name='Позиция')
    bid = models.IntegerField(verbose_name='Ставка')
    competitors = models.IntegerField(verbose_name='Количество конкурентов с этой ставкой')
    client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.PROTECT)
    dealer = models.CharField(max_length=500, null=True, blank=True, verbose_name='Дилер')

    def __str__(self):
        return f'{self.datetime} | {self.autoru_region} | {self.mark.name} | {self.model.name} | {self.position} | {self.bid}'

    class Meta:
        db_table = 'auction_autoru_auction_history'
        verbose_name = 'Авто.ру История Аукциона'
        verbose_name_plural = 'Авто.ру История Аукциона'

