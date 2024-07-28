from celery import shared_task
from .models import Product, DailyProductData, FacebookPost, FacebookLike, FacebookComment
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

@shared_task
def record_daily_score_view():
    try:
        products = Product.objects.all()
        for product in products:
            DailyProductData.objects.create(
                product=product,
                score_view=product.score_view
            )
            print(f"Recorded daily score_view for product {product.product_id}")
    except Exception as e:
        print(f"Error recording daily score_view: {e}")
        raise e

@shared_task
def fetch_xml_data():
    try:
        xml_url = 'https://www.alkapida.com/feeds/products/promotion-products.xml'
        response = requests.get(xml_url)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        for product_element in root.findall('product'):
            product_id = product_element.find('product_id').text
            product_name = product_element.find('name').text
            product_score = product_element.find('score_view').text

            product, created = Product.objects.get_or_create(product_id=product_id)
            product.name = product_name
            product.score_view = product_score
            product.save()

        print("XML data fetched and processed.")
        
    except Exception as e:
        print(f"Error fetching and processing XML data: {e}")
        raise e

def get_page_posts(access_token, since_timestamp, limit=100):
    page_id = "307752226016480"
    url = f"https://graph.facebook.com/v20.0/{page_id}/posts"
    params = {
        "access_token": access_token,
        "fields": "id,message,created_time,full_picture",
        "since": since_timestamp,
        "limit": limit
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

# Facebook gönderilerini ve etkileşimlerini güncelleyen görev
@shared_task
def fetch_facebook_posts():
    def get_page_posts(access_token, since_timestamp, limit=20):
        page_id = "307752226016480"
        url = f"https://graph.facebook.com/v20.0/{page_id}/posts"
        params = {
            "access_token": access_token,
            "fields": "id,message,created_time,full_picture",
            "since": since_timestamp,
            "limit": limit
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
            "metric": "post_impressions,post_clicks,post_engaged_users",
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
            "limit": 100
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

    access_token = "EAAGtGL40drQBO8ZCK8FxCVIMETXS1hUUU5ZAu9s32zLE7mti0Vhu8eKAHm444aaQhvwPLRZBoOZCEZAsazFNo5ZC4ydVeQjdPw2OG0HuNATEPaIG9rCSEwhn2tRmIdTSnnWylelRxbG8bT71Hb9KKI8wJlA5EzpI06ICZBTsg78xGzDxknNkdjQZBFxMZAZAY5TiAqpuTsjg4EMEQf7WNV"
    since_timestamp = int(datetime(2024, 7, 1).timestamp())
    
    posts_data = get_all_page_posts(access_token, since_timestamp)
    
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
        liked_users = []
        comments = comments_data
        
        if insights_data.get('data'):
            for metric in insights_data['data']:
                if metric['name'] == 'post_impressions':
                    impressions = metric['values'][0]['value']
                if metric['name'] == 'post_clicks':
                    clicks = metric['values'][0]['value']
                if metric['name'] == 'post_engaged_users':
                    shares = metric['values'][0]['value']
        
        if likes_data.get('summary'):
            likes = likes_data['summary']['total_count']
        
        liked_users = liked_users_data
        
        post_record, created = FacebookPost.objects.get_or_create(
            post_id=post_id,
            defaults={
                'message': post.get('message', ''),
                'created_time': post.get('created_time', ''),
                'full_picture': post.get('full_picture', ''),
                'impressions': impressions,
                'clicks': clicks,
                'shares': shares,
                'likes': likes,
            }
        )
        
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
