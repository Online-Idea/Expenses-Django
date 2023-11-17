from rest_framework import serializers

from libs.services.models import Client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('name', 'manager', 'active')


