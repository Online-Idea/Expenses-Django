from rest_framework import serializers

from applications.calls.calls import calculate_call_price
from applications.calls.models import Call, TargetChoice


class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = ['mark', 'model', 'target', 'other_comments', 'client_primatel', 'client_name', 'manager_name',
                  'moderation', 'car_price', 'status', 'call_price', 'manual_call_price', 'color', 'body', 'drive',
                  'engine', 'complectation', 'attention', 'city']

    def update(self, instance, validated_data):
        # Если Ручное редактирование стоимости звонка не отмечено
        if not validated_data['manual_call_price']:
            # Заполняю стоимость звонка в зависимости от настроек из CallPriceSetting
            validated_data['call_price'] = calculate_call_price(instance, validated_data)

        if not validated_data['mark']:
            validated_data['model'] = None

        return super().update(instance, validated_data)
