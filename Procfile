web: daphne -b 0.0.0.0 -p $PORT arab_chat.asgi:application
worker: celery -A arab_chat worker --loglevel=info --pool=solo

