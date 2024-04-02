import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.conf import settings

from applications.accounts.forms import ApplicationForm
from applications.accounts.models import Application

EMAIL_HOST_USER = os.environ.get('EMAIL_USER')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'


class RegisterView(CreateView):
    model = Application
    form_class = ApplicationForm
    success_url = reverse_lazy('accounts_app:login')

    def form_valid(self, form):
        print('Форма пришла')
        # Добавляем IP адрес пользователя перед сохранением объекта
        form.instance.user_ip = self.get_client_ip(self.request)
        response = super().form_valid(form)  # Сохраняем объект и получаем ответ
        application = form.instance
        # Отправка уведомления на почту администратора и клиенту
        # self.send_emails(application)
        messages.success(self.request, 'Заявка успешно отправлена!')
        return response

    def form_invalid(self, form):
        # Обработка случая, когда форма невалидна
        for error in form.errors:
            messages.error(self.request, f"{error}: {form.errors[error]}")
        return super().form_invalid(form)

    @staticmethod
    def send_emails(application):
        # Отправка уведомления администратору
        send_mail(
            'Новая заявка на регистрацию',
            f'Имя: {application.username}\n'
                    f'Email: {application.email}\n'
                    f'Комментарий: {application.comment}\n'
                    f'IP: {application.user_ip}',
            settings.EMAIL_HOST_USER,
            ['melnovnikita16@gmail.com'],
            fail_silently=False,
        )
        # Отправка подтверждения клиенту
        send_mail(
            'Ваша заявка принята',
            'Спасибо за вашу заявку! Мы рассмотрим ее в ближайшее время.',
            settings.EMAIL_HOST_USER,
            [application.email],
            fail_silently=False,
        )

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
