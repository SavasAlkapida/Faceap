from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import AdvertisementForm, SearchForm
from .models import Advertisement , Product, AdvertisedHistory
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from .forms import UploadFileForm
from .models import SocialMediaPost
import openpyxl
import pandas as pd
import os
import datetime
import pytz
from django.contrib import messages
from django.urls import reverse
from .models import Product, ScoreViewHistory
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.timezone import make_aware
from django.utils.timezone import make_aware, is_aware, utc
import requests
import xml.etree.ElementTree as ET
from celery import shared_task
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .tasks import record_daily_score_view, fetch_xml_data
from .utils import find_product_with_highest_score_increase
from face_result.models import ProductChangeLog
from django.db.models import F, ExpressionWrapper, DecimalField, Case, When, Value


def create_advertisement(request):
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)  # Resim dosyalarını kabul etmek için request.FILES ekledik
        if form.is_valid():
            form.save()
            return redirect('advertisement_list')
    else:
        form = AdvertisementForm()
    return render(request, 'face_result/create_advertisement.html', {'form': form})





def update_advertisements(request):
    access_token = settings.FACEBOOK_ACCESS_TOKEN  # access_token settings.py dosyasından alınıyor
    ad_account_id = settings.FACEBOOK_AD_ACCOUNT_ID  # ad_account_id settings.py dosyasından alınıyor

    url = f'https://graph.facebook.com/v12.0/{ad_account_id}/ads'
    params = {
        'fields': 'name,insights{impressions}',
        'access_token': access_token
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'data' in data:
            for ad in data['data']:
                ad_name = ad['name']
                impressions = ad['insights']['data'][0]['impressions'] if 'insights' in ad and 'data' in ad['insights'] else 'No data'
                print(f'Ad Name: {ad_name}, Impressions: {impressions}')
        else:
            print('Error:', data)
    except requests.exceptions.RequestException as e:
        print(f'Error fetching Facebook data: {e}')

    return redirect('advertisement_list')

def save_advertisements(request):
    if request.method == 'POST':
        data = request.POST
        for key, value in data.items():
            if key.startswith('ad_'):
                ad_id, field = key.split('_')[1], key.split('_')[2]
                ad = get_object_or_404(Advertisement, pk=ad_id)
                setattr(ad, field, value)
                ad.save()
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)
    
