# Generated by Django 4.2.6 on 2024-05-30 12:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0022_log'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyProductData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('score_view', models.FloatField()),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_data', to='face_result.product')),
            ],
        ),
    ]
