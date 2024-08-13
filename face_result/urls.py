from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from .views import create_advertisement, combined_view, advertisement_list, update_advertisements, save_advertisements, upload_file, delete_all_items, show_highest_impressions, list_products, handle_uploaded_file, fetch_xml_data, high_score_products, trigger_record_daily_score_view, trigger_fetch_xml_data, trigger_tasks, display_highest_score_increase, product_get, product_detail, hidden_products, upload_file_den, post_list, exract_number_vieuw, facebook_login, facebook_callback,publish_post,get_page_posts, product_list, display_facebook_posts, pdf_list_view, oauth2callback, create_label, create_filter, correct_pdf_view

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
    path('combined_view/', combined_view, name='combined_view'),
    path('exract_number_vieuw/', exract_number_vieuw, name='exract_number_vieuw'),
    path('facebook-login/', facebook_login, name='facebook_login'),
    path('facebook-callback/', facebook_callback, name='facebook_callback'),
    path('publish-post/', publish_post, name='publish_post'),
    path('get-page-posts/', get_page_posts, name='get_page_posts'),
    path('product_list', product_list, name='product_list'),
    path('display-facebook-posts/', display_facebook_posts, name='display-facebook-posts'),
    path('draw_and_show_polygon/', views.draw_and_show_polygon, name='draw_and_show_polygon'),
    path('pdf-list/', pdf_list_view, name='pdf_list'),
    path('oauth2callback', oauth2callback, name='oauth2callback'),
    path('create_label', create_label, name='create_label'),
    path('oauth2callback', oauth2callback, name='oauth2callback'),
    path('create_filter/', create_filter, name='create_filter'),
    path('upload/', views.upload_photo, name='upload_photo'),
    path('photo_list/', views.photo_list, name='photo_list'),
    path('photo/<int:id>/', views.photo_detail, name='photo_detail'),
    path('analyze_products/', views.analyze_and_save_products, name='analyze_products'),
    path('analyze_existing_photos/', views.analyze_existing_photos, name='analyze_existing_photos'),
    path('correct-pdf/', correct_pdf_view, name='correct_pdf'),
    path('upload_new/', views.handle_photo_upload, name='handle_photo_upload'),
    path('photos/', views.list_all_photos, name='list_all_photos'),
    path('photos/<int:id>/', views.display_photo_with_similar, name='display_photo_with_similar'),
    path('analyze_and_save_products_custom/', views.analyze_and_save_products_custom, name='analyze_and_save_products_custom'),
    path('analyze_existing_photos_custom/', views.analyze_existing_photos_custom, name='analyze_existing_photos_custom'),
    # path('cendex/', views.cendex, name='cendex'),
    # path('get_image_properties/', views.get_image_properties, name='get_image_properties'),
    
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
