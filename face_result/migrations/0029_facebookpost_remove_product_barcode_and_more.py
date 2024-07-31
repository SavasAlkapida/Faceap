# Generated by Django 4.2.6 on 2024-07-21 21:56

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('face_result', '0028_postd_remove_post_title_post_ad_cpm_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FacebookPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_id', models.CharField(max_length=255, unique=True)),
                ('message', models.TextField(blank=True, null=True)),
                ('created_time', models.DateTimeField()),
                ('full_picture', models.URLField(blank=True, null=True)),
                ('impressions', models.IntegerField(default=0)),
                ('clicks', models.IntegerField(default=0)),
                ('shares', models.IntegerField(default=0)),
                ('likes', models.IntegerField(default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name='product',
            name='barcode',
        ),
        migrations.AlterField(
            model_name='post',
            name='ad_cpm',
            field=models.FloatField(default=0.0, verbose_name="Reklam CPM'si (ABD Doları)"),
        ),
        migrations.AlterField(
            model_name='post',
            name='ad_impressions',
            field=models.IntegerField(default=0, verbose_name='Reklam gösterimleri'),
        ),
        migrations.AlterField(
            model_name='post',
            name='average_second_views',
            field=models.FloatField(default=0.0, verbose_name='Ortalama Saniye görüntülemeler'),
        ),
        migrations.AlterField(
            model_name='post',
            name='comments',
            field=models.IntegerField(default=0, verbose_name='Yorumlar'),
        ),
        migrations.AlterField(
            model_name='post',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Tarih'),
        ),
        migrations.AlterField(
            model_name='post',
            name='estimated_earnings',
            field=models.FloatField(default=0.0, verbose_name='Tahmini Kazançlar (ABD Doları)'),
        ),
        migrations.AlterField(
            model_name='post',
            name='link_clicks',
            field=models.IntegerField(default=0, verbose_name='Bağlantı Tıklamaları'),
        ),
        migrations.AlterField(
            model_name='post',
            name='negative_feedback_hide_all',
            field=models.IntegerField(default=0, verbose_name='Kullanıcılardan olumsuz görüşler: Tümünü Gizle'),
        ),
        migrations.AlterField(
            model_name='post',
            name='other_clicks',
            field=models.IntegerField(default=0, verbose_name='Diğer Tıklamalar'),
        ),
        migrations.AlterField(
            model_name='post',
            name='publication_time',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Yayınlanma Zamanı'),
        ),
        migrations.AlterField(
            model_name='post',
            name='reels_plays_count',
            field=models.IntegerField(default=0, verbose_name='REELS_PLAYS:COUNT'),
        ),
        migrations.AlterField(
            model_name='post',
            name='second_views',
            field=models.IntegerField(default=0, verbose_name='Saniye görüntülemeler'),
        ),
        migrations.AlterField(
            model_name='post',
            name='shares',
            field=models.IntegerField(default=0, verbose_name='Paylaşımlar'),
        ),
        migrations.AlterField(
            model_name='post',
            name='target_audience_photo_click',
            field=models.IntegerField(default=0, verbose_name='Eşleşen Hedef Kitle Tüketim Hedeflemesi (Photo Click)'),
        ),
        migrations.AlterField(
            model_name='post',
            name='target_audience_video_click',
            field=models.IntegerField(default=0, verbose_name='Eşleşen Hedef Kitle Tüketim Hedeflemesi (Video Click)'),
        ),
        migrations.AlterField(
            model_name='post',
            name='total_clicks',
            field=models.IntegerField(default=0, verbose_name='Toplam Tıklamalar'),
        ),
        migrations.CreateModel(
            name='FacebookLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=255)),
                ('user_name', models.CharField(max_length=255)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_likes', to='face_result.facebookpost')),
            ],
        ),
        migrations.CreateModel(
            name='FacebookComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment_id', models.CharField(max_length=255, unique=True)),
                ('user_id', models.CharField(max_length=255)),
                ('user_name', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('created_time', models.DateTimeField()),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_comments', to='face_result.facebookpost')),
            ],
        ),
    ]