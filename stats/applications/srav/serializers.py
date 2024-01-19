from rest_framework import serializers

from .models import *
from libs.services.serializers import MarkSerializer


class AutoruParsedAdSerializer(serializers.ModelSerializer):
    mark = MarkSerializer(read_only=True)

    class Meta:
        model = AutoruParsedAd
        fields = "__all__"

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['mark'] = instance.mark.mark
        rep['model'] = instance.model.model
        return rep

