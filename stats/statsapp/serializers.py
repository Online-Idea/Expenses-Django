from rest_framework import serializers

from .models import *


class ClientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clients
        fields = ('name', 'manager', 'active')


class AutoruParsedAdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoruParsedAds
        fields = "__all__"
