from django.urls import path
from .views import issue_access_tokens, list_user_identities, delete_user_identity, issue_access_tokens, renew_access_token, get_access_token, index


urlpatterns = [
    path('', index, name='index'),
    path('issue-tokens/', issue_access_tokens, name='issue_access_tokens'),
    path('list-identities/', list_user_identities, name='list_user_identities'),
    path('delete-identity/<str:identity_id>/', delete_user_identity, name='delete_user_identity'),
    path('issue-tokens/', issue_access_tokens, name='issue_access_tokens'),
    path('renew-token/', renew_access_token, name='renew_access_token'),
    path('get-access-token/', get_access_token, name='get_access_token'),
    
]