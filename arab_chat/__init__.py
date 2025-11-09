# استيراد pymysql فقط إذا كان متوفراً (للاستخدام مع MySQL)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    # pymysql غير متوفر - المشروع يستخدم SQLite
    pass

from .celery import app as celery_app

__all__ = ('celery_app',)
