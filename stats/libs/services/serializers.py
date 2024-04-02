from rest_framework import serializers

from applications.accounts.models import Client
from libs.services.models import Mark


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('name', 'manager', 'active')


class MarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mark
        fields = ['mark']

