import locale

from django.db import models
from django.urls import reverse

from libs.services.models import BaseModel, Client, Model, Mark, BodyTypes, Colors


# TODO доделать эту если придут мысли что ещё добавить
class Salon(BaseModel):
    client = models.ManyToManyField(Client)
    name = models.CharField(max_length=255, verbose_name='Название')
    price_url = models.CharField(max_length=2000, verbose_name='Ссылка на прайс')
    datetime_updated = models.DateTimeField(verbose_name='Время последнего обновления')
    # дописать


class Ad(BaseModel):
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, related_name='ads', verbose_name='Марка')
    model = models.ForeignKey(Model, on_delete=models.PROTECT, related_name='ads', verbose_name='Модель')
    configuration = models.CharField(max_length=255, verbose_name='Комплектация')
    price = models.IntegerField(verbose_name='Цена')
    body_type = models.CharField(max_length=64, choices=BodyTypes.choices, verbose_name='Кузов')
    year = models.IntegerField(verbose_name='Год выпуска')
    color = models.CharField(max_length=64, choices=Colors.choices, verbose_name='Цвет')
    description = models.TextField(blank=True, verbose_name='Описание')
    vin = models.CharField(max_length=17, blank=True, verbose_name='VIN')
    photo = models.CharField(max_length=10500, blank=True, verbose_name='Ссылка на фото')
    datetime_created = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Дата создания")
    datetime_updated = models.DateTimeField(auto_now=True, editable=False, verbose_name="Дата обновления")

    def __str__(self):
        return f'{self.mark} | {self.model} | {self.price} | {self.vin}'

    class Meta:
        db_table = 'ads_ad'
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'

    def get_first_photo(self) -> str:
        if not self.photo:
            return ''

        photo_links: list[str] = self.photo.split(', ')

        if not photo_links:
            return ''

        return photo_links[0]

    def get_additional_photos(self):
        """
        Метод для получения списка дополнительных фотографий.
        """
        if self.photo:
            return self.photo.split(', ')  # Бывает запятая, пробел или вместе всё
        else:
            return []


    def get_additional_photos_enum(self):
        return enumerate(self.get_additional_photos())


    def get_price_display(self):
        # Установка локали на основе текущей системы
        locale.setlocale(locale.LC_ALL, '')
        # Форматирование числа с разделителями разрядов
        formatted_price = locale.format_string("%d", self.price, grouping=True)

        return formatted_price + ' ₽'

    def get_absolute_url(self):
        return reverse('ads_app:ad_detail', args=[str(self.pk)])