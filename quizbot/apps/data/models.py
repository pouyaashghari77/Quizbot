from django.db import models
from django.db.models import DateTimeField, IntegerField, CharField, BooleanField, SET_NULL, ForeignKey
from django.utils import timezone


def get_now():
    return timezone.now()


class AbstractLayer(models.Model):
    created_time = DateTimeField()
    last_updated_time = DateTimeField()

    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return cls.objects.get(*args, **kwargs)
        except:
            return None

    @classmethod
    def filter(cls, *args, **kwargs):
        return cls.objects.filter(*args, **kwargs)

    class Meta:
        abstract = True


class User(AbstractLayer):
    tg_id = IntegerField(unique=True)
    step = IntegerField(default=0)
    temp_data = CharField(max_length=4095, null=True)

    @classmethod
    def create(cls, tg_id):
        now = get_now()
        obj = cls(
            tg_id=tg_id,
            created_time=now,
            last_updated_time=now
        )
        obj.save()
        return obj

    def save(self, *args, **kwargs):
        self.last_updated_time = get_now()
        super(User, self).save(*args, **kwargs)


class Quiz(AbstractLayer):
    photo = CharField(max_length=255, null=True, default=None)
    question = CharField(max_length=4095)
    description = CharField(max_length=1023, null=True)
    description2 = CharField(max_length=1023, null=True)
    description3 = CharField(max_length=1023, null=True)
    description4 = CharField(max_length=1023, null=True)
    option1 = CharField(max_length=1023, null=True)
    option2 = CharField(max_length=1023, null=True)
    option3 = CharField(max_length=1023, null=True)
    option4 = CharField(max_length=1023, null=True)
    ready = BooleanField(default=False)
    is_played = BooleanField(default=False)
    scheduled = BooleanField(default=False)

    @classmethod
    def create(cls, question, photo=None, option1=None, option2=None, option3=None, option4=None):
        now = get_now()
        obj = cls(
            photo=photo,
            question=question,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            created_time=now,
            last_updated_time=now
        )
        obj.save()
        return obj

    def save(self, *args, **kwargs):
        self.last_updated_time = get_now()
        super(Quiz, self).save(*args, **kwargs)


class QuizAttempt(AbstractLayer):
    quiz = ForeignKey(Quiz, null=True, on_delete=SET_NULL)
    user = ForeignKey(User, null=True, on_delete=SET_NULL)
    option = IntegerField()

    @classmethod
    def create(cls, quiz, user, option):
        now = get_now()
        obj = cls(
            quiz=quiz,
            user=user,
            option=option,
            created_time=now,
            last_updated_time=now
        )
        obj.save()
        return obj

    def save(self, *args, **kwargs):
        self.last_updated_time = get_now()
        super(QuizAttempt, self).save(*args, **kwargs)



