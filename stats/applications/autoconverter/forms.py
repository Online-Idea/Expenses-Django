from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit

from applications.autoconverter.models import ConverterTask


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
