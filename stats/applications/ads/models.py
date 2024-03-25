import decimal
import re
import locale
from typing import Union, List, Tuple, Any

from django.db import models
from django.urls import reverse

from libs.services.models import BaseModel, Model, Mark, Client, BodyTypes, Colors
# from applications.accounts.models import Client


# TODO доделать эту если придут мысли что ещё добавить
class Salon(BaseModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='salons')
    name = models.CharField(max_length=255, verbose_name='Название')
    price_url = models.CharField(max_length=2000, verbose_name='Ссылка на прайс')
    datetime_updated = models.DateTimeField(verbose_name='Время последнего обновления')
    city = models.CharField(max_length=255, verbose_name='Город салона')
    adress = models.CharField(max_length=255, verbose_name='Адрес')
    telephone = models.CharField(max_length=255, verbose_name='Телефон')


class Ad(BaseModel):
    """
    Модель объявления.
    """
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, related_name='ads', verbose_name='Марка')
    model = models.ForeignKey(Model, on_delete=models.PROTECT, related_name='ads', verbose_name='Модель')
    complectation = models.CharField(max_length=255, verbose_name='Комплектация')
    price = models.IntegerField(verbose_name='Цена')
    body_type = models.CharField(max_length=64, choices=BodyTypes.choices, verbose_name='Кузов')
    year = models.IntegerField(verbose_name='Год выпуска')
    color = models.CharField(max_length=64, choices=Colors.choices, verbose_name='Цвет')
    description = models.TextField(blank=True, verbose_name='Описание')
    original_vin = models.CharField(max_length=17, null=True, blank=True, verbose_name='Исходный VIN')
    vin = models.CharField(max_length=17, null=True, blank=True, verbose_name='VIN')
    photo = models.CharField(max_length=10500, blank=True, verbose_name='Ссылка на фото')
    price_nds = models.CharField(max_length=8, null=True, blank=True, verbose_name='Цена c НДС')
    engine_capacity = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                          verbose_name='Объём двигателя')
    power = models.IntegerField(blank=True, verbose_name='Мощность')
    engine_type = models.CharField(max_length=32, blank=True, verbose_name='Тип двигателя')
    transmission = models.CharField(max_length=16, blank=True, verbose_name='Коробка передач')
    drive = models.CharField(max_length=32, blank=True, verbose_name='Привод')
    modification = models.CharField(max_length=128, blank=True, verbose_name='Модификация')
    trade_in = models.IntegerField(null=True, blank=True, verbose_name='Трейд-ин')
    credit = models.IntegerField(null=True, blank=True, verbose_name='Кредит')
    insurance = models.IntegerField(null=True, blank=True, verbose_name='Страховка')
    max_discount = models.IntegerField(null=True, blank=True, verbose_name='Максимальная скидка')
    condition = models.CharField(max_length=16, null=True, blank=True, verbose_name='Состояние машины')
    run = models.IntegerField(null=True, blank=True, default=0, verbose_name='Пробег')
    modification_code = models.CharField(max_length=32, null=True, blank=True, verbose_name='Код модификации')
    color_code = models.CharField(max_length=16, null=True, blank=True, verbose_name='Код цвета')
    interior_code = models.CharField(max_length=16, null=True, blank=True, verbose_name='Код интерьера')
    configuration_codes = models.CharField(max_length=1024, null=True, blank=True,
                                           verbose_name='Коды опций комплектации')
    stickers_autoru = models.CharField(max_length=128, null=True, blank=True, verbose_name='Стикеры авто.ру')
    video = models.CharField(max_length=128, null=True, blank=True, verbose_name='Ссылка на видео')
    telephone = models.CharField(max_length=16, null=True, blank=True, verbose_name='Номер телефона')
    availability = models.CharField(max_length=32, null=True, blank=True, verbose_name='Наличие')
    id_model_autoru = models.IntegerField(null=True, blank=True, verbose_name='ID модели на авто.ру')
    id_modification_autoru = models.IntegerField(null=True, blank=True, verbose_name='ID модификации на авто.ру')
    modification_autoru = models.CharField(max_length=64, null=True, blank=True, verbose_name='Модификация авто.ру')
    configuration_autoru = models.CharField(max_length=255, null=True, blank=True, verbose_name='Комплектация авто.ру')
    status = models.CharField(max_length=16, null=True, blank=True, verbose_name='Статус продажи')
    id_client = models.CharField(max_length=32, null=True, blank=True, verbose_name='ID от клиента')
    datetime_created = models.DateTimeField(auto_now_add=True, editable=False,
                                            verbose_name="Дата создания и размещения")
    datetime_updated = models.DateTimeField(auto_now=True, editable=False, verbose_name="Дата обновления")

    def __str__(self) -> str:
        return f'{self.mark} | {self.model} | {self.price} | {self.vin}'

    class Meta:
        db_table = 'ads_ad'
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'

    @staticmethod
    def get_formatted_price(price: int, unit: str = '₽') -> str:
        """
        Возвращает отформатированное число по разрядности с единицей измерения.

        :param price: цена для форматирования по разрядности.
        :param unit: Единицы измерения.
        :param empty: Значение для пустого атрибута.

        """
        locale.setlocale(locale.LC_ALL, '')
        formatted_price: str = locale.format_string("%d", price, grouping=True)
        return f'{formatted_price} {unit}'

    @staticmethod
    def is_number(value: Any) -> bool:
        if value is not None and isinstance(value, (int, float, decimal.Decimal)):
            return True
        return False

    @staticmethod
    def get_formatted_value(value: Any, unit: str = '', empty: str = '-') -> str:
        """
        Возвращает форматированное значение атрибута с единицами измерения.

        :param value: Название атрибута.
        :param unit: Единицы измерения.
        :param empty: Значение по умолчанию для пустого атрибута.
        """
        if value is not None:
            return f'{value} {unit}'
        return empty

    def get_absolute_url(self) -> str:
        """
        Возвращает абсолютный URL для детальной страницы объявления.
        """
        return reverse('ads_app:ad_detail', args=[str(self.pk)])

    def get_first_photo(self) -> Union[str, None]:
        """
        Возвращает первое фото из списка фотографий.
        или #, если фотографии отсутствуют.
        """
        return self.get_photos()[0] if self.get_photos() else '#'

    def get_photos(self) -> List[str]:
        """
        Возвращает список ссылок на фотографии.
        """
        if self.photo:
            return list(map(str.strip, self.photo.split(', ')))
        else:
            return []

    def get_photos_enum(self) -> List[Tuple[int, str]]:
        """
        Возвращает перечисление индексов и фотографий для модального окна.
        """
        return list(enumerate(self.get_photos()))

    def get_price_display(self) -> str:
        """
        Возвращает отформатированную цену Авто
        """
        if Ad.is_number(self.price):
            return Ad.get_formatted_price(self.price)
        return '-'

    def get_trade_in_display(self) -> str:
        """
        Возвращает отформатированный цену Трейд-Ин
        """
        if Ad.is_number(self.trade_in):
            return Ad.get_formatted_price(self.trade_in)
        return '-'

    def get_credit_display(self) -> str:
        """
        Возвращает отформатированный размер кредита
        """
        if Ad.is_number(self.credit):
            return Ad.get_formatted_price(self.credit)
        return '-'

    def get_insurance_display(self) -> str:
        """
        Возвращает отформатированное значение страховки
        """
        if Ad.is_number(self.insurance):
            return Ad.get_formatted_price(self.insurance)
        return '-'

    def get_max_discount_display(self) -> str:
        """
        Возвращает отформатированное значение максимальной скидки
        """
        if Ad.is_number(self.max_discount):
            return Ad.get_formatted_price(self.max_discount)
        return '-'

    def get_engine_display(self) -> str:
        """
        Возвращает отформатированный объем двигателя  или '-'
        """
        if Ad.is_number(self.engine_capacity) and self.engine_capacity != 0:
            return Ad.get_formatted_value(self.engine_capacity, 'л')
        return '-'

    def get_run_display(self) -> str:
        """
        Возвращает отформатированный пробег или 'Новая в зависимости от поля "состояние".
        """
        if self.condition == 'Новая':
            return 'Новая'
        return Ad.get_formatted_value(self.run, 'км', 'Новая')

    def get_power_display(self) -> str:
        """
        Возвращает отформатированную мощность двигателя, если пусто, то '-'.
        """
        return Ad.get_formatted_value(self.power, 'л.с.')

    def get_price_nds_display(self) -> str:
        """
        Возвращает цену с НДС, если пусто, то 'Нет'.
        """
        return self.price_nds or 'Нет'

    def get_availability_display(self) -> str:
        """
        Возвращает поле наличие, при пустом поле 'В наличии'
        """
        return self.availability or 'В наличии'

    def get_preview_video(self):
        pattern = (
            r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
        )
        match = re.search(pattern, self.video)
        if match:
            id_ = match.group(1)
            return f'https://img.youtube.com/vi/{id_}/0.jpg'
        return None

    def get_sum_discount_display(self) -> int:
        return self.max_discount or sum(
            [num for num in
             [self.trade_in, self.credit, self.insurance]
             if num]
        )

    def get_good_price(self) -> str:
        new_price = self.price - self.get_sum_discount_display()
        return Ad.get_formatted_price(new_price)

    def get_modification_display(self) -> str:
        return (
            f"{self.get_engine_display()} / {self.get_power_display()} / "
            f"{self.engine_type} / {self.transmission} / {self.drive}"
        )


# class ClientManager(BaseUserManager):
#     def create_user(self, email, password=None, **extra_fields):
#         # Создание обычного пользователя
#         extra_fields.setdefault('is_staff', False)
#         # остальная логика создания пользователя
#
#     def create_superuser(self, email, password=None, **extra_fields):
#         # Создание суперпользователя
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         # остальная логика создания суперпользователя