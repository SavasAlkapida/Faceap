# Generated by Django 4.2.6 on 2024-07-22 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0030_product_barcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='facebookcomment',
            name='extracted_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]