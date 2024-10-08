# Generated by Django 4.2.6 on 2024-06-14 18:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0025_product_advertised_date_product_is_advertised'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvertisedHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('advertised_date', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='advertised_history', to='face_result.product')),
            ],
        ),
    ]
