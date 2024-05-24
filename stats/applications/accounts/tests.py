from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import Group
from applications.accounts.models import Client

group = Group.objects.get(name='admin')
users_group = Client.objects.filter(groups=group)
for user in users_group:
    print(user.username)