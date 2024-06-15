from django.core.management.base import BaseCommand
import pandas as pd
from ...models import SocialMediaPost  # Doğru yolu sağlamak için bu importu uyarlayın

class Command(BaseCommand):
    help = 'Imports social media posts from an Excel file into the database'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        self.stdout.write(self.style.SUCCESS(f'Importing data from {file_path}'))
        
        df = pd.read_excel(file_path)

        for index, row in df.iterrows():
            post, created = SocialMediaPost.objects.update_or_create(
                post_code=row['post_code'],
                defaults={
                    'page_code': row['page_code'],
                    'page_name': row['page_name'],
                    'title': row['title'],
                    'description': row['description'],
                    'duration_seconds': row.get('duration_seconds', 0),
                    'publish_time': pd.to_datetime(row['publish_time']),
                    'subtitle_type': row['subtitle_type'],
                    'permalink': row['permalink'],
                    'cross_share': row['cross_share'],
                    'share_type': row['share_type'],
                    'post_type': row['post_type'],
                    'languages': row['languages'],
                    'special_tags': row['special_tags'],
                    'sponsored_content_status': row['sponsored_content_status'],
                    'data_comment': row['data_comment'],
                    'date': pd.to_datetime(row['date']).date() if pd.notnull(row['date']) else None,
                    'impressions': row['impressions'],
                    'reach': row['reach'],
                    'reactions_comments_shares': row['reactions_comments_shares'],
                    'reactions': row['reactions'],
                    'comments': row['comments'],
                    'shares': row['shares'],
                    'total_clicks': row['total_clicks'],
                    'link_clicks': row['link_clicks'],
                    'other_clicks': row['other_clicks'],
                    'matched_target_audience_consumption_photo_click': row['matched_target_audience_consumption_photo_click'],
                    'matched_target_audience_consumption_video_click': row['matched_target_audience_consumption_video_click'],
                    'negative_feedback_from_users_hide_all': row['negative_feedback_from_users_hide_all'],
                    'reels_plays_count': row['reels_plays_count'],
                    'second_views': row['second_views'],
                    'average_second_views': row['average_second_views'],
                    'estimated_earnings_usd': row['estimated_earnings_usd'],
                    'ad_cpm_usd': row['ad_cpm_usd'],
                    'ad_impressions': row['ad_impressions'],
                }
            )
            action = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(f'Post {action}: {post.post_code}'))

        self.stdout.write(self.style.SUCCESS('Import complete!'))
