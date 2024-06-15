from django.core.management.base import BaseCommand
import requests
import xml.etree.ElementTree as ET
from face_result.models import Product
import pandas as pd

class Command(BaseCommand):
    help = 'Imports products from the XML feed into the database'

    def handle(self, *args, **options):
        url = 'https://www.alkapida.com/feeds/products/promotion-products.xml'
        response = requests.get(url)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for product_elem in root.findall('product'):
                self.create_or_update_product(product_elem)
        else:
            self.stdout.write(self.style.ERROR("Failed to retrieve the XML data"))

    def create_or_update_product(self, elem):
        product_id = elem.find('product_id').text
        description_elem = elem.find('description')
        description = description_elem.text.strip() if description_elem is not None and description_elem.text is not None else 'No description available'


        defaults = {
            'product_code': elem.find('product_code').text,
            'barcode': elem.find('barcode').text,
            'name': elem.find('name').text.strip(),
            'brand': elem.find('brand').text,
            'description': description,
            'price': float(elem.find('price').text),
            'currency': elem.find('currency').text,
            'cost_price': float(elem.find('cost_price').text),
            'cost_price_currency': elem.find('cost_price_currency').text,
            'stock': int(elem.find('stock').text),
            'score_sale': self.parse_float(elem.find('score_sale').text),
            'score_price': self.parse_float(elem.find('score_price').text),
            'score_view': self.parse_float(elem.find('score_view').text),
            'score_total': self.parse_float(elem.find('score_total').text),
            'days_online': int(elem.find('days_online').text),
            'sold_6_months': int(elem.find('sold_6_months').text),
            'viewed_90_days': int(elem.find('viewed_90_days').text),
            'category_path': ' > '.join([cp.text for cp in elem.find('category_data/category_path')]),
            'images': ','.join([img.text for img in elem.findall('images')])
        }

        product, created = Product.objects.update_or_create(
            product_id=product_id, defaults=defaults
        )
        action = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(f'Product {action}: {product.name}'))

    def parse_float(self, value):
        try:
            return float(value.replace(',', '.'))
        except (ValueError, AttributeError):
            return 0.0
