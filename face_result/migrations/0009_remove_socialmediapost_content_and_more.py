# Generated by Django 4.2.6 on 2024-05-21 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0008_alter_socialmediapost_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialmediapost',
            name='content',
        ),
        migrations.AlterField(
            model_name='socialmediapost',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]
