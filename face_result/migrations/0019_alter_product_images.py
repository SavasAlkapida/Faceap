# Generated by Django 4.2.6 on 2024-05-28 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0018_alter_socialmediapost_matched_target_audience_consumption_photo_click_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='images',
            field=models.CharField(max_length=1024),
        ),
    ]
