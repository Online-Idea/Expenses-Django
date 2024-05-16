from django.contrib.auth.models import Group, User
from rest_framework import serializers

from applications.accounts.models import Client
from applications.calls.models import Call


class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = ['num_from', 'duration', 'mark', 'target']