def update_advertisement(request, pk):
    advertisement = get_object_or_404(Advertisement, pk=pk)
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES, instance=advertisement)
        if form.is_valid():
            form.save()
            return redirect('advertisement_list')
    else:
        form = AdvertisementForm(instance=advertisement)
    return render(request, 'face_result/update_advertisement.html', {'form': form})

    extension = os.path.splitext(f.name)[1]
    if extension not in ['.xlsx', '.xls']:
        return HttpResponseBadRequest("Invalid file format. Please upload an Excel file.")
    
    df = pd.read_excel(f, engine='openpyxl' if extension == '.xlsx' else 'xlrd')
    df.columns = df.columns.str.strip()
    
    required_columns = [
        'Gönderi Kodu', 'Sayfa Kodu', 'Sayfa Adı', 'Unvan', 'Açıklama', 'Süre (sn)',
        'Yayınlanma Zamanı', 'Altyazı Türü', 'Sabit Bağlantı', 'Çapraz Paylaşım', 'Paylaşım',
        'Gönderi Türü', 'Diller', 'Özel Etiketler', 'Finansmanlı içerik durumu', 'Veri yorumu',
        'Tarih', 'Gösterimler', 'Erişim', 'İfadeler, Yorumlar ve Paylaşımlar', 'İfadeler',
        'Yorumlar', 'Paylaşımlar', 'Toplam Tıklamalar', 'Bağlantı Tıklamaları', 'Diğer Tıklamalar',
        'Eşleşen Hedef Kitle Tüketim Hedeflemesi (Photo Click)', 'Eşleşen Hedef Kitle Tüketim Hedeflemesi (Video Click)',
        'Kullanıcılardan olumsuz görüşler: Tümünü Gizle', 'REELS_PLAYS:COUNT', 'Saniye görüntülemeler',
        'Ortalama Saniye görüntülemeler', 'Tahmini Kazançlar (ABD Doları)', "Reklam CPM'si (ABD Doları)",
        'Reklam gösterimleri'
    ]

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return HttpResponseBadRequest(f"Missing required columns: {missing_cols}")

    try:
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
        # Zaman dilimi bilgisi eklenirken NaT kontrolü yapılıyor
        df['Yayınlanma Zamanı'] = pd.to_datetime(df['Yayınlanma Zamanı'], errors='coerce')
        df['Yayınlanma Zamanı'] = df['Yayınlanma Zamanı'].apply(lambda x: x.tz_localize('UTC') if pd.notnull(x) else None)
    except Exception as e:
        return HttpResponseBadRequest(f"Date conversion error: {e}")

    df.fillna({
        'Süre (sn)': 0,
        'Gösterimler': 0,
        'Erişim': 0,
        'İfadeler, Yorumlar ve Paylaşımlar': 0,
        'İfadeler': 0,
        'Yorumlar': 0,
        'Paylaşımlar': 0,
        'Toplam Tıklamalar': 0,
        'Bağlantı Tıklamaları': 0,
        'Diğer Tıklamalar': 0,
        'Eşleşen Hedef Kitle Tüketim Hedeflemesi (Photo Click)': 0,
        'Eşleşen Hedef Kitle Tüketim Hedeflemesi (Video Click)': 0,
        'Kullanıcılardan olumsuz görüşler: Tümünü Gizle': 0,
        'REELS_PLAYS:COUNT': 0,
        'Saniye görüntülemeler': 0,
        'Ortalama Saniye görüntülemeler': 0.0,
        'Tahmini Kazançlar (ABD Doları)': 0.0,
        "Reklam CPM'si (ABD Doları)": 0.0,
        'Reklam gösterimleri': 0,
    }, inplace=True)

    # Veritabanı güncellemesi veya başka işlemler için buradan devam edebilirsiniz
    
    for index, row in df.iterrows():
        post_code = row['Gönderi Kodu']
        
        post, created = SocialMediaPost.objects.update_or_create(
            post_code=post_code,
            defaults={
                
                'post_code': row['Gönderi Kodu'],
                'page_code': row['Sayfa Kodu'],
                'page_name': row['Sayfa Adı'],
                'title': row['Unvan'],
                'description': row['Açıklama'],
                'duration_seconds': row['Süre (sn)'],
                'publish_time': row['Yayınlanma Zamanı'],
                'subtitle_type': row['Altyazı Türü'],
                'permalink': row['Sabit Bağlantı'],
                'cross_share': row['Çapraz Paylaşım'],
                'share_type': row['Paylaşım'],
                'post_type': row['Gönderi Türü'],
                'languages': row['Diller'],
                'special_tags': row['Özel Etiketler'],
                'sponsored_content_status': row['Finansmanlı içerik durumu'],
                'data_comment': row['Veri yorumu'],
                'date': row['Tarih'],
                'impressions': row['Gösterimler'],
                'reach': row['Erişim'],
                'reactions_comments_shares': row['İfadeler, Yorumlar ve Paylaşımlar'],
                'reactions': row['İfadeler'],
                'comments': row['Yorumlar'],
                'shares': row['Paylaşımlar'],
                'total_clicks': row['Toplam Tıklamalar'],
                'link_clicks': row['Bağlantı Tıklamaları'],
                'other_clicks': row['Diğer Tıklamalar'],
                'matched_target_audience_consumption_photo_click': row['Eşleşen Hedef Kitle Tüketim Hedeflemesi (Photo Click)'],
                'matched_target_audience_consumption_video_click': row['Eşleşen Hedef Kitle Tüketim Hedeflemesi (Video Click)'],
                'negative_feedback_from_users_hide_all': row['Kullanıcılardan olumsuz görüşler: Tümünü Gizle'],
                'reels_plays_count': row['REELS_PLAYS:COUNT'],
                'second_views': row['Saniye görüntülemeler'],
                'average_second_views': row['Ortalama Saniye görüntülemeler'],
                'estimated_earnings_usd': row['Tahmini Kazançlar (ABD Doları)'],
                'ad_cpm_usd': row["Reklam CPM'si (ABD Doları)"],
                'ad_impressions': row['Reklam gösterimleri'],
            }
        )
    

    return redirect('advertisement_list')  # İşlem başarılı ise uygun bir view'a yönlendirin





def delete_all_items(request):
    if request.method == 'POST':
        SocialMediaPost.objects.all().delete()
        return redirect('advertisement_list')
    
    else:
        return render(request, 'face_result/advertisement_list.html')
    
