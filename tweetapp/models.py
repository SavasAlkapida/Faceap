from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal, getcontext
from datetime import timedelta
# Create your models here.

class Tweet(models.Model):
    username = models.ForeignKey(User,on_delete=models.CASCADE, null=True)
    message = models.CharField(max_length=100)

    def __str__(self):
        return f"Tweet nick: {self.username} message: {self.message}"
    
class Reklam(models.Model):
    isim = models.CharField(max_length=100, verbose_name="Reklam İsmi")
    reklam_id = models.AutoField(primary_key=True, verbose_name="Reklam ID")
    yayinlanma_tarihi = models.DateField(verbose_name="Reklam Yayınlanma Tarihi")
    bitis_tarihi = models.DateField(verbose_name="Reklam Bitiş Tarihi")
    rating = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Etkileşim")
    goruntuleme_sayisi = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Görüntüleme Sayısı")
    tiklama_sayisi = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Tıklama Sayısı")

    def toplam_skor1(self):
        return float(self.rating) + float(self.goruntuleme_sayisi)

    def __str__(self):
        return self.isim    
    
    def get_sure(self):
        return (self.bitis_tarihi - self.yayinlanma_tarihi).days if self.bitis_tarihi and self.yayinlanma_tarihi else 0
    
    def toplam_skor(self):
        sure = self.get_sure()
        if sure > 0:  # Süre 0'dan büyük olmalıdır, aksi takdirde bölme işlemi hata verir
            normalized_goruntuleme = Decimal(self.goruntuleme_sayisi) / Decimal(sure)
        else:
            normalized_goruntuleme = 0
        toplam = Decimal(self.rating) + normalized_goruntuleme
        return toplam.quantize(Decimal('0.00'))  # Sonucu iki ondalık basamakla sınırla
    
    