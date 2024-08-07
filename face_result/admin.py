# face_result/admin.py

from django.contrib import admin
from face_result.models import Product , SocialMediaPost, ScoreViewHistory, Log, DailyProductData, ProductChangeLog, Post, Postd, FacebookPost, FacebookLike, FacebookComment, Photo



class ProductAdmin(admin.ModelAdmin):
    search_fields = ['product_id', 'product_code', 'name', 'brand']

class PostAdmin(admin.ModelAdmin):
    search_fields = ['post_code', 'page_code', 'page_name', 'description']
    
admin.site.register(Product, ProductAdmin)
admin.site.register(SocialMediaPost)
admin.site.register(ScoreViewHistory)
admin.site.register(ProductChangeLog)
admin.site.register(Log)
admin.site.register(Post, PostAdmin)
admin.site.register(Postd)    
admin.site.register(FacebookPost)
admin.site.register(FacebookLike)
admin.site.register(FacebookComment)
admin.site.register(Photo)

@admin.register(DailyProductData)
class DailyProductDataAdmin(admin.ModelAdmin):
    list_display = ('product', 'date', 'score_view')
    
 
    

