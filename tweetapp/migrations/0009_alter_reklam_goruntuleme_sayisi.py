# Generated by Django 4.2.6 on 2024-05-09 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tweetapp', '0008_reklam'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reklam',
            name='goruntuleme_sayisi',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Görüntüleme Sayısı'),
        ),
    ]
