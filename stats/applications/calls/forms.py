from django import forms

from applications.accounts.models import Client
from applications.calls.models import Call, ClientPrimatel, ClientPrimatelMark
from libs.services.models import Mark, Model


class CallChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_clients = forms.BooleanField(required=False,
                                            widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    client_checkbox = forms.ModelMultipleChoiceField(queryset=Client.objects.filter(active=True),
                                                     widget=forms.CheckboxSelectMultiple(attrs={'checked': True}))


class CallForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = ['mark', 'model', 'target', 'other_comments', 'client_primatel', 'client_name', 'manager_name', 'moderation', 'price',
                  'status', 'call_price', 'manual_call_price', 'color', 'body', 'drive', 'engine', 'complectation',
                  'attention', 'city']
        widgets = {
            'client_primatel': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client_primatel = ClientPrimatel.objects.get(pk=self.initial['client_primatel'])
        client_primatel_marks = (ClientPrimatelMark.objects.filter(client_primatel=client_primatel)
                                 .values_list('mark', flat=True))
        client_primatel_marks = list(client_primatel_marks)
        client_primatel_marks.append(client_primatel.main_mark.pk)
        self.fields['mark'].queryset = Mark.objects.filter(id__in=client_primatel_marks)
        self.fields['model'].queryset = Model.objects.filter(mark__id__in=client_primatel_marks)
