from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import format_polygon, analyze_layout, analyze_invoice, analyze_elio_sentences, upload_invoice, invoice_list, success_view, analyze_layout_view, analyze_invoice_view

urlpatterns = [
    path('format_polygon/', format_polygon, name='format_polygon'),
    path('analyze-layout/', analyze_layout, name='analyze_layout'),
    path('analyze/', analyze_invoice_view, name='analyze_invoice_view'),
    path('analyze-invoice/', analyze_invoice, name='analyze_invoice'),
    path('analyze-elio-sentences/', analyze_elio_sentences, name='analyze_elio_sentences'),
    path('upload/', upload_invoice, name='upload_invoice'),
    path('invoices/', invoice_list, name='invoice_list'),
    path('success/', success_view, name='success_view'),
    path('analyze-layout-view/', analyze_layout_view, name='analyze_layout_view'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

