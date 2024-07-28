from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangotweet.settings')

app = Celery('djangotweet')

# Celery ayarlarını Django'nun ayarlarından yükle
app.config_from_object('django.conf:settings', namespace='CELERY')

# Otomatik olarak Django uygulamalarındaki task'leri yükle
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
