from rest_framework import serializers

from libs.services.models import Client, Mark


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('name', 'manager', 'active')


class MarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mark
        fields = ['mark']

