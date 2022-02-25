release: python manage.py migrate
web: gunicorn task_manager.wsgi
worker: REMAP_SIGTERM=SIGQUIT celery -A task_manager.celery worker --loglevel=info
beat: REMAP_SIGTERM=SIGQUIT celery -A task_manager.celery beat --loglevel=info
worker_and_beat: REMAP_SIGTERM=SIGQUIT celery -A task_manager.celery worker --loglevel=info -B