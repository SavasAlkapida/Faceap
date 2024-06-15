# face_result/admin.py

from django.contrib import admin
from face_result.models import Product , SocialMediaPost, ScoreViewHistory, Log, DailyProductData, ProductChangeLog

admin.site.register(Product)
admin.site.register(SocialMediaPost)
admin.site.register(ScoreViewHistory)
admin.site.register(ProductChangeLog)
admin.site.register(Log)

@admin.register(DailyProductData)
class DailyProductDataAdmin(admin.ModelAdmin):
    list_display = ('product', 'date', 'score_view')
