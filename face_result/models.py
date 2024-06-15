from django.db import models
from django.utils import timezone
import xml.etree.ElementTree as ET
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import json
from datetime import timedelta

class Advertisement(models.Model):
    reklam_verme_tarihi = models.DateField(verbose_name='Reklam Verme Tarihi')
    tiklama_sayisi_face = models.PositiveIntegerField(verbose_name='Tıklama Sayısı Face')
    goruntuleme_sayisi_face = models.PositiveIntegerField(verbose_name='Görüntüleme Sayısı Face')
    tiklama_sayisi_instg = models.PositiveIntegerField(verbose_name='Tıklama Sayısı INSTG')
    goruntuleme_sayisi_instgr = models.PositiveIntegerField(verbose_name='Görüntüleme Sayısı INSTGR')
    satis_orani = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Satış Oranı')
    site_raytingi = models.DecimalField(max_digits=3, decimal_places=2, verbose_name='Site Raytingi')
    image = models.ImageField(upload_to='advertisements/', verbose_name="Reklam Resmi", null=True, blank=True)


    def __str__(self):
        return f"Reklam Verme Tarihi: {self.reklam_verme_tarihi}, Tıklama Sayısı Face: {self.tiklama_sayisi_face}"
    
    @property
    def total_views(self):
        return self.goruntuleme_sayisi_face + self.goruntuleme_sayisi_instgr


class SocialMediaPost(models.Model):
    post_code = models.CharField(max_length=255,)
    page_code = models.CharField(max_length=255)
    page_name = models.CharField(max_length=255)
    description = models.TextField()
    duration_seconds = models.IntegerField()
    publish_time = models.DateTimeField(null=True, blank=True)
    subtitle_type = models.CharField(max_length=255)
    permalink = models.URLField()
    cross_share = models.BooleanField()
    share_type = models.CharField(max_length=255)
    post_type = models.CharField(max_length=255)
    languages = models.CharField(max_length=255)
    special_tags = models.CharField(max_length=255)
    sponsored_content_status = models.CharField(max_length=255)
    data_comment = models.TextField()
    date = models.CharField(max_length=255)
    impressions = models.IntegerField()
    reach = models.IntegerField()
    reactions_comments_shares = models.IntegerField()
    reactions = models.IntegerField()
    comments = models.IntegerField()
    shares = models.IntegerField()
    total_clicks = models.IntegerField()
    link_clicks = models.IntegerField()
    other_clicks = models.IntegerField()
    matched_target_audience_consumption_photo_click = models.CharField(max_length=255)
    matched_target_audience_consumption_video_click = models.CharField(max_length=255)
    negative_feedback_from_users_hide_all = models.IntegerField()
    reels_plays_count = models.IntegerField()
    second_views = models.IntegerField()
    average_second_views = models.FloatField()
    estimated_earnings_usd = models.FloatField()
    ad_cpm_usd = models.FloatField()
    ad_impressions = models.IntegerField()
    title = models.CharField(max_length=200)
   

    def __str__(self):
        return self.post_code
    
class Product(models.Model):
    product_id = models.CharField(max_length=255, unique=True)
    product_code = models.CharField(max_length=255, null=True, blank=True)
    barcode = models.CharField(max_length=255, null=True, blank=True)
    name = models.TextField()
    brand = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    price = models.FloatField()
    currency = models.CharField(max_length=10)
    cost_price = models.FloatField()
    cost_price_currency = models.CharField(max_length=10)
    stock = models.IntegerField()
    score_sale = models.FloatField(null=True, blank=True)
    score_price = models.FloatField(null=True, blank=True)
    score_view = models.FloatField(null=True, blank=True)
    score_total = models.FloatField(null=True, blank=True)
    days_online = models.IntegerField()
    sold_6_months = models.IntegerField()
    viewed_90_days = models.IntegerField()
    category_path = models.CharField(max_length=255, null=True, blank=True)
    images = models.CharField(max_length=1024)  # Ürün resmi URL'si
    active = models.IntegerField()
    is_advertised = models.BooleanField(default=False)
    advertised_date = models.DateField(null=True, blank=True)
    

    
    def __str__(self):
        return self.name    
    
    
class AdvertisedHistory (models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='advertised_history')
    advertised_date = models.DateTimeField(auto_now_add=True)
        
    
class ProductChangeLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=255)  # 'created', 'updated', 'deleted'
    timestamp = models.DateTimeField(auto_now_add=True)
    changed_data = models.TextField()  # JSON formatında değişiklik verisi
    
@receiver(post_save, sender=Product)
def log_product_save(sender, instance, created, **kwargs):
    change_type = 'created' if created else 'updated'
    change_data = json.dumps({
        'product_id': instance.product_id,
        'product_code': instance.product_code,
        'barcode': instance.barcode,
        'name': instance.name,
        'brand': instance.brand,
        'description': instance.description,
        'price': instance.price,
        'currency': instance.currency,
        'cost_price': instance.cost_price,
        'cost_price_currency': instance.cost_price_currency,
        'stock': instance.stock,
        'score_sale': instance.score_sale,
        'score_price': instance.score_price,
        'score_view': instance.score_view,
        'score_total': instance.score_total,
        'days_online': instance.days_online,
        'sold_6_months': instance.sold_6_months,
        'viewed_90_days': instance.viewed_90_days,
        'category_path': instance.category_path,
        'images': instance.images,
        'active': instance.active,
    })
    ProductChangeLog.objects.create(
        product=instance,
        change_type=change_type,
        changed_data=change_data
    )

@receiver(post_delete, sender=Product)
def log_product_delete(sender, instance, **kwargs):
    change_data = json.dumps({
        'product_id': instance.product_id,
        'product_code': instance.product_code,
        'barcode': instance.barcode,
        'name': instance.name,
        'brand': instance.brand,
        'description': instance.description,
        'price': instance.price,
        'currency': instance.currency,
        'cost_price': instance.cost_price,
        'cost_price_currency': instance.cost_price_currency,
        'stock': instance.stock,
        'score_sale': instance.score_sale,
        'score_price': instance.score_price,
        'score_view': instance.score_view,
        'score_total': instance.score_total,
        'days_online': instance.days_online,
        'sold_6_months': instance.sold_6_months,
        'viewed_90_days': instance.viewed_90_days,
        'category_path': instance.category_path,
        'images': instance.images,
        'active': instance.active,
    })
    ProductChangeLog.objects.create(
        product=instance,
        change_type='deleted',
        changed_data=change_data
    )        
    
    

    
class Log(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    model_name = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.model_name}.{self.field_name} changed from '{self.old_value}' to '{self.new_value}'"    


    
class ScoreViewHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='view_scores')
    date = models.DateField(default=timezone.now)
    score_view = models.FloatField()

    def __str__(self):
        return f"{self.product.name} - {self.date} - {self.score_view}"     

class DailyProductData(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='daily_data')
    date = models.DateField(auto_now_add=True)
    score_view = models.FloatField()

    def __str__(self):
        return f"Daily data for {self.product.name} on {self.date}"    
    
    

    
    