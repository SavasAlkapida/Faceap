from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from .views import create_advertisement, advertisement_list, update_advertisements, advertisement_list, save_advertisements, advertisement_list, upload_file, delete_all_items, show_highest_impressions, list_products, handle_uploaded_file, fetch_xml_data, high_score_products, trigger_record_daily_score_view, trigger_fetch_xml_data, trigger_tasks, display_highest_score_increase, product_get, product_get, product_detail,hidden_products, upload_file_den, post_list


urlpatterns = [
    path('create/', create_advertisement, name='create_advertisement'),
    path('advertisement_list/', advertisement_list, name='advertisement_list'),
    path('update/', update_advertisements, name='update_advertisements'),
    path('save/', save_advertisements, name='save_advertisements'),
    path('upload_file', upload_file, name='upload_file'),
    path('delete-all-data/', delete_all_items, name='delete_all_items'),
    path('show_highest_impressions/', show_highest_impressions, name='show_highest_impressions'),
    path('list_products/', list_products, name='list_products'),
    path('handle_uploaded_file/', handle_uploaded_file, name='handle_uploaded_file'),
    path('fetch_xml_data/', fetch_xml_data, name='fetch_xml_data'),
    path('upload_file_den/', upload_file_den, name='upload_file_den'),
    path('high_score_products/', high_score_products, name='high_score_products'),
    path('trigger-record-daily-score-view/', trigger_record_daily_score_view, name='trigger_record_daily_score_view'),
    path('trigger-fetch-xml-data/', trigger_fetch_xml_data, name='trigger_fetch_xml_data'),
    path('trigger-tasks/', trigger_tasks, name='trigger_tasks'),
    path('display_highest_score_increase/', display_highest_score_increase, name='display_highest_score_increase'),
    path('product_get/', product_get, name='product_get'),
    path('product/', product_get, name='product_list'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('hidden_products/', hidden_products, name='hidden_products'),
    path('post_list/', post_list, name='post_list'),
    
]
    

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
