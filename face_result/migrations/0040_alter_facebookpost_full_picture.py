# Generated by Django 4.2.6 on 2024-08-04 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0039_alter_socialmediapost_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facebookpost',
            name='full_picture',
            field=models.URLField(blank=True, max_length=400, null=True),
        ),
    ]
