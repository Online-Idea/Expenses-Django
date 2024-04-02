from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Отправляет тестовое письмо на указанный email.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email адрес получателя')

    def handle(self, *args, **options):
        recipient_email = options['email']
        send_mail(
            'Тестовое сообщение',
            'Это тестовое сообщение, отправленное из Django.',
            settings.EMAIL_HOST_USER,
            [recipient_email],
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS(f'Тестовое письмо успешно отправлено на {recipient_email}'))
