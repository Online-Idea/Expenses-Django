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
    original_vin = models.CharField(max_length=17, null=True, blank=True, verbose_name='Исходный VIN')
    vin = models.CharField(max_length=17, null=True, blank=True, verbose_name='VIN')
    photo = models.CharField(max_length=10500, blank=True, verbose_name='Ссылка на фото')
    price_nds = models.CharField(max_length=8, null=True, blank=True, verbose_name='Цена c НДС')
    engine_capacity = models.IntegerField(null=True, blank=True, verbose_name='Объём двигателя')
    power = models.IntegerField(blank=True, verbose_name='Мощность')
    engine_type = models.CharField(max_length=32, blank=True, verbose_name='Тип двигателя')
    transmission = models.CharField(max_length=16, blank=True, verbose_name='Коробка передач')
    drive = models.CharField(max_length=32, blank=True, verbose_name='Привод')
    trade_in = models.IntegerField(null=True, blank=True, verbose_name='Трейд-ин')
    credit = models.IntegerField(null=True, blank=True, verbose_name='Кредит')
    insurance = models.IntegerField(null=True, blank=True, verbose_name='Страховка')
    max_discount = models.IntegerField(null=True, blank=True, verbose_name='Максимальная скидка')
    condition = models.CharField(max_length=16, null=True, blank=True, verbose_name='Состояние машины')
    run = models.IntegerField(null=True, blank=True, default=0, verbose_name='Пробег')
    modification_code = models.CharField(max_length=32, null=True, blank=True, verbose_name='Код модификации')
    color_code = models.CharField(max_length=16, null=True, blank=True, verbose_name='Код цвета')
    interior_code = models.CharField(max_length=16, null=True, blank=True, verbose_name='Код интерьера')
    configuration_codes = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Коды опций комплектации')
    stickers_autoru = models.CharField(max_length=128, null=True, blank=True, verbose_name='Стикеры авто.ру')
    video = models.CharField(max_length=128, null=True, blank=True, verbose_name='Ссылка на видео')
    telephone = models.CharField(max_length=16, null=True, blank=True, verbose_name='Номер телефона')
    availability = models.CharField(max_length=32, null=True, blank=True, verbose_name='Наличие')
    id_model_autoru = models.IntegerField(null=True, blank=True, verbose_name='ID модели на авто.ру')
    id_modification_autoru = models.IntegerField(null=True, blank=True, verbose_name='ID модификации на авто.ру')
    id_configuration_autoru = models.IntegerField(null=True, blank=True, verbose_name='ID комплектации на авто.ру')
    modification_autoru = models.CharField(max_length=64, null=True, blank=True, verbose_name='Модификация авто.ру')
    configuration_autoru = models.CharField(max_length=255, null=True, blank=True, verbose_name='Комплектация авто.ру')
    status = models.CharField(max_length=16, null=True, blank=True, verbose_name='Статус продажи')
    id_client = models.CharField(max_length=32, null=True, blank=True, verbose_name='ID от клиента')
    currency = models.CharField(max_length=16, null=True, blank=True, verbose_name='Валюта')
    datetime_created = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Дата создания и размещения")
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