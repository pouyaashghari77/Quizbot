from __future__ import absolute_import, unicode_literals

from billiard.exceptions import SoftTimeLimitExceeded

from quizbot import celery_app
from quizbot.apps.data.models import Quiz


@celery_app.task(name='publish-scheduled-quizzes', routing_key='default')
def publish_scheduled_quizzes():
    scheduled_quizzes = Quiz.filter(scheduled=True, is_played=False)
    try:
        from quizbot.apps.data.views import bot, channel, quiz_preview, QUIZ_TYPE_PHOTO, QUIZ_TYPE_TEXT

        for quiz in scheduled_quizzes:
            quiz_type, question, markup = quiz_preview(quiz)
            bot.send_message(channel, text=question, parse_mode="html", reply_markup=markup)
            quiz.is_played = True
            quiz.save()
    except SoftTimeLimitExceeded:
        pass
