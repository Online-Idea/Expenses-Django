from django import forms

from .models import *


class ClientsChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    client_checkbox = forms.ModelMultipleChoiceField(
        queryset=Clients.objects.filter(active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'checked': True}),
    )


class ConverterManualForm(forms.Form):
    task_checkbox = forms.ModelMultipleChoiceField(
        queryset=ConverterTask.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Задачи'
    )
