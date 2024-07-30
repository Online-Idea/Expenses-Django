from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.db.models import Q

# from libs.services.models import Client
from applications.accounts.models import Client


class ClientChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_clients = forms.BooleanField(required=False,
                                            widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    # Исключаю пользователей-админов
    # TODO когда будет настроена группа пользователей Клиент, поменять здесь чтобы фильтровались по этой группе
    group = Group.objects.get(name='admin')
    clients = Client.objects.filter(~Q(groups=group), Q(active=True)).order_by('name')
    client_checkbox = forms.ModelMultipleChoiceField(queryset=clients,
                                                     widget=forms.CheckboxSelectMultiple(attrs={'checked': True}))


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Логин'
    }))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Пароль'
    }))