def show_highest_impressions(request):
    # En yüksek score_total değerine sahip ilk 50 kaydı al
    highest_impression_ads = Product.objects.order_by('-score_total')[:50]

    # Template'e bu listeyi gönder
    return render(request, 'face_result/first_advertisiment.html', {'advertisements': highest_impression_ads})


def list_products(request):
    products = Product.objects.all()  # Tüm ürünleri veritabanından çek
    for product in products:
        product.image_url = product.images.split (',')[0] if product.images else None
    
    paginator = Paginator(products, 25)  # Her sayfada 25 ürün göster

    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # Eğer sayfa sayısal bir değer değilse, ilk sayfayı göster
        products = paginator.page(1)
    except EmptyPage:
        # Eğer sayfa boşsa (içerik yoksa), son sayfayı göster
        products = paginator.page(paginator.num_pages)    
        
    
    return render(request, 'face_result/list_products.html', {'products': products})




        
def calculate_time_since_published(request):
    advertisement = Advertisement.objects.get(id=1)  # Örnek bir reklam id'si ile reklamı alın
    now = datetime.now(datetime.timezone.utc)  # Şu anki zaman, UTC zaman diliminde
    
    if advertisement.publish_time:
        time_elapsed = now - advertisement.publish_time  # Yayınlanma tarihinden bu yana geçen süre
        context = {
            'advertisement': advertisement,
            'time_elapsed': time_elapsed
        }
    else:
        context = {
            'advertisement': advertisement,
            'error': 'Publish time not available.'
        }

    return render(request, 'face_result/advertisementlist.html', context)        


        
def list_social_media_posts(request):
    posts = SocialMediaPost.objects.all()  # Tüm kayıtları çek
    return render(request, 'face_result/social_media_posts.html', {'posts': posts})       

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            message = handle_uploaded_file(request.FILES['file'])
            # Kullanıcıya işlem hakkında bilgi ver
            messages.success(request, message)
            return HttpResponse(message)
        else:
            return HttpResponseBadRequest("advertisement_list")
    else:
        form = UploadFileForm()
        return render(request, 'face_result/upload.html', {'form': form}) 
    
def advertisement_list(request):
    # Queryset'i belirli bir sırayla al, örneğin yayınlanma zamanına veya ID'ye göre
    item_list = SocialMediaPost.objects.all().order_by('-publish_time')  # Yayınlanma zamanına göre tersten sırala

    paginator = Paginator(item_list, 50)  # Her sayfada 50 kayıt göster

    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    current_time = timezone.now()
    ads_with_duration = []
    for ad in items:
        if ad.publish_time:
            duration = current_time - ad.publish_time
            ad.duration = duration.days  # Sadece gün sayısını al
        else:
            ad.duration = "Yayınlanma zamanı belirtilmemiş"
        ads_with_duration.append(ad)

    return render(request, 'face_result/advertisement_list.html', {'items': ads_with_duration})    


