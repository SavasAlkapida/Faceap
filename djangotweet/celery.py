from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangotweet.settings')

app = Celery('face_result')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Beat schedule ayarlarınız
app.conf.beat_schedule = {
    'fetch_xml_data_every_5_minutes': {
        'task': 'face_result.tasks.fetch_xml_data',
        'schedule': crontab(minute='*/5'),  # Her 5 dakikada bir çalıştır
    },
    'record_daily_score_view_every_5_minutes': {
        'task': 'face_result.tasks.record_daily_score_view',
        'schedule': crontab(minute='*/5'),  # Her 5 dakikada bir çalıştır
    },
}
