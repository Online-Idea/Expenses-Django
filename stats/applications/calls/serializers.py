from django.contrib.auth.models import Group, User
from rest_framework import serializers

from applications.accounts.models import Client
from applications.calls.models import Call


class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = ['mark', 'model', 'target', 'other_comments', 'client_primatel', 'client_name', 'manager_name',
                  'moderation', 'price', 'status', 'call_price', 'manual_call_price', 'color', 'body', 'drive',
                  'engine', 'complectation', 'attention', 'city']

