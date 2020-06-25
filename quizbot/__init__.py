from __future__ import absolute_import

from .celery import app as celery_app

DEFAULT_SETTINGS_MODULE = 'quizbot.settings'

__all__ = ['celery_app']
