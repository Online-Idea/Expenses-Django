from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms
from django.forms.widgets import DateTimeInput
from django.utils import timezone

from applications.calls.models import Call, ClientPrimatel, ClientPrimatelMark
from applications.mainapp.models import Mark, Model


class LocalDatetimeInput(DateTimeInput):
    input_type = 'datetime-local'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        if value:
            value = value.isoformat()
        return super().render(name, value, attrs, renderer)


class CallForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = ['client_primatel', 'datetime', 'num_from', 'num_to', 'duration', 'mark', 'model', 'num_to',
                  'moderation', 'status', 'other_comments', 'call_price',  'client_name',
                  'manager_name', 'car_price', 'color', 'body', 'drive', 'engine', 'complectation',
                  'city', 'num_redirect', 'record', 'manual_edit', 'attention', ]
        widgets = {
            'datetime': LocalDatetimeInput(format='%Y-%m-%dT%H:%M:%S', attrs={'type': 'datetime-local', 'step': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'client_primatel' in self.initial:
            client_primatel = [ClientPrimatel.objects.get(pk=self.initial['client_primatel'])]
        else:
            client_primatel = ClientPrimatel.objects.filter(active=True).order_by('name')
        client_primatel_marks = (ClientPrimatelMark.objects.filter(client_primatel__in=client_primatel)
                                 .values_list('mark', flat=True))
        client_primatel_marks = list(client_primatel_marks)
        self.fields['mark'].queryset = Mark.objects.filter(id__in=client_primatel_marks)
        self.fields['model'].queryset = Model.objects.filter(mark__id__in=client_primatel_marks)

        self.helper = create_layout_from_list(self.Meta.fields, 4)


def create_layout_from_list(field_list, columns_per_row):
    """
    Создаёт Layout от crispy_forms, разбивая список полей на нужное количество столбцов
    :param field_list: список полей
    :param columns_per_row: столбцов в каждом ряду
    :return: FormHelper с настроенным layout
    """
    col_size = int(12 / columns_per_row)

    helper = FormHelper()
    rows = []
    current_row = Row()

    for field_name in field_list:
        current_row.append(Column(field_name, css_class=f'col-md-{col_size}'))
        if len(current_row) == columns_per_row:
            rows.append(current_row)
            current_row = Row()  # Start a new row

    # Add the last row if it has any columns
    if current_row:
        rows.append(current_row)

    helper.layout = Layout(*rows)
    return helper
