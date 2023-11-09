import os
import signal
from celery import Celery, Task
from celery.utils.log import get_task_logger
from celery.signals import task_failure
from django.core.mail import send_mail


# class MyBaseTask(Task):
#     def __call__(self, *args, **kwargs):
#         signal.signal(signal.SIGTERM,
#                       lambda signum, frame: logger.info('SIGTERM received, wait till the task finished'))
#         return super().__call__(*args, **kwargs)


logger = get_task_logger('my_logger')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stats.settings')
app = Celery('stats')
# app.Task = MyBaseTask
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None,
                        args=None, kwargs=None, traceback=None, einfo=None, **kw):
    # Отправляет письмо когда Celery task крашится
    send_mail(
        subject='Celery task failed',
        message=f'Task {sender.name} with id {task_id} failed with exception {exception}',
        from_email=os.environ['EMAIL_LOGIN'],
        recipient_list=['evgen0nlin3@gmail.com'],
        fail_silently=False,
    )