def handle_uploaded_file(file):
    try:
        df = pd.read_excel(file, engine='openpyxl')
        df['negative_feedback_from_users_hide_all'] = df['negative_feedback_from_users_hide_all'].fillna(0)

        # 'Yayınlanma Zamanı' sütunu için tarih dönüşümünü düzeltin
        df['Yayınlanma Zamanı'] = pd.to_datetime(df['Yayınlanma Zamanı'], errors='coerce', utc=True)
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date

        for index, row in df.iterrows():
            if pd.notna(row['Yayınlanma Zamanı']) and not is_aware(row['Yayınlanma Zamanı']):
                publish_time = make_aware(row['Yayınlanma Zamanı'], timezone=utc)
            else:
                publish_time = row['Yayınlanma Zamanı']  # Eğer zaten aware ise veya NaT ise doğrudan kullan

            obj, created = SocialMediaPost.objects.update_or_create(
                post_code=row['Gönderi Kodu'],
                defaults={
                    'publish_time': publish_time,
                    'negative_feedback_from_users_hide_all': row['negative_feedback_from_users_hide_all'],
                    'page_code': row['Sayfa Kodu'],
                    'page_name': row['Sayfa Adı'],
                    'title': row['Unvan'],
                    'description': row['Açıklama'],
                    'duration_seconds': row['Süre (sn)'],
                    'subtitle_type': row['Altyazı Türü'],
                    'permalink': row['Sabit Bağlantı'],
                    'cross_share': row['Çapraz Paylaşım'],
                    'share_type': row['Paylaşım'],
                    'post_type': row['Gönderi Türü'],
                    'languages': row['Diller'],
                    'special_tags': row['Özel Etiketler'],
                    'sponsored_content_status': row['Finansmanlı içerik durumu'],
                    'data_comment': row['Veri yorumu'],
                    'date': row['Tarih'],
                    'impressions': row['Gösterimler'],
                    'reach': row['Erişim'],
                    'reactions_comments_shares': row['İfadeler, Yorumlar ve Paylaşımlar'],
                    'reactions': row['İfadeler'],
                    'comments': row['Yorumlar'],
                    'shares': row['Paylaşımlar'],
                    'total_clicks': row['Toplam Tıklamalar'],
                    'link_clicks': row['Bağlantı Tıklamaları'],
                    'matched_target_audience_consumption_photo_click': row['Eşleşen Hedef Kitle Tüketim Hedeflemesi (Photo Click)'],
                    'other_clicks': row['Diğer Tıklamalar'],
                    'matched_target_audience_consumption_video_click': row['Eşleşen Hedef Kitle Tüketim Hedeflemesi (Video Click)'],
                    'negative_feedback_from_users_hide_all': row['Kullanıcılardan olumsuz görüşler: Tümünü Gizle'],
                    'reels_plays_count': row['REELS_PLAYS:COUNT'],
                    'second_views': row['Saniye görüntülemeler'],
                    'average_second_views': row['Ortalama Saniye görüntülemeler'],
                    'estimated_earnings_usd': row['Tahmini Kazançlar (ABD Doları)'],
                    'ad_cpm_usd': row["Reklam CPM'si (ABD Doları)"],
                    'ad_impressions': row['Reklam gösterimleri'],
                }
            )

        return "File has been uploaded and processed successfully."
    except Exception as e:
        return str(e)  # Hata mesajını doğrudan döndürün


def parse_and_save(xml_data):
    tree = ET.fromstring(xml_data)
    for item in tree.findall('.//product'):  # XML yapınıza göre ayarlayın
        product_id = item.find('product_id').text
        product_code = item.find('product_code').text
        barcode = item.find('barcode').text
        name = item.find('name').text
        brand = item.find('brand').text
        price = float(item.find('price').text)
        currency = item.find('currency').text
        cost_price = float(item.find('cost_price').text)
        cost_price_currency = item.find('cost_price_currency').text
        stock = int(item.find('stock').text)
        score_sale = float(item.find('score_sale').text) if item.find('score_sale') is not None else None
        score_price = float(item.find('score_price').text) if item.find('score_price') is not None else None
        score_view = float(item.find('score_view').text) if item.find('score_view') is not None else None
        score_total = float(item.find('score_total').text) if item.find('score_total') is not None else None
        days_online = int(item.find('days_online').text)
        sold_6_months = int(item.find('sold_6_months').text)
        viewed_90_days = int(item.find('viewed_90_days').text)
        images = item.find('images').text
        active = int(item.find('active').text)

        Product.objects.update_or_create(
            product_id=product_id,
            defaults={
                'product_code': product_code,
                'barcode': barcode,
                'name': name,
                'brand': brand,
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
                'images': images,
                'active': active
            }
        )
        
        
      

def fetch_xml_data(request):
    url = "https://www.alkapida.com/feeds/products/promotion-products.xml"
    response = requests.get(url)
    if response.status_code == 200:
        parse_and_save(response.content)
        return HttpResponse("Data fetched and saved successfully")
    else:
        return HttpResponse(f"Failed to fetch data: {response.status_code}", status=400)
    

def start_fetch_xml_data(request):
    fetch_xml_data.delay()  # Task'ı asenkron olarak başlat
    return JsonResponse({"status": "Task started"})  # JSON yanıt döndür   


def high_score_products(request):
    product_score = Product.objects.filter(sold_6_months__lt=10, active=1).order_by('-score_total')[:25]
    return render(request, 'face_result/high_score_products.html', {'product_score': product_score})



@shared_task
def record_daily_score_view():
    today = timezone.now().date()
    products = Product.objects.filter(active=1)  # Sadece aktif ürünler üzerinde işlem yapılması
    for product in products:
        ScoreViewHistory.objects.create(
            product=product,
            date=today,
            score_view=product.score_view
        )

def trigger_tasks(request):
    return render(request, 'face_result/trigger_tasks.html')        
        
def trigger_record_daily_score_view(request):
    result = record_daily_score_view.delay()  # Görevi asenkron olarak çalıştır
    return JsonResponse({'status': 'success', 'task_id': result.id})

