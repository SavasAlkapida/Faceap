from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import AdvertisementForm, SearchForm, UploadFileForm, UploadFileForm2
from .models import Advertisement, Product, AdvertisedHistory, SocialMediaPost, ScoreViewHistory, Post, Postd, FacebookPost, FacebookComment, FacebookLike, Photo
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import openpyxl
import pandas as pd
import os, re
import datetime
from datetime import datetime
import pytz
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware, is_aware
import xml.etree.ElementTree as ET
from celery import shared_task
from .tasks import record_daily_score_view, fetch_xml_data
from .utils import find_product_with_highest_score_increase
from face_result.models import ProductChangeLog
from django.db.models import F, ExpressionWrapper, DecimalField, Case, When, Value
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow 
from googleapiclient.errors import HttpError
from google.cloud import vision
from google.cloud.vision_v1 import types

# datetime.timezone.utc yerine geçmek için
from datetime import timezone as dt_timezone


def create_advertisement(request):
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('advertisement_list')
    else:
        form = AdvertisementForm()
    return render(request, 'face_result/create_advertisement.html', {'form': form})


def update_advertisements(request):
    access_token = settings.FACEBOOK_ACCESS_TOKEN
    ad_account_id = settings.FACEBOOK_AD_ACCOUNT_ID

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


def delete_all_items(request):
    if request.method == 'POST':
        SocialMediaPost.objects.all().delete()
        return redirect('advertisement_list')
    else:
        return render(request, 'face_result/advertisement_list.html')


def show_highest_impressions(request):
    highest_impression_ads = Product.objects.order_by('-score_total')[:50]
    return render(request, 'face_result/first_advertisiment.html', {'advertisements': highest_impression_ads})


def list_products(request):
    products = Product.objects.all()
    for product in products:
        product.image_url = product.images.split(',')[0] if product.images else None

    paginator = Paginator(products, 25)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'face_result/list_products.html', {'products': products})


def calculate_time_since_published(request):
    advertisement = Advertisement.objects.get(id=1)
    now = datetime.datetime.now(dt_timezone.utc)

    if advertisement.publish_time:
        time_elapsed = now - advertisement.publish_time
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
    posts = SocialMediaPost.objects.all()
    return render(request, 'face_result/social_media_posts.html', {'posts': posts})



def advertisement_list(request):
    item_list = SocialMediaPost.objects.all().order_by('-publish_time')
    paginator = Paginator(item_list, 50)
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
            ad.duration = duration.days
        else:
            ad.duration = "Yayınlanma zamanı belirtilmemiş"
        ads_with_duration.append(ad)

    return render(request, 'face_result/advertisement_list.html', {'items': ads_with_duration})


def handle_uploaded_file(file):
    try:
        df = pd.read_excel(file, engine='openpyxl')

        # NaN değerlerini sıfır ile doldur
        df['negative_feedback_from_users_hide_all'] = df['negative_feedback_from_users_hide_all'].fillna(0)

        # Tarih ve zaman alanlarını dönüştür
        df['Yayınlanma Zamanı'] = pd.to_datetime(df['Yayınlanma Zamanı'], errors='coerce', utc=True)
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date

        # Düzenli ifade deseni
        pattern = r'"(\d+)"'

        for index, row in df.iterrows():
            if pd.notna(row['Yayınlanma Zamanı']) and not is_aware(row['Yayınlanma Zamanı']):
                publish_time = make_aware(row['Yayınlanma Zamanı'], timezone=dt_timezone.utc)
            else:
                publish_time = row['Yayınlanma Zamanı']

            # Tırnak içindeki sayıyı ayıklama
            description = row['Açıklama']
            if not isinstance(description, str):
                description = str(description)  # 'description' alanını dizeye dönüştürün
            match = re.search(pattern, description)
            post_code = match.group(1) if match else None

            if post_code is None:
                # Eğer tırnak içinde sayı bulunamazsa bu satırı atla
                continue

            obj, created = SocialMediaPost.objects.update_or_create(
                post_code=post_code,
                defaults={
                    'publish_time': publish_time,
                    'negative_feedback_from_users_hide_all': row['negative_feedback_from_users_hide_all'],
                    'page_code': row['Sayfa Kodu'],
                    'page_name': row['Sayfa Adı'],
                    'title': row['Unvan'],
                    'description': description,
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
                    'other_clicks': row['Diğer Tıklamalar'],
                    'matched_target_audience_consumption_photo_click': row['Eşleşen Hedef Kitle Tüketim Hedeflemesi (Photo Click)'],
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
        return str(e)


def parse_and_save(xml_data):
    tree = ET.fromstring(xml_data)
    for item in tree.findall('.//product'):
        product_id = item.find('product_id').text
        product_code = item.find('product_code').text
        barcode = item.find('barcode').text
        name = item.find('name').text
        brand = item.find('brand').text
        
        # Virgül içeren stringleri nokta ile değiştirerek float'a çevir
        price = float(item.find('price').text.replace(',', '.'))
        cost_price = float(item.find('cost_price').text.replace(',', '.'))
        
        currency = item.find('currency').text
        cost_price_currency = item.find('cost_price_currency').text
        stock = int(item.find('stock').text)
        
        score_sale = item.find('score_sale').text
        score_sale = float(score_sale.replace(',', '.')) if score_sale else None
        
        score_price = item.find('score_price').text
        score_price = float(score_price.replace(',', '.')) if score_price else None
        
        score_view = item.find('score_view').text
        score_view = float(score_view.replace(',', '.')) if score_view else None
        
        score_total = item.find('score_total').text
        score_total = float(score_total.replace(',', '.')) if score_total else None
        
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

    # XML güncellemesinden sonra tüm ürünlerin score_view_updated alanını False olarak ayarla
    Product.objects.update(score_view_updated=False)

    for product in Product.objects.filter(score_view_updated=False, score_total_updated=False):
        product.score_total += 0.20
        product.score_view_updated = True
        product.save()  


def fetch_xml_data(request):
    url = "https://www.alkapida.com/feeds/products/promotion-products.xml"
    response = requests.get(url)
    if response.status_code == 200:
        parse_and_save(response.content)
        message = "Alkapida XML i başarıyla güncellendi"
    else:
        message = f"Malisef Alkapida XML güncellenmesinde bir hata yaşandı: {response.status_code}"
    
    # HTML ve JavaScript ile mesajı gösterip yönlendirme
    html = f"""
    <html>
    <head>
        <script type="text/javascript">
            setTimeout(function() {{
                window.location.href = "/face_result/product/";
            }}, 5000);
        </script>
    </head>
    <body>
        <p>{message}</p>
        <p>5 saniye içerisinde product sayfasına yönlendirileceksiniz</p>
    </body>
    </html>
    """
    
    return HttpResponse(html)


def start_fetch_xml_data(request):
    fetch_xml_data.delay()
    return JsonResponse({"status": "Task started"})


def high_score_products(request):
    product_score = Product.objects.filter(sold_6_months__lt=10, active=1).order_by('-score_total')[:25]
    return render(request, 'face_result/high_score_products.html', {'product_score': product_score})


@shared_task
def record_daily_score_view():
    today = timezone.now().date()
    products = Product.objects.filter(active=1)
    for product in products:
        ScoreViewHistory.objects.create(
            product=product,
            date=today,
            score_view=product.score_view
        )


def trigger_tasks(request):
    return render(request, 'face_result/trigger_tasks.html')


def trigger_record_daily_score_view(request):
    result = record_daily_score_view.delay()
    return JsonResponse({'status': 'success', 'task_id': result.id})


def trigger_fetch_xml_data(request):
    result = fetch_xml_data.delay()
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
    products_queryset = get_products_queryset()
    category_path = request.GET.get('category_path')
    days_online_lt = request.GET.get('days_online_lt')
    score_total_gt = request.GET.get('score_total_gt')
    sold_6_months_gt = request.GET.get('sold_6_months_gt')
    order_by = request.GET.get('order_by', 'total_score')
    direction = request.GET.get('direction', 'desc')

    if direction == 'desc':
        order_by = '-' + order_by

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
    categories = Product.objects.values_list('category_path', flat=True).distinct()

    products_with_impressions = []
    for product in products1:
        product_impressions = product.get_impressions()
        product_extracted_number = product.get_extracted_number()
        product_extracted_number2 =product.get_extracted_number2
        
        
        products_with_impressions.append({
            'product': product,
            'impressions': product_impressions,
            'product_extracted_number': product_extracted_number,
        })

    context = {
        'products1': products_with_impressions,
        'products': products,
        'categories': categories,
        'selected_category_path': category_path,
        'days_online_lt': days_online_lt,
        'score_total_gt': score_total_gt,
        'sold_6_months_gt': sold_6_months_gt,
        'order_by': order_by.lstrip('-'),
        'direction': direction,
    }

    return render(request, 'face_result/product.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    posts = FacebookPost.objects.filter(extracted_number=product.product_id)
    
    posts_calculation_results = []

    for post in posts:
        if post.impressions is not None and post.page_total_actions is not None:
            result = (float(post.impressions) / 300000) * post.page_total_actions
            formatted_result = "{:.4f}".format(result)  # Sonucu 4 basamaklı formatla
            mother_total = float(product.score_total) + float(formatted_result)
            posts_calculation_results.append({
                'post_id': post.post_id,
                'result': formatted_result,
                'impressions': post.impressions,
                'page_total_actions': post.page_total_actions,
                'product_id' : product.product_id,
                'mother_total': mother_total
            })
            
    products_queryset = get_products_queryset()

    buy_score = products_queryset.filter(pk=pk).values_list('buy_price', flat=True).first
    sale_price = products_queryset.filter(pk=pk).values_list('extra_price', flat=True).first
    

    if request.method == 'POST':
        product.is_advertised = 'is_advertised' in request.POST
        if product.is_advertised:
            product.advertised_date = timezone.now()
            AdvertisedHistory.objects.create(product=product)
        else:
            product.advertised_date = None
        product.save()

    advertised_history = product.advertised_history.all()
    impressions_face_excel = product.get_impressions()
    impressions_face = product.get_impressions_face
    masage_face_api = product.get_message
    banner_face_api = product.get_full_picture
    clik_face_api = product.get_clicks
    created_time_face_api = product.get_created_time
    
    if impressions_face_excel is not None:
        impressions_divided = impressions_face_excel / 100000
    else:
        impressions_divided = 0 
    publication_time = product.get_publication_time()
    perma_link = product.get_permalink()
     

    context = {
        'product': product,
        'buy_score': buy_score,
        'sale_price': sale_price,
        'advertised_history': advertised_history,
        'impressions_face_excel': impressions_face_excel,
        'publication_time': publication_time,
        'impressions_divided': impressions_divided,
        'perma_link': perma_link,
        'impressions_face' : impressions_face,
        'masage_face_api' : masage_face_api,
        'banner_face_api' : banner_face_api,
        'clik_face_api' : clik_face_api,
        'created_time_face_api' : created_time_face_api,
        'result':posts_calculation_results
        }

    return render(request, 'face_result/product_detail.html', context)


def hidden_products(request):
    products = Product.objects.annotate(
        total_score=F('score_total') + F('score_view'),
        buy_price=Case(
            When(cost_price_currency="TRY", then=ExpressionWrapper(F("cost_price") / 36, output_field=DecimalField())),
            default=F("cost_price"),
            output_field=DecimalField()
        ),
        extra_price=Case(
            When(cost_price_currency="TRY", then=ExpressionWrapper((F("cost_price") / 36) * 1.2, output_field=DecimalField())),
            default=ExpressionWrapper(F("cost_price") * 1.2, output_field=DecimalField()),
            output_field=DecimalField()
        )
    ).order_by('category_path', '-total_score').filter(
        is_advertised=True,
    )[:200]

    return render(request, "face_result/hidden_products.html", {"products": products})

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                # Excel dosyasını okuyun
                df = pd.read_excel(excel_file, engine='openpyxl')
                
                # Sütun isimlerini kontrol edin
                print(df.columns)
                
                pattern = r'"(\d+)"'

                for index, row in df.iterrows():
                    # Tarih ve saat verilerini kontrol edin ve dönüştürün
                    publication_time = pd.to_datetime(row['Yayınlanma Zamanı'], errors='coerce')
                    date = pd.to_datetime(row['Tarih'], errors='coerce').date()

                    # NaT ve NaN değerlerini varsayılan bir değer ile değiştirin
                    if pd.isna(publication_time):
                        publication_time = pd.Timestamp('1970-01-01')
                    if pd.isna(date):
                        date = pd.Timestamp('1970-01-01').date()
                    
                    target_audience_photo_click = row['Eşleşen Hedef Kitle Tüketim Hedeflemesi (Photo Click)'] if pd.notna(row['Eşleşen Hedef Kitle Tüketim Hedeflemesi (Photo Click)']) else 0
                    other_clicks = row['Diğer Tıklamalar'] if pd.notna(row['Diğer Tıklamalar']) else 0
                    link_clicks = row['Bağlantı Tıklamaları'] if pd.notna(row['Bağlantı Tıklamaları']) else 0
                    
                    description = row['Açıklama']
                    match = re.search(pattern, description)
                    post_code = match.group(1) if match else None
                    
                    if post_code is None:
                        # Eğer tırnak içinde sayı bulunamazsa bu satırı atla
                        continue

                    Post.objects.create(
                        post_code=post_code,
                        page_code=row['Sayfa Kodu'],
                        page_name=row['Sayfa Adı'],
                        description=row['Açıklama'],
                        duration=row['Süre (sn)'],
                        publication_time=publication_time,
                        subtitle_type=row['Altyazı Türü'],
                        permalink=row['Sabit Bağlantı'],
                        cross_sharing=row['Çapraz Paylaşım'],
                        sharing=row['Paylaşım'],
                        post_type=row['Gönderi Türü'],
                        languages=row['Diller'],
                        special_tags=row['Özel Etiketler'],
                        sponsored_content_status=row['Finansmanlı içerik durumu'],
                        data_commentary=row['Veri yorumu'],
                        date=date,
                        impressions=row['Gösterimler'],
                        reach=row['Erişim'],
                        reactions=row['İfadeler'],
                        comments=row['Yorumlar'],
                        shares=row['Paylaşımlar'],
                        total_clicks=row['Toplam Tıklamalar'],
                        link_clicks=link_clicks,
                        target_audience_photo_click=target_audience_photo_click,
                        other_clicks=other_clicks,
                        target_audience_video_click=target_audience_video_click,
                        negative_feedback_hide_all=negative_feedback_hide_all,
                        reels_plays_count=row['REELS_PLAYS:COUNT'] if pd.notna(row['REELS_PLAYS:COUNT']) else 0,
                        second_views=row['Saniye görüntülemeler'] if pd.notna(row['Saniye görüntülemeler']) else 0,
                        average_second_views=row['Ortalama Saniye görüntülemeler'] if pd.notna(row['Ortalama Saniye görüntülemeler']) else 0.0,
                        estimated_earnings=row['Tahmini Kazançlar (ABD Doları)'] if pd.notna(row['Tahmini Kazançlar (ABD Doları)']) else 0.0,
                        ad_cpm=row['Reklam CPM\'si (ABD Doları)'] if pd.notna(row['Reklam CPM\'si (ABD Doları)']) else 0.0,
                        ad_impressions=row['Reklam gösterimleri'] if pd.notna(row['Reklam gösterimleri']) else 0
                    )
                
                return HttpResponse("Dosya başarıyla yüklendi ve işlendi.")
            except Exception as e:
                return HttpResponse(f"Dosya işlenirken bir hata oluştu: {str(e)}")
    else:
        form = UploadFileForm()
    return render(request, 'face_result/upload.html', {'form': form})

def upload_file_den(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file, engine='openpyxl')
                # Sütun isimlerini kontrol edin
                print(df.columns)
                
                for index, row in df.iterrows():
                    Postd.objects.create(
                        question1=row['deneme1'],
                        question2=row['deneme2'],
                        question3=row['deneme3'],
                        
                    )
                
                return HttpResponse("Dosya başarıyla yüklendi ve işlendi.")
            except Exception as e:
                return HttpResponse(f"Dosya işlenirken bir hata oluştu: {str(e)}")
             
    else:
        form = UploadFileForm()
    return render(request, 'face_result/upload.html', {'form': form})

def post_list(request):
    order_by = request.GET.get('order_by', '-total_clicks')  # Default sıralama
    direction = request.GET.get('direction', 'asc')  # Default yön
    if direction == 'desc':
        order_by = f'-{order_by}'

    posts = Post.objects.all().order_by(order_by)
    return render(request, 'face_result/post_list.html', {'posts': posts, 'order_by': order_by, 'direction': direction})

def combined_view(request):
    products = Product.objects.all()
    posts = Post.objects.all()
    
    # Barkodları eşleştirmek için bir sözlük yapısı kullanıyoruz
    barcode_dict = {}

    for product in products:
        if product.barcode not in barcode_dict:
            barcode_dict[product.barcode] = {'product': product, 'post': None}
        else:
            barcode_dict[product.barcode]['product'] = product

    for post in posts:
        if post.barcode not in barcode_dict:
            barcode_dict[post.barcode] = {'product': None, 'post': post}
        else:
            barcode_dict[post.barcode]['post'] = post
    
    # Sözlüğü bir listeye dönüştürüyoruz
    combined_list = list(barcode_dict.values())
    
    context = {
        'combined_list': combined_list,
    }
    
    return render(request, 'face_result/your_template.html', context)

def exract_number_vieuw (request):
    tekst = 'Hollanda Outlet Mağazamızda Sürpriz İndirimler Sizleri Bekliyor. "128396" Nucleonweg 1 4706 PZ Roosendaal'
    pattern = r'(\d+)'
    match = re.search(pattern, tekst)
    number =match.group() if match else None
    context = { 
        'number': number,
        'tekst': tekst,
               
    }
    
    
    
    return render(request, 'face_result/exract_number_vieuw.html', context)



def facebook_login(request):
    client_id = '471796758640308'  # Facebook Uygulama ID'niz
    redirect_uri = 'http://localhost:8000/face_result/facebook-callback/'  # Yönlendirme URL'si
    scope = 'pages_manage_metadata,pages_manage_posts,pages_read_engagement,pages_show_list'
    auth_url = f"https://www.facebook.com/v10.0/dialog/oauth?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
    return redirect(auth_url)

def facebook_callback(request):
    client_id = '471796758640308'
    client_secret = '833b0b349df9417b0680bc43a46e6635'
    redirect_uri = 'http://localhost:8000/face_result/facebook-callback/'
    code = request.GET.get('code')

    if not code:
        return JsonResponse({'error': 'Authorization code not provided'}, status=400)

    token_url = f"https://graph.facebook.com/v10.0/oauth/access_token?client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&code={code}"
    token_response = requests.get(token_url)
    
    if token_response.status_code != 200:
        return JsonResponse({'error': 'Failed to retrieve access token', 'details': token_response.json()}, status=token_response.status_code)
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')

    if not access_token:
        return JsonResponse({'error': 'Access token not found in response', 'details': token_data}, status=400)

    # Kullanıcı bilgilerini al
    user_info_url = f"https://graph.facebook.com/me?access_token={access_token}"
    user_info_response = requests.get(user_info_url)
    
    if user_info_response.status_code != 200:
        return JsonResponse({'error': 'Failed to retrieve user info', 'details': user_info_response.json()}, status=user_info_response.status_code)
    
    user_info = user_info_response.json()
    user_id = user_info.get('id')

    # Sayfa erişim tokenlerini al
    pages_url = f"https://graph.facebook.com/{user_id}/accounts?access_token={access_token}"
    pages_response = requests.get(pages_url)
    
    if pages_response.status_code != 200:
        return JsonResponse({'error': 'Failed to retrieve pages info', 'details': pages_response.json()}, status=pages_response.status_code)
    
    pages_data = pages_response.json()

    return JsonResponse(pages_data)

def index(request):
    return render(request, 'face_result/face.html')

def publish_post(request):
    # Kullanmak istediğiniz sayfanın erişim tokenini ve ID'sini alın
    page_access_token = 'EAAGtGL40drQBO8ZCK8FxCVIMETXS1hUUU5ZAu9s32zLE7mti0Vhu8eKAHm444aaQhvwPLRZBoOZCEZAsazFNo5ZC4ydVeQjdPw2OG0HuNATEPaIG9rCSEwhn2tRmIdTSnnWylelRxbG8bT71Hb9KKI8wJlA5EzpI06ICZBTsg78xGzDxknNkdjQZBFxMZAZAY5TiAqpuTsjg4EMEQf7WNV'
    page_id = '302596556573689'
    
    # Yayınlamak istediğiniz mesajı belirleyin
    message = 'Bu bir test gönderisidir.'
    
    # API URL'si
    post_url = f"https://graph.facebook.com/{page_id}/feed"
    
    # POST isteği için veriler
    payload = {
        'message': message,
        'access_token': page_access_token
    }
    
    response = requests.post(post_url, data=payload)
    
    if response.status_code == 200:
        return JsonResponse({'message': 'Post published successfully!', 'response': response.json()})
    else:
        return JsonResponse({'error': 'Failed to publish post', 'details': response.json()}, status=response.status_code)

def get_page_posts(access_token, since_timestamp):
    page_id = "307752226016480"
    url = f"https://graph.facebook.com/v20.0/{page_id}/posts"
    params = {
        "access_token": access_token,
        "fields": "id,message,created_time,full_picture",
        "since": '2024-07-20T00:00:00',
        "limit": 20  # Bir sayfada döndürülecek maksimum gönderi sayısını belirtin
    }
    response = requests.get(url, params=params)
    return response.json()

def get_all_page_posts(access_token, since_timestamp):
    posts = []
    response = get_page_posts(access_token, since_timestamp)
    posts.extend(response.get('data', []))
    
    while 'paging' in response and 'next' in response['paging']:
        next_page_url = response['paging']['next']
        response = requests.get(next_page_url).json()
        posts.extend(response.get('data', []))
    
    return posts

def get_post_insights(post_id, access_token):
    url = f"https://graph.facebook.com/v20.0/{post_id}/insights"
    params = {
        "metric": "post_impressions,post_clicks,post_engaged_users,post_clicks_by_type,post_clicks_unique,page_total_actions",
        "access_token": access_token
    }
    response = requests.get(url, params=params)
    return response.json()

def get_post_likes(post_id, access_token):
    url = f"https://graph.facebook.com/v20.0/{post_id}/likes"
    params = {
        "access_token": access_token,
        "summary": "true"
    }
    response = requests.get(url, params=params)
    return response.json()

def get_liked_users(post_id, access_token):
    liked_users = []
    url = f"https://graph.facebook.com/v20.0/{post_id}/likes"
    params = {
        "access_token": access_token,
        "fields": "name",
        "limit": 10
    }
    while url:
        response = requests.get(url, params=params)
        data = response.json()
        liked_users.extend(user['name'] for user in data.get('data', []))
        url = data.get('paging', {}).get('next')
    
    return liked_users

def get_post_comments(post_id, access_token):
    comments = []
    url = f"https://graph.facebook.com/v20.0/{post_id}/comments"
    params = {
        "access_token": access_token,
        "fields": "message,from{name}",
        "limit": 100
    }
    while url:
        response = requests.get(url, params=params)
        data = response.json()
        comments.extend(
            {"message": comment['message'], "from": comment['from']['name']}
            for comment in data.get('data', [])
        )
        url = data.get('paging', {}).get('next')
    
    return comments

def extract_numbers_from_message(message):
    # Mesajdaki tırnak içerisindeki sayıları çıkarır
    return re.findall(r'"(\d+)"', message)

def display_facebook_posts(request):
    access_token = "EAAGtGL40drQBO8ZCK8FxCVIMETXS1hUUU5ZAu9s32zLE7mti0Vhu8eKAHm444aaQhvwPLRZBoOZCEZAsazFNo5ZC4ydVeQjdPw2OG0HuNATEPaIG9rCSEwhn2tRmIdTSnnWylelRxbG8bT71Hb9KKI8wJlA5EzpI06ICZBTsg78xGzDxknNkdjQZBFxMZAZAY5TiAqpuTsjg4EMEQf7WNV"
    since_timestamp = int(datetime(2024, 7, 1).timestamp())
    
    posts_data = get_all_page_posts(access_token, since_timestamp)
    
    posts_insights = []
    
    for post in posts_data:
        post_id = post['id']
        insights_data = get_post_insights(post_id, access_token)
        likes_data = get_post_likes(post_id, access_token)
        liked_users_data = get_liked_users(post_id, access_token)
        comments_data = get_post_comments(post_id, access_token)
        
        impressions = 0
        clicks = 0
        shares = 0
        likes = 0
        clicks_unique = 0
        page_total_actions = 0
        other_clicks = 0
        photo_view_clicks = 0
        link_clicks = 0
        liked_users = []
        comments = comments_data
        extracted_numbers = ""
        
        if insights_data.get('data'):
            for metric in insights_data['data']:
                if metric['name'] == 'post_impressions':
                    impressions = metric['values'][0]['value']
                if metric['name'] == 'post_clicks':
                    clicks = metric['values'][0]['value']
                if metric['name'] == 'post_engaged_users':
                    post_engaged_users = metric['values'][0]['value']
                if metric['name'] == 'post_clicks_unique':
                    clicks_unique = metric['values'][0]['value']
                if metric['name'] == 'page_total_actions':
                    page_total_actions = metric['values'][0]['value']
                if metric['name'] == 'post_clicks_by_type':
                    post_clicks_by_type = metric['values'][0]['value']
                    other_clicks = post_clicks_by_type.get('other clicks', 0)
                    photo_view_clicks = post_clicks_by_type.get('photo view', 0)
                    link_clicks = post_clicks_by_type.get('link clicks', 0)
                    
        if likes_data.get('summary'):
            likes = likes_data['summary']['total_count']
        
        liked_users = liked_users_data
        
        message = post.get('message', "")
        extracted_numbers_list = extract_numbers_from_message(message)
        extracted_numbers = ",".join(extracted_numbers_list)  # Sayıları virgülle birleştirerek tek bir string oluşturun
        
        
        post_record, created = FacebookPost.objects.update_or_create(
            post_id=post_id,
            defaults={
                'message': message,
                'created_time': post.get('created_time', ''),
                'full_picture': post.get('full_picture', ''),
                'impressions': impressions,
                'clicks_unique': clicks_unique,
                'clicks': clicks,
                'shares': shares,
                'likes': likes,
                'page_total_actions': page_total_actions,
                'other_clicks': other_clicks,
                'photo_view_clicks': photo_view_clicks,
                'link_clicks': link_clicks,
                'extracted_number': extracted_numbers,  # Tek bir string olarak kaydedin
                'page_total_actions' : post_engaged_users           }
        )

        # Eğer extracted_numbers doluysa ve product veritabanında mevcutsa güncellemeleri yap
        if extracted_numbers:
            try:
                product = Product.objects.get(product_id=extracted_numbers)
                if not product.score_total_updated:
                    product.score_total -= 0.20
                    product.score_total_updated = True
                    product.save()
            except Product.DoesNotExist:
                pass
        
        for user in liked_users:
            FacebookLike.objects.get_or_create(
                post=post_record,
                user_name=user
            )
        
        for comment in comments:
            FacebookComment.objects.get_or_create(
                post=post_record,
                message=comment['message'],
                author=comment['from']
            )
        
        posts_insights.append({
            'post_id': post_id,
            'message': message,
            'created_time': post.get('created_time', ''),
            'full_picture': post.get('full_picture', ''),
            'impressions': impressions,
            'clicks': clicks,
            'post_engaged_users': post_engaged_users,
            'likes': likes,
            'clicks_unique': clicks_unique,
            'page_total_actions': page_total_actions,
            'other_clicks': other_clicks,
            'photo_view_clicks': photo_view_clicks,
            'link_clicks': link_clicks,
            'liked_users': liked_users,
            'comments': comments,
            'extracted_numbers': extracted_numbers  # Elde edilen sayıları ekleyin
        })
    
    return render(request, 'face_result/facebook_posts.html', {'posts': posts_insights})

def update_post_calculation():
    posts = FacebookPost.objects.all()
    for post in posts:
        if post.impressions is not None and post.page_total_actions is not None:
            result = (post.impressions / 200000) * post.page_total_actions
            post.calculation_result = result
            post.save()



def product_list (request):
    products = Product.objects.all()
    
    product_with_score = []
    product_number = 1
    
    for product in products:
        if product.score_view is not None and product.score_view != 0:
            score_view_multiplier = product.score_view *2
            nieuw_score_multipler = score_view_multiplier *12
            nieuwe_score_divide = nieuw_score_multipler / score_view_multiplier
           
        else:
            score_view_multiplier = 0
            nieuw_score_multipler = 0    
            nieuwe_score_divide  = 0
            nieuwe_score_divide  =  0
            
        product_with_score.append({
            'product_id' : product_number,
            'product_name' : product.name,
            'product_brand' : product.brand,
            'score_view' : product.score_view,
            'product_code': product.product_code,
            'score_view_multiplier': score_view_multiplier,
            'nieuw_score_multipler' : nieuw_score_multipler,
            'nieuwe_score_divide': nieuwe_score_divide,
        })    
        
        product_number += 1
        
    
    return render(request, 'face_result/product_list2.html', {'products': product_with_score})        
            
def draw_and_show_polygon(request):
    # Koordinatlar (yüzde değerler, A4 sayfası üzerinde normalize edilmiş)
    polygon_coords = [
        [0.41, 0.092],
        [0.536, 0.092],
        [0.536, 0.106],
        [0.41, 0.106]
    ]

    # A4 sayfasının boyutları (mm cinsinden)
    a4_width_mm = 210
    a4_height_mm = 297

    # Koordinatları A4 sayfası boyutlarına dönüştürme
    polygon_coords_mm = [[x * a4_width_mm, y * a4_height_mm] for x, y in polygon_coords]

    # Grafik oluşturma
    fig, ax = plt.subplots()
    ax.set_xlim(0, a4_width_mm)
    ax.set_ylim(0, a4_height_mm)
    ax.set_aspect('equal')
    ax.set_xlabel('Width (mm)')
    ax.set_ylabel('Height (mm)')
    ax.set_title('A4 Sayfası Üzerinde Koordinatlar')

    # Polygonu çiz
    polygon = patches.Polygon(polygon_coords_mm, closed=True, fill=None, edgecolor='r')
    ax.add_patch(polygon)

    # Görüntüyü PNG formatında kaydetme
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    # HTTP yanıtı oluşturma
    response = HttpResponse(buf, content_type='image/png')
    
    return response

# OAuth 2.0 Scopes for Gmail API
SCOPES = [
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.settings.basic'
]

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def authenticate_gmail(request):
    creds = None
    if os.path.exists('credentials.json'):
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = Flow.from_client_secrets_file('credentials.json', SCOPES)
                flow.redirect_uri = request.build_absolute_uri(reverse('oauth2callback'))

                authorization_url, state = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true')

                request.session['state'] = state
                return redirect(authorization_url)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
    else:
        raise FileNotFoundError("credentials.json file not found")
    return creds

def oauth2callback(request):
    state = request.session['state']
    flow = Flow.from_client_secrets_file('credentials.json', SCOPES, state=state)
    flow.redirect_uri = request.build_absolute_uri(reverse('oauth2callback'))

    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    return redirect('create_label')

def get_pdf_attachments(service, user_id, query):
    results = service.users().messages().list(userId=user_id, q=query).execute()
    messages = results.get('messages', [])

    pdf_files = []

    if not messages:
        print("No messages found.")
    else:
        for message in messages:
            msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
            for part in msg['payload']['parts']:
                if part['filename'] and 'application/pdf' in part['mimeType']:
                    if 'data' in part['body']:
                        data = part['body']['data']
                    else:
                        att_id = part['body']['attachmentId']
                        att = service.users().messages().attachments().get(userId=user_id, messageId=message['id'], id=att_id).execute()
                        data = att['data']
                    file_data = base64.urlsafe_b64decode(data)
                    path = os.path.join(settings.MEDIA_ROOT, part['filename'])
                    with open(path, 'wb') as f:
                        f.write(file_data)
                    pdf_files.append(part['filename'])
    return pdf_files

def pdf_list_view(request):
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)
    
    creds = authenticate_gmail(request)
    if isinstance(creds, HttpResponse):  # Eğer doğrulama gerekli ise
        return creds

    service = build('gmail', 'v1', credentials=creds)

    user_id = 'me'
    query = 'from:savas@alkapida.com label:PDF-faturalar has:attachment filename:pdf'
    pdf_files = get_pdf_attachments(service, user_id, query)

    context = {
        'pdf_files': pdf_files,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    
    return render(request, 'face_result/pdf_list.html', context)

def create_label(request):
    creds = authenticate_gmail(request)
    if isinstance(creds, HttpResponse):  # Eğer doğrulama gerekli ise
        return creds

    service = build('gmail', 'v1', credentials=creds)
    
    if request.method == 'POST':
        label_name = request.POST.get('label_name')
        visibility = request.POST.get('visibility')
        message_visibility = request.POST.get('message_visibility')

        label = {
            'name': label_name,
            'labelListVisibility': visibility,
            'messageListVisibility': message_visibility
        }

        try:
            created_label = service.users().labels().create(userId='me', body=label).execute()
            messages.success(request, f'Label {created_label["name"]} created successfully!')
        except HttpError as e:
            messages.error(request, f'An error occurred: {str(e)}')

    return render(request, 'face_result/create_label.html')

def create_filter(request):
    creds = authenticate_gmail(request)
    if isinstance(creds, HttpResponse):  # Eğer doğrulama gerekli ise
        return creds

    service = build('gmail', 'v1', credentials=creds)
    
    if request.method == 'POST':
        from_email = request.POST.get('from_email')
        label_name = request.POST.get('label_name')
        user_email = request.POST.get('user_email')  # Kullanıcının e-posta adresini alın

        try:
            # Etiketin ID'sini alın
            labels = service.users().labels().list(userId=user_email).execute()
            label_id = None
            for label in labels['labels']:
                if label['name'] == label_name:
                    label_id = label['id']
                    break

            if not label_id:
                messages.error(request, f'Label {label_name} not found.')
                return render(request, 'face_result/create_filter.html')

            # Filtre oluşturun
            filter_body = {
                'criteria': {
                    'from': from_email
                },
                'action': {
                    'addLabelIds': [label_id],
                    'removeLabelIds': ['INBOX']
                }
            }

            created_filter = service.users().settings().filters().create(userId=user_email, body=filter_body).execute()
            messages.success(request, f'Filter created successfully for emails from {from_email} to label {label_name}!')

        except HttpError as error:
            messages.error(request, f'An error occurred: {error}')

    return render(request, 'face_result/create_filter.html')


# Ortam değişkenini ayarlayın
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\31621\\Downloads\\alkapida-1490688048932-b9250de86516.json'

# Google Vision istemcisi oluşturun
# client = vision.ImageAnnotatorClient()
# def get_image_properties(request):
#     """Görüntünün özelliklerini döndüren bir fonksiyon."""
#     if request.method == 'POST' and request.FILES.get('image'):
#         image_file = request.FILES['image']
#         content = image_file.read()
        
#         image = types.Image(content=content)
#         response = client.image_properties(image=image)
#         props = response.image_properties_annotation
        
#         # Baskın renkleri çıkar
#         dominant_colors = extract_dominant_colors(props)
#         return JsonResponse({'dominant_colors': dominant_colors})
    
#     return JsonResponse({'error': 'No image provided'}, status=400)

# def extract_dominant_colors(props):
#     """Görüntüden baskın renkleri çıkaran bir fonksiyon."""
#     colors = []
#     for color in props.dominant_colors.colors:
#         colors.append({
#             'red': color.color.red,
#             'green': color.color.green,
#             'blue': color.color.blue
#         })
#     return colors

# def cendex(request):
#     return render(request, 'face_result/cendex.html')


import os
from django.shortcuts import render
from django.http import JsonResponse
from google.cloud import vision_v1 as vision
from .models import Photo

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\31621\\Downloads\\vision-project-2-b2d238969216.json'

# Google Vision istemcisi oluşturun
client = vision.ImageAnnotatorClient()

def upload_photo(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        images = request.FILES.getlist('images')
        results = []

        for image_file in images:
            photo = Photo(image=image_file)
            photo.save()

            try:
                # Google Vision API ile renk analizi
                image_file.seek(0)  # Dosya akışını başa sarın
                content = image_file.read()
                image = vision.Image(content=content)

                # Gerekli özellikleri belirtin
                features = [
                    vision.Feature(type=vision.Feature.Type.IMAGE_PROPERTIES),
                    vision.Feature(type=vision.Feature.Type.TEXT_DETECTION)
                ]
                request_annotate = vision.AnnotateImageRequest(image=image, features=features)

                response = client.annotate_image(request=request_annotate)
                props = response.image_properties_annotation
                texts = response.text_annotations

                # Baskın renkleri çıkar
                dominant_colors = extract_dominant_colors(props)

                # OCR metnini çıkar
                ocr_text = texts[0].description if texts else ""

                # Verileri veritabanına kaydet
                photo.dominant_colors = dominant_colors
                photo.ocr_text = ocr_text
                if dominant_colors:
                    photo.red = dominant_colors[0]['red']
                    photo.green = dominant_colors[0]['green']
                    photo.blue = dominant_colors[0]['blue']
                photo.save()

                results.append({'image': photo.image.url, 'dominant_colors': dominant_colors, 'ocr_text': ocr_text})

            except Exception as e:
                results.append({'error': str(e)})

        return JsonResponse({'results': results})

    return render(request, 'face_result/upload_photo.html')

def find_similar_photos(photo):
    """Benzer fotoğrafları bulmak için bir fonksiyon."""
    photos = Photo.objects.all()
    similarities = []

    for other_photo in photos:
        if other_photo.id != photo.id and photo.dominant_colors and other_photo.dominant_colors:
            distance = color_distance(photo.dominant_colors, other_photo.dominant_colors)
            similarities.append((other_photo, distance))

    similarities.sort(key=lambda x: x[1])
    return [sim[0] for sim in similarities[:5]]

def color_distance(colors1, colors2):
    """İki renk listesi arasındaki ortalama renk mesafesini hesaplayan bir fonksiyon."""
    if not colors1 or not colors2:
        return float('inf')

    total_distance = 0
    count = min(len(colors1), len(colors2))

    for i in range(count):
        color1 = colors1[i]
        color2 = colors2[i]
        distance = ((color1['red'] - color2['red']) ** 2 +
                    (color1['green'] - color2['green']) ** 2 +
                    (color1['blue'] - color2['blue']) ** 2) ** 0.5
        total_distance += distance

    return total_distance / count

def photo_list(request):
    photos = Photo.objects.all()
    return render(request, 'face_result/photo_list.html', {'photos': photos})

def analyze_and_save_products(request):
    # Google Vision istemcisini oluşturun
    client = vision.ImageAnnotatorClient()

    # Veritabanından 100 ürünü çekin
    products = Product.objects.all()[:10]

    for product in products:
        image_uris = product.images.split(',')  # Virgülle ayrılmış resim URL'lerini ayırın
        if not image_uris:
            continue

        first_image_uri = image_uris[0]  # İlk resim URL'sini alın
        print(f"Processing {product.name} with image {first_image_uri}")

        image = vision.Image()
        image.source.image_uri = first_image_uri

        # Görüntü özelliklerini belirtin
        features = [
            vision.Feature(type=vision.Feature.Type.IMAGE_PROPERTIES),
            vision.Feature(type=vision.Feature.Type.TEXT_DETECTION)
        ]
        request_annotate = vision.AnnotateImageRequest(image=image, features=features)

        try:
            response = client.annotate_image(request=request_annotate)
            props = response.image_properties_annotation
            texts = response.text_annotations

            dominant_colors = extract_dominant_colors(props)
            ocr_text = texts[0].description if texts else ""

            # Photo modeline kaydet
            photo = Photo(
                image=first_image_uri,
                name=product.name,
                red=dominant_colors[0]['red'] if dominant_colors else None,
                green=dominant_colors[0]['green'] if dominant_colors else None,
                blue=dominant_colors[0]['blue'] if dominant_colors else None,
                ocr_text=ocr_text,
                dominant_colors=dominant_colors
            )
            photo.save()
            print(f"Processed {product.name}: {dominant_colors}, OCR Text: {ocr_text}")

        except Exception as e:
            # Hata durumunda mesajı kaydedebilirsiniz
            print(f"Error processing {product.name}: {e}")

    # Analyze products sayfasına yönlendirme
    return render(request, 'face_result/analyze_products.html', {'photos': Photo.objects.all()})

def extract_dominant_colors(props):
    """Görüntüden baskın renkleri çıkaran bir fonksiyon."""
    colors = []
    if props:
        for color in props.dominant_colors.colors:
            colors.append({
                'red': color.color.red,
                'green': color.color.green,
                'blue': color.color.blue
            })
    return colors

def analyze_products(request):
    photos = Photo.objects.all()
    return render(request, 'face_result/analyze_products.html', {'photos': photos})

def photo_detail(request, id):
    photo = get_object_or_404(Photo, id=id)
    similar_photos = find_similar_photos(photo)
    return render(request, 'face_result/photo_detail.html', {'photo': photo, 'similar_photos': similar_photos})