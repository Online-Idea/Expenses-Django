from rest_framework import serializers

from .models import *
from libs.services.serializers import MarkSerializer


class AutoruParsedAdSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoruParsedAd
        fields = "__all__"

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['mark'] = instance.mark.name
        rep['model'] = instance.model.name
        return rep

