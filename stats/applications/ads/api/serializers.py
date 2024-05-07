from rest_framework import serializers
from applications.ads.models import Ad, Mark, Model


class AdSerializer(serializers.ModelSerializer):
    # Кастомные поле для вычисляемых данных
    mark_name = serializers.StringRelatedField(source='mark.mark', read_only=True)
    model_name = serializers.StringRelatedField(source='model.model', read_only=True)
    good_price = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()
    price_nds_display = serializers.SerializerMethodField()
    modification_display = serializers.SerializerMethodField()
    availability_display = serializers.SerializerMethodField()
    first_photo = serializers.SerializerMethodField()
    run_display = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            'mark_name', 'model_name', 'complectation', 'body_type', 'year', 'color', 'original_vin',
            'good_price', 'price_display', 'run_display', 'price_nds_display', 'availability_display',
            'absolute_url', 'first_photo', 'modification_display'
        ]

    @staticmethod
    def get_good_price(obj):
        return obj.get_good_price()

    @staticmethod
    def get_price_display(obj):
        return obj.get_price_display()

    @staticmethod
    def get_run_display(obj):
        return obj.get_run_display()

    @staticmethod
    def get_price_nds_display(obj):
        return obj.get_price_nds_display()

    @staticmethod
    def get_availability_display(obj):
        return obj.get_availability_display()

    @staticmethod
    def get_first_photo(obj):
        return obj.get_first_photo()

    @staticmethod
    def get_modification_display(obj):
        return obj.get_modification_display()

    @staticmethod
    def get_absolute_url(obj):
        return obj.get_absolute_url()


class MarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mark
        fields = ['id', 'name']


class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields = ['id', 'name']


class ModificationSerializer(serializers.ModelSerializer):
    modification_display = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = ['modification_display']

    @staticmethod
    def get_modification_display(obj):
        return obj.get_modification_display()