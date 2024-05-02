from django import forms

from applications.accounts.models import Client


class CallChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_clients = forms.BooleanField(required=False,
                                            widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    client_checkbox = forms.ModelMultipleChoiceField(queryset=Client.objects.filter(active=True),
                                                     widget=forms.CheckboxSelectMultiple(attrs={'checked': True}))
