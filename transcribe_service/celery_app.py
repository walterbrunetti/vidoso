
from celery import Celery

def init_app():
    celery_app = Celery('app_name',
                        broker='redis://redis_service',
                        backend='redis://redis_service',
                        include=["transcribe_service.consumers",])
    celery_app.conf.task_default_queue = "default"
    celery_app.conf.broker_connection_retry_on_startup = True
    celery_app.conf.task_routes = {'transcribe_service.consumers.*': {'queue': 'pipeline_1'}}
    celery_app.conf.SEARCH_URL = 'http://search_service:5000'
    return celery_app

celery_app = init_app()
