from django.urls import path
from . import views

app_name = 'tweetapp'

urlpatterns = [
    path('', views.listtweet, name='listtweet'),  # atilsamancioglu.com/tweetapp/
    path('add_reklam/', views.add_reklam, name='add_reklam'),
    path('reklamlar/', views.reklam_listele_kaydet_ve_grafik, name='reklamlar'),
    path('addtweet/', views.addtweet, name='addtweet'),  # atilsamancioglu.com/tweetapp/addtweet
    path('addtweetbyform', views.addtweetbyform, name='addtweetbyform'),  # atilsamancioglu.com/tweetapp/addtweetbyform
    path('addtweetbymodelform', views.addtweetbymodelform, name='addtweetbymodelform'),
    path('signup/', views.SignUpView.as_view(), name="signup"),
    path('deletetweet/<int:id>', views.deletetweet, name="deletetweet"),
    path('reklamlar/sil/<int:reklam_id>/', views.reklam_sil, name='reklam_sil'),
    path('grafik/', views.reklam_grafik_view, name='grafik_view'),
    path('reklamlar/guncelle/<int:pk>/', views.reklam_guncelle, name='reklam_guncelle'),
    path('get_communication_token/', views.get_communication_token, name='get_communication_token'),
    path('index', views.index, name='index'),
]

