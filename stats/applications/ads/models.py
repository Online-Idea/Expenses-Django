from django.db import models

from libs.services.models import BaseModel, Client


# TODO доделать эту если придут мысли что ещё добавить
class Salon(BaseModel):
    client = models.ManyToManyField(Client)
    name = models.CharField(max_length=255, verbose_name='Название')
    price_url = models.CharField(max_length=2000, verbose_name='Ссылка на прайс')
    datetime_updated = models.DateTimeField(verbose_name='Время последнего обновления')
