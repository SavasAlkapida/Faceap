# Generated by Django 4.2.6 on 2024-07-26 21:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0037_product_score_total_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='facebookpost',
            name='calculation_result',
            field=models.IntegerField(default=0),
        ),
    ]