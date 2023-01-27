import os
import signal
from celery import Celery, Task
from celery.utils.log import get_task_logger


class MyBaseTask(Task):
    def __call__(self, *args, **kwargs):
        signal.signal(signal.SIGTERM,
                      lambda signum, frame: logger.info('SIGTERM received, wait till the task finished'))
        return super().__call__(*args, **kwargs)


logger = get_task_logger('my_logger')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stats.settings')
app = Celery('stats')
app.Task = MyBaseTask
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
