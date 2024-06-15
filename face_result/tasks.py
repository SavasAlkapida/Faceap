from celery import shared_task
from .models import Product, DailyProductData
import requests
import xml.etree.ElementTree as ET

@shared_task
def record_daily_score_view():
    try:
        products = Product.objects.all()
        for product in products:
            DailyProductData.objects.create(
                product=product,
                score_view=product.score_view
            )
            print(f"Recorded daily score_view for product {product.product_id}")
    except Exception as e:
        print(f"Error recording daily score_view: {e}")
        raise e

@shared_task
def fetch_xml_data():
    try:
        # XML dosyasını indirin
        xml_url = 'https://www.alkapida.com/feeds/products/promotion-products.xml'
        response = requests.get(xml_url)
        response.raise_for_status()  # HTTP hatalarını kontrol edin

        # XML verilerini ayrıştırın
        root = ET.fromstring(response.content)

        # XML verilerini işleme örneği
        for product_element in root.findall('product'):
            product_id = product_element.find('product_id').text
            product_name = product_element.find('name').text
            product_score = product_element.find('score_view').text  # Düzgün etiketi kontrol edin

            # Veritabanında ürünü bul veya oluştur
            product, created = Product.objects.get_or_create(product_id=product_id)
            product.name = product_name
            product.score_view = product_score
            # Diğer alanları güncelle...
            product.save()

        print("XML data fetched and processed.")
    except Exception as e:
        print(f"Error fetching and processing XML data: {e}")
        raise e
