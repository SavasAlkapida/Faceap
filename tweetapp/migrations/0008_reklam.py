# Generated by Django 4.2.6 on 2024-05-07 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tweetapp', '0007_delete_etkinlik'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reklam',
            fields=[
                ('isim', models.CharField(max_length=100, verbose_name='Reklam İsmi')),
                ('reklam_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Reklam ID')),
                ('yayinlanma_tarihi', models.DateField(verbose_name='Reklam Yayınlanma Tarihi')),
                ('bitis_tarihi', models.DateField(verbose_name='Reklam Bitiş Tarihi')),
                ('rating', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Reklamın Aldığı Rating')),
                ('goruntuleme_sayisi', models.PositiveIntegerField(verbose_name='Görüntüleme Sayısı')),
                ('tiklama_sayisi', models.PositiveIntegerField(verbose_name='Tıklama Sayısı')),
            ],
        ),
    ]