def trigger_fetch_xml_data(request):
    result = fetch_xml_data.delay()  # Görevi asenkron olarak çalıştır
    return JsonResponse({'status': 'success', 'task_id': result.id})


def display_highest_score_increase(request):
    product_score, score_increase, product_impressions, impressions_increase = find_product_with_highest_score_increase()
    context = {
        'product_score': product_score,
        'score_increase': score_increase,
        'product_impressions': product_impressions,
        'impressions_increase': impressions_increase
    }
    return render(request, 'face_result/highest_score_increase.html', context)



def get_products_queryset():
    return Product.objects.annotate(
        total_score=F('score_total') + F('score_view'),
        buy_price=Case(
            When(cost_price_currency="TRY", then=ExpressionWrapper(F("cost_price") / 36, output_field=DecimalField()))
        ),
        extra_price=Case(
            When(cost_price_currency="TRY", then=ExpressionWrapper((F("cost_price") / 36) * 1.45, output_field=DecimalField())),
            default=ExpressionWrapper(F("cost_price") * 1.2, output_field=DecimalField()))
    ).filter(active=1)

def product_get(request):
    # Ortak sorgu fonksiyonunu çağırarak products1 ve products queryset'lerini alır
    products_queryset = get_products_queryset()

    # category_path ve diğer filtreleme parametrelerini al
    category_path = request.GET.get('category_path')
    days_online_lt = request.GET.get('days_online_lt')
    score_total_gt = request.GET.get('score_total_gt')
    sold_6_months_gt = request.GET.get('sold_6_months_gt')
    order_by = request.GET.get('order_by', 'total_score')
    direction = request.GET.get('direction', 'desc')

    # Sıralama yönünü belirle
    if direction == 'desc':
        order_by = '-' + order_by

    # Filtreleme işlemlerini uygula
    if days_online_lt:
        products_queryset = products_queryset.filter(days_online__lt=days_online_lt)
    if score_total_gt:
        products_queryset = products_queryset.filter(total_score__gt=score_total_gt)
    if sold_6_months_gt:
        products_queryset = products_queryset.filter(sold_6_months__gt=sold_6_months_gt)
    if category_path:
        products_queryset = products_queryset.filter(category_path=category_path)

    products = products_queryset.all()
    products1 = products_queryset.filter(is_advertised=False).order_by(order_by)[:300]

    # Benzersiz category_path değerlerini alır
    categories = Product.objects.values_list('category_path', flat=True).distinct()

    # Template'e gönderilecek veriler context sözlüğünde toplanır
    context = {
        'products1': products1,
        'products': products,
        'categories': categories,
        'selected_category_path': category_path,
        'days_online_lt': days_online_lt,
        'score_total_gt': score_total_gt,
        'sold_6_months_gt': sold_6_months_gt,
        'order_by': order_by.lstrip('-'),
        'direction': direction,
    }

    # 'face_result/product.html' template'ini render eder ve context'i template'e geçirir
    return render(request, 'face_result/product.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    products_queryset = get_products_queryset()
    
    buy_score = products_queryset.filter(pk=pk).values_list('buy_price', flat=True).first
    sale_price = products_queryset.filter(pk=pk).values_list('extra_price',flat=True).first
    
    if request.method == 'POST':
        product.is_advertised = 'is_advertised' in request.POST
        if product.is_advertised:
            product.advertised_date = timezone.now()
            AdvertisedHistory.objects.create(product=product)
        else:
            product.advertised_date = None  
        product.save()
    
    advertised_history = product.advertised_history.all()
    
    
    context = {
        'product': product,
        'buy_score': buy_score,
        'sale_price': sale_price,
        'advertised_history' : advertised_history
    }
    
    return render(request, 'face_result/product_detail.html', context)


def hidden_products(request):
    products = Product.objects.annotate(
        total_score=F('score_total') + F('score_view'),
        buy_price=Case(
            When(cost_price_currency="TRY", then=ExpressionWrapper((F("cost_price")/36),output_field=DecimalField()))),
        extra_price=Case(
            When(cost_price_currency="TRY", then=ExpressionWrapper((F("cost_price") / 36) * 1.2, output_field=DecimalField())),
            default=ExpressionWrapper(F("cost_price") * 1.2, output_field=DecimalField())
        )
    ).order_by('category_path', '-total_score').filter(
        is_advertised=True ,
    )[:200]
    
    return render(request, "face_result/hidden_products.html", {"products": products})