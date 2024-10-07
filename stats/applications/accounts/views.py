import os
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, CreateView
from django.conf import settings
from applications.accounts.forms import ApplicationForm
from applications.accounts.models import Registration

# Получаем email пользователя из переменных окружения
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Класс ProfileView отображает страницу профиля для аутентифицированного пользователя.
    Шаблон страницы указан в поле template_name.
    """
    template_name = 'registration/profile.html'


class RegisterView(CreateView):
    """
    Класс RegisterView отвечает за регистрацию пользователей путем создания новой записи в модели Registration.
    """
    model = Registration  # Модель для регистрации пользователей
    form_class = ApplicationForm  # Форма, используемая для регистрации
    success_url = reverse_lazy('accounts_app:login')  # URL для перенаправления после успешной регистрации

    def form_valid(self, form):
        """
        Выполняется при успешной валидации формы. Сохраняет объект регистрации, добавляет IP пользователя
        и отправляет уведомления по электронной почте.

        :param form: Объект формы, который прошел валидацию.
        :return: Ответ с перенаправлением на указанный success_url.
        """
        print('Форма пришла')
        # Добавляем IP адрес пользователя в объект формы перед его сохранением
        form.instance.user_ip = self.get_client_ip(self.request)
        response = super().form_valid(form)  # Сохраняем объект и получаем ответ
        application = form.instance
        # Отправка уведомлений на почту администратору и клиенту
        self.send_emails(application)
        # Добавление сообщения об успешной регистрации
        messages.success(self.request, 'Заявка успешно отправлена!')
        return response

    def form_invalid(self, form):
        """
        Выполняется в случае, если форма не прошла валидацию. Отображает ошибки пользователю.

        :param form: Объект формы, который не прошел валидацию.
        :return: Ответ с отображением формы с ошибками.
        """
        # Обработка ошибок формы
        for field, errors in form.errors.items():
            messages.error(self.request, f"{field}: {', '.join(errors)}")
        return super().form_invalid(form)

    @staticmethod
    def send_emails(application: Registration) -> None:
        """
        Отправляет два уведомления по электронной почте: одно администратору, другое клиенту.

        :param application: Объект регистрации, содержащий данные заявки.
        """
        # Отправка уведомления администратору
        send_mail(
            'Новая заявка на регистрацию',
            f'Имя: {application.username}\n'
            f'Email: {application.email}\n'
            f'Комментарий: {application.comment}\n'
            f'IP: {application.user_ip}',
            settings.EMAIL_HOST_USER,
            ['admin@example.com'],  # Email администратора
            fail_silently=False,
        )
        # Отправка подтверждения клиенту
        send_mail(
            'Ваша заявка принята',
            'Спасибо за вашу заявку! Мы рассмотрим ее в ближайшее время.',
            settings.EMAIL_HOST_USER,
            [application.email],  # Email клиента
            fail_silently=False,
        )

    @staticmethod
    def get_client_ip(request) -> str:
        """
        Возвращает IP адрес клиента.

        :param request: Объект запроса HTTP.
        :return: Строка с IP адресом клиента.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Если используется прокси-сервер, получаем первый IP из списка
            ip = x_forwarded_for.split(',')[0]
        else:
            # Если прокси не используется, берем IP из заголовка REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR')
        return ip
