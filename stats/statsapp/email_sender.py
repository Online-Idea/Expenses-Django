import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date


# TODO убрать
def send_email_to_client(client_email: str, file_paths: list) -> None:
    """
    Отправляет письмо с файлом
    @param client_email: почты получателей, разделены запятой
    @param file_paths: путь к файлам
    """

    # Инфо письма
    sender = os.environ['EMAIL_LOGIN']
    password = os.environ['EMAIL_PASSWORD']
    recipients = client_email
    date_str = date.today().strftime('%d.%m.%Y')
    file_name_ext = os.path.basename(file_paths[0])
    subject = f'Звонки РОЛЬФ {date_str}'
    body = 'Добрый день,\n\n' \
           'В приложении звонки по вчерашний день.\n\n' \
           'Это письмо отправлено автоматически. Пожалуйста, не отвечайте на него.\n' \
           'Чтобы отписаться от рассылки напишите нам на: info@ra-online.ru'

    # Сообщение
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = client_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Прикрепляю файлы
    for file in file_paths:
        file_name_ext = os.path.basename(file)
        with open(file, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='xlsx')
            attachment.add_header('Content-Disposition', 'attachment', filename=file_name_ext)
            msg.attach(attachment)

    # Отправляю письмо
    with smtplib.SMTP_SSL('smtp.yandex.ru', 465) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, recipients, msg.as_string())


def send_email(subject: str, body: str, recipients: str, attachments: list = None):
    sender = os.environ['EMAIL_LOGIN']
    password = os.environ['EMAIL_PASSWORD']

    # Сообщение
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipients
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Прикрепляю файлы
    if attachments:
        for file in attachments:
            file_name_ext = os.path.basename(file)
            with open(file, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='xlsx')
                attachment.add_header('Content-Disposition', 'attachment', filename=file_name_ext)
                msg.attach(attachment)

    # Отправляю письмо
    with smtplib.SMTP_SSL('smtp.yandex.ru', 465) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, recipients, msg.as_string())
