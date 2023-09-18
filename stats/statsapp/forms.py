from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit
from django import forms

from .models import *


class ClientsChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_clients = forms.ChoiceField(required=False,
                                           widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    client_checkbox = forms.ModelMultipleChoiceField(
        queryset=Clients.objects.filter(active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'checked': True}),
    )


class AuctionChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_marks = forms.ChoiceField(required=False,
                                         widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    mark_checkbox = forms.ModelMultipleChoiceField(
        queryset=Marks.objects.filter(id__in=AutoruAuctionHistory.objects.values('mark').distinct()),
        widget=forms.CheckboxSelectMultiple(attrs={'checked': True}),
    )
    select_all_regions = forms.ChoiceField(required=False,
                                           widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    region_checkbox = forms.ModelMultipleChoiceField(
        queryset=AutoruAuctionHistory.objects.order_by('autoru_region').values_list('autoru_region', flat=True).distinct(),
        widget=forms.CheckboxSelectMultiple(attrs={'checked': True})
    )


# class ConverterManualForm(forms.Form):
#     task_checkbox = forms.ModelMultipleChoiceField(
#         queryset=ConverterTask.objects.filter(active=True),
#         widget=forms.CheckboxSelectMultiple,
#         label='Задачи'
#     )


class ConverterManualForm(forms.Form):
    task_checkbox = forms.ModelMultipleChoiceField(
        queryset=ConverterTask.objects.filter(active=True),
        widget=forms.CheckboxSelectMultiple,
        label=''
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.field_class = 'col-lg-10'
        self.helper.attrs = {'onsubmit': 'showLoading()'}
        self.helper.layout = Layout(
            Fieldset(
                'Задачи',
                'task_checkbox',
            ),
            ButtonHolder(
                Submit('submit', 'Запустить', css_class='btn-primary')
            )
        )
