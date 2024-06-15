from django.shortcuts import render
from face_result.models import ProductChangeLog
import json


def find_product_with_highest_score_increase():
    products = ProductChangeLog.objects.values('product_id').distinct()  # Benzersiz ürünleri alır.
    max_score_increase = 0  # En büyük skor artışını tutar.
    max_impressions_increase = 0  # En büyük izlenim artışını tutar.
    product_with_max_score_increase = None  # En büyük skor artışına sahip ürünü tutar.
    product_with_max_impressions_increase = None  # En büyük izlenim artışına sahip ürünü tutar.

    for product in products:  # Her benzersiz ürün için döngüye girer.
        logs = ProductChangeLog.objects.filter(product_id=product['product_id']).order_by('timestamp')  # Ürünün değişiklik günlüklerini zaman sırasına göre alır.
        prev_score = None  # Önceki skor değeri.
        prev_impressions = None  # Önceki izlenim değeri.

        for log in logs:  # Her bir günlük için döngüye girer.
            changed_data = json.loads(log.changed_data)  # Günlük verilerini JSON olarak yükler.
            score_total = changed_data.get('score_total')  # Skor toplamını alır.
            impressions = changed_data.get('score_view')  # İzlenim değerini alır.

            if score_total is not None:
                if prev_score is not None:
                    score_increase = score_total - prev_score  # Skor artışını hesaplar.
                    if score_increase > max_score_increase:  # Eğer bu artış, önceki maksimum artıştan büyükse:
                        max_score_increase = score_increase  # Maksimum skoru günceller.
                        product_with_max_score_increase = log.product  # Bu ürünü maksimum skor artışına sahip ürün olarak ayarlar.
                prev_score = score_total  # Mevcut skoru önceki skor olarak ayarlar.

            if impressions is not None:
                if prev_impressions is not None:
                    impressions_increase = impressions - prev_impressions  # İzlenim artışını hesaplar.
                    if impressions_increase > max_impressions_increase:  # Eğer bu artış, önceki maksimum artıştan büyükse:
                        max_impressions_increase = impressions_increase  # Maksimum izlenimleri günceller.
                        product_with_max_impressions_increase = log.product  # Bu ürünü maksimum izlenim artışına sahip ürün olarak ayarlar.
                prev_impressions = impressions  # Mevcut izlenimleri önceki izlenimler olarak ayarlar.

    return product_with_max_score_increase, max_score_increase, product_with_max_impressions_increase, max_impressions_increase


