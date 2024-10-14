from rest_framework import serializers
from applications.ads.models import Ad
from applications.mainapp.models import Mark, Model


class AdSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Ad, который предоставляет вычисляемые данные,
    такие как имя марки, модели, цену, модификацию и т.д.
    """

    # Кастомное поле для отображения имени марки
    mark_name = serializers.StringRelatedField(source='mark.mark', read_only=True)

    # Кастомное поле для отображения имени модели
    model_name = serializers.StringRelatedField(source='model.model', read_only=True)

    # Кастомное поле для вычисляемой цены
    good_priced = serializers.SerializerMethodField()

    # Кастомное поле для отображения цены
    price_display = serializers.SerializerMethodField()

    # Кастомное поле для отображения абсолютного URL
    absolute_url = serializers.SerializerMethodField()

    # Кастомное поле для отображения цены с НДС
    price_nds_display = serializers.SerializerMethodField()

    # Кастомное поле для отображения модификации
    modification_display = serializers.SerializerMethodField()

    # Кастомное поле для отображения доступности
    availability_display = serializers.SerializerMethodField()

    # Кастомное поле для отображения первой фотографии
    first_photo = serializers.SerializerMethodField()

    # Кастомное поле для отображения пробега
    run_display = serializers.SerializerMethodField()

    class Meta:
        """
        Мета-класс для указания модели Ad и полей, которые будут сериализованы.
        """
        model: type = Ad
        fields: list[str] = [
            'mark_name', 'model_name', 'complectation', 'body_type', 'year', 'color', 'original_vin',
            'good_price', 'price_display', 'run_display', 'price_nds_display', 'availability_display',
            'absolute_url', 'first_photo', 'modification_display'
        ]

    @staticmethod
    def get_good_price(obj: Ad) -> str:
        """
        Метод для получения вычисляемой хорошей цены.
        :param obj: Объект Ad
        :return: Строковое представление хорошей цены
        """
        return obj.get_good_price()

    @staticmethod
    def get_price_display(obj: Ad) -> str:
        """
        Метод для получения отображаемой цены.
        :param obj: Объект Ad
        :return: Строковое представление цены
        """
        return obj.get_price_display()

    @staticmethod
    def get_run_display(obj: Ad) -> str:
        """
        Метод для получения отображаемого пробега.
        :param obj: Объект Ad
        :return: Строковое представление пробега
        """
        return obj.get_run_display()

    @staticmethod
    def get_price_nds_display(obj: Ad) -> str:
        """
        Метод для получения отображаемой цены с НДС.
        :param obj: Объект Ad
        :return: Строковое представление цены с НДС
        """
        return obj.get_price_nds_display()

    @staticmethod
    def get_availability_display(obj: Ad) -> str:
        """
        Метод для получения отображаемой доступности.
        :param obj: Объект Ad
        :return: Строковое представление доступности
        """
        return obj.get_availability_display()

    @staticmethod
    def get_first_photo(obj: Ad) -> str:
        """
        Метод для получения первой фотографии.
        :param obj: Объект Ad
        :return: Строковое представление первой фотографии
        """
        return obj.get_first_photo()

    @staticmethod
    def get_modification_display(obj: Ad) -> str:
        """
        Метод для получения отображаемой модификации.
        :param obj: Объект Ad
        :return: Строковое представление модификации
        """
        return obj.get_modification_display()

    @staticmethod
    def get_absolute_url(obj: Ad) -> str:
        """
        Метод для получения абсолютного URL.
        :param obj: Объект Ad
        :return: Строковое представление абсолютного URL
        """
        return obj.get_absolute_url()


class MarkSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Mark.
    """

    class Meta:
        """
        Мета-класс для указания модели Mark и полей, которые будут сериализованы.
        """
        model: type = Mark
        fields: list[str] = ['id', 'name']


class ModelSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Model.
    """

    class Meta:
        """
        Мета-класс для указания модели Model и полей, которые будут сериализованы.
        """
        model: type = Model
        fields: list[str] = ['id', 'name']


class ModificationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения модификации.
    """

    # Кастомное поле для отображения модификации
    modification_display = serializers.SerializerMethodField()

    class Meta:
        """
        Мета-класс для указания модели Ad и полей, которые будут сериализованы.
        """
        model: type = Ad
        fields: list[str] = ['modification_display']

    @staticmethod
    def get_modification_display(obj: Ad) -> str:
        """
        Метод для получения отображаемой модификации.
        :param obj: Объект Ad
        :return: Строковое представление модификации
        """
        return obj.get_modification_display()
