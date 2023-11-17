from rest_framework import serializers

from .models import *


class AutoruParsedAdSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoruParsedAd
        fields = "__all__"

