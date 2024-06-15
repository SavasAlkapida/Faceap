import xml.etree.ElementTree as ET
from .models import Product

def parse_and_save(xml_data):
    tree = ET.fromstring(xml_data)
    for item in tree.findall('./product'):
        product_id = item.find('product_id').text
        product_code = item.find('product_code').text if item.find('product_code') is not None else None
        barcode = item.find('barcode').text if item.find('barcode') is not None else None
        name = item.find('name').text
        brand = item.find('brand').text if item.find('brand') is not None else None
        description = item.find('description').text if item.find('description') is not None else None
        price = float(item.find('price').text) if item.find('price') is not None else None
        currency = item.find('currency').text if item.find('currency') is not None else None
        cost_price = float(item.find('cost_price').text) if item.find('cost_price') is not None else None
        cost_price_currency = item.find('cost_price_currency').text if item.find('cost_price_currency') is not None else None
        stock = int(item.find('stock').text) if item.find('stock') is not None else None
        score_sale = float(item.find('score_sale').text) if item.find('score_sale') is not None else None
        score_price = float(item.find('score_price').text) if item.find('score_price') is not None else None
        score_view = float(item.find('score_view').text) if item.find('score_view') is not None else None
        score_total = float(item.find('score_total').text) if item.find('score_total') is not None else None
        days_online = int(item.find('days_online').text) if item.find('days_online') is not None else None
        sold_6_months = int(item.find('sold_6_months').text) if item.find('sold_6_months') is not None else None
        viewed_90_days = int(item.find('viewed_90_days').text) if item.find('viewed_90_days') is not None else None
        category_path = item.find('category_path').text if item.find('category_path') is not None else None
        images = item.find('images').text if item.find('images') is not None else None
        active = int(item.find('active').text) if item.find('active') is not None else None

        Product.objects.update_or_create(
            product_id=product_id,
            defaults={
                'product_code': product_code,
                'barcode': barcode,
                'name': name,
                'brand': brand,
                'description': description,
                'price': price,
                'currency': currency,
                'cost_price': cost_price,
                'cost_price_currency': cost_price_currency,
                'stock': stock,
                'score_sale': score_sale,
                'score_price': score_price,
                'score_view': score_view,
                'score_total': score_total,
                'days_online': days_online,
                'sold_6_months': sold_6_months,
                'viewed_90_days': viewed_90_days,
                'category_path': category_path,
                'images': images,
                'active': active
            }
        )
