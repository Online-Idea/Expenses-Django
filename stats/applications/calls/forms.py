from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms

from applications.accounts.models import Client
from applications.calls.models import Call, ClientPrimatel, ClientPrimatelMark
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
        fields = ['mark', 'model', 'target', 'moderation', 'status', 'other_comments', 'call_price',
                  'manual_call_price', 'client_name', 'manager_name', 'car_price', 'color', 'body', 'drive',
                  'engine', 'complectation', 'attention', 'city', 'client_primatel', ]
        widgets = {
            'client_primatel': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client_primatel = ClientPrimatel.objects.get(pk=self.initial['client_primatel'])
        client_primatel_marks = (ClientPrimatelMark.objects.filter(client_primatel=client_primatel)
                                 .values_list('mark', flat=True))
        client_primatel_marks = list(client_primatel_marks)
        self.fields['mark'].queryset = Mark.objects.filter(id__in=client_primatel_marks)
        self.fields['model'].queryset = Model.objects.filter(mark__id__in=client_primatel_marks)

        self.helper = create_layout_from_list(self.Meta.fields, 3)


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
