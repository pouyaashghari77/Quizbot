# Generated by Django 3.0.5 on 2020-04-30 21:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='QuizAttempts',
            new_name='QuizAttempt',
        ),
    ]
