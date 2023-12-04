from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.generic import FormView

from applications.autoconverter.converter import *
from applications.autoconverter.forms import ConverterManualForm
from applications.autoconverter.models import *
from libs.services.decorators import allowed_users


@method_decorator(allowed_users(allowed_groups=['admin']), name='dispatch')
class ConverterManual(SuccessMessageMixin, FormView):
    template_name = 'autoconverter/converter_manual.html'
    ordering = ['client']
    form_class = ConverterManualForm
    success_url = 'converter'
    success_message = format_html('Готово, файлы в <a href="https://t.me/ConverterLogsBot">телеграме</a>')

    def form_valid(self, form):
        tasks = form.cleaned_data['task_checkbox']
        for task in tasks:
            get_price(ConverterTask.objects.get(pk=task.id))
        return super().form_valid(form)


def photo_folders(request):
    get_photo_folders()
    return redirect('home')


def configurations(request):
    get_configurations()
    return redirect('home')

