from django.core.management.base import BaseCommand
from face_result.utils import find_product_with_highest_score_increase

class Command(BaseCommand):
    help = 'Find the product with the highest score_total increase'

    def handle(self, *args, **kwargs):
        product, increase = find_product_with_highest_score_increase()
        if product:
            self.stdout.write(self.style.SUCCESS(f'En büyük artış: {increase}, Ürün: {product.name}'))
        else:
            self.stdout.write(self.style.WARNING('Hiç artış bulunamadı'))