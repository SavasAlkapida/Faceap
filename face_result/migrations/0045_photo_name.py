# Generated by Django 4.2.6 on 2024-08-07 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0044_photo_dominant_colors'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='name',
            field=models.TextField(default=0),
            preserve_default=False,
        ),
    ]
