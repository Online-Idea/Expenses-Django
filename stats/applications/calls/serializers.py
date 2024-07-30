from rest_framework import serializers

from applications.calls.calls import calculate_call_price
from applications.calls.models import Call, TargetChoice


class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = ['client_primatel', 'datetime', 'num_from', 'num_to', 'duration', 'mark', 'model', 'target',
                  'moderation', 'status', 'other_comments', 'call_price',  'client_name',
                  'manager_name', 'car_price', 'color', 'body', 'drive', 'engine', 'complectation',
                  'city', 'num_redirect', 'record', 'manual_edit', 'attention', ]

    def update(self, instance, validated_data):
        # Если Ручное редактирование звонка не отмечено
        if not validated_data['manual_edit']:
            # Заполняю стоимость звонка в зависимости от настроек из CallPriceSetting
            validated_data['call_price'] = calculate_call_price(instance, validated_data)

        if not validated_data['mark']:
            validated_data['model'] = None

        return super().update(instance, validated_data)
