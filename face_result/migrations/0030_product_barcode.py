# Generated by Django 4.2.6 on 2024-07-22 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0029_facebookpost_remove_product_barcode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='barcode',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
