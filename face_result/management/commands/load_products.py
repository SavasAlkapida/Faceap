import os
from django.core.management.base import BaseCommand
from face_result.models import Product

class Command(BaseCommand):
    help = 'Load products from XML file'

    def handle(self, *args, **kwargs):
        xml_path = 'https://www.alkapida.com/feeds/products/promotion-products.xml'
        # Burada XML dosya yolunu belirtin

        # Ürünleri veri tabanına yükle
        products = Product.objects.all()
        for product in products:
            product.load_from_xml(xml_path)
            self.stdout.write(self.style.SUCCESS(f'Successfully updated product {product.product_id}'))

