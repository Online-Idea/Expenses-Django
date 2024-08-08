from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.db.models import Q

# from libs.services.models import Client
from applications.accounts.models import Client, AccountClient


class ClientChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_clients = forms.BooleanField(required=False,
                                            widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    # TODO когда будет настроена группа пользователей Клиент, поменять здесь чтобы фильтровались по этой группе
    # AccountClient.objects.filter(account=current_user)
    # clients = Client.objects.filter(Q(active=True)).order_by('name')
    # client_checkbox = forms.ModelMultipleChoiceField(queryset=clients,
    #                                                  widget=forms.CheckboxSelectMultiple(attrs={'checked': True}))
    client_checkbox = forms.ModelMultipleChoiceField(
        queryset=Client.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'checked': True}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ClientChooseForm, self).__init__(*args, **kwargs)
        if user:
            filters = {'active': True, }
            groups = user.groups.all().values_list('name', flat=True)
            # Для админа доступны все Клиенты, для остальных только те что назначены
            if 'admin' not in groups:
                filters['accountclient__account'] = user

            self.fields['client_checkbox'].queryset = Client.objects.filter(**filters).order_by('name')


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Логин'
    }))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Пароль'
    }))
