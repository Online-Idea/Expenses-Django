from django import forms

from applications.accounts.models import Client
from applications.calls.models import Call, ClientPrimatel, ClientPrimatelMark, CallPriceSetting
from applications.calls.widgets import PlayButtonWidget
from libs.services.models import Mark, Model


class CallChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_clients = forms.BooleanField(required=False,
                                            widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    # TODO в queryset брать только клиентов, админа убрать. Ниже примерный код для проверки группы у пользователя
    # from django.contrib.auth.models import Group
    # from applications.accounts.models import Client
    #
    # group = Group.objects.get(name='admin')
    # users_group = Client.objects.filter(groups=group)
    # for user in users_group:
    #     print(user.username)
    client_checkbox = forms.ModelMultipleChoiceField(queryset=Client.objects.filter(active=True).order_by('name'),
                                                     widget=forms.CheckboxSelectMultiple(attrs={'checked': True}))


class CallForm(forms.ModelForm):
    class Meta:
        model = Call
        # TODO поменять порядок на более удобный
        # TODO добавить кнопку плеера для record
        fields = ['mark', 'model', 'target', 'other_comments', 'client_primatel', 'client_name', 'manager_name',
                  'moderation', 'car_price', 'status', 'call_price', 'manual_call_price', 'color', 'body', 'drive',
                  'engine', 'complectation', 'attention', 'city']
        widgets = {
            'client_primatel': forms.HiddenInput(),
            # 'record': PlayButtonWidget(),
        }
        # labels = {
        #     'record': 'Запись звонка',
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client_primatel = ClientPrimatel.objects.get(pk=self.initial['client_primatel'])
        client_primatel_marks = (ClientPrimatelMark.objects.filter(client_primatel=client_primatel)
                                 .values_list('mark', flat=True))
        client_primatel_marks = list(client_primatel_marks)
        self.fields['mark'].queryset = Mark.objects.filter(id__in=client_primatel_marks)
        self.fields['model'].queryset = Model.objects.filter(mark__id__in=client_primatel_marks)
