from django.shortcuts import render, redirect, get_object_or_404
from . import models
from django.views.decorators.cache import never_cache
from django.urls import reverse, reverse_lazy
from tweetapp.forms import AddTweetForm, AddTweetModelForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from .forms import  ReklamForm
from .models import Reklam
from django.core.serializers import serialize
from django.http import JsonResponse
from azure.communication.identity import CommunicationIdentityClient
from django.conf import settings
# Create your views here.


def listtweet(request):
    all_tweets = models.Tweet.objects.all()
    tweet_dict = {"tweets":all_tweets}
    return render(request,'tweetapp/listtweet.html',context=tweet_dict)

@login_required(login_url="/login")
def addtweet(request):
    if request.POST:
        message = request.POST["message"]
        models.Tweet.objects.create(username=request.user, message=message)
        return redirect(reverse('tweetapp:listtweet'))
    else:
        return render(request,'tweetapp/addtweet.html')


def addtweetbyform(request):
    if request.method == "POST":
        form = AddTweetForm(request.POST)
        if form.is_valid():
            nickname = form.cleaned_data["nickname_input"]
            message = form.cleaned_data["message_input"]
            models.Tweet.objects.create(nickname=nickname, message = message)
            return redirect(reverse('tweetapp:listtweet'))
        else:
            print("error in form!")
            return render(request,'tweetapp/addtweetbyform.html', context={"form":form})
    else:
        form = AddTweetForm()
        return render(request,'tweetapp/addtweetbyform.html', context={"form":form})

def addtweetbymodelform(request):
    if request.method == "POST":
        form = AddTweetModelForm(request.POST)
        if form.is_valid():
            nickname = form.cleaned_data["nickname"]
            message = form.cleaned_data["message"]
            models.Tweet.objects.create(nickname=nickname, message = message)            
            return redirect(reverse('tweetapp:listtweet'))
        else:
            print("error in form!")
            return render(request,'tweetapp/addtweetbymodelform.html', context={"form":form})
    else:
        form = AddTweetModelForm()
        return render(request,'tweetapp/addtweetbymodelform.html', context={"form":form})
    
class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = "registration/signup.html"


@login_required
def deletetweet(request, id):
   tweet = models.Tweet.objects.get(pk=id)
   if request.user == tweet.username:
      models.Tweet.objects.filter(id=id).delete()
      return redirect('tweetapp:listtweet')
  
@never_cache
def add_reklam(request):
    if request.method == 'POST':
        form = ReklamForm(request.POST)
        if form.is_valid():
            form.save()
            #form = ReklamForm()
            return redirect(reverse('tweetapp:reklamlar'))

    else:
        form = ReklamForm()
    return render(request, 'tweetapp/add_reklam.html', {'form': form})  

def reklam_listele_kaydet_ve_grafik(request):
    # Arama işlevselliği
    query = request.GET.get('q', '')
    if query:
        reklamlar = Reklam.objects.filter(isim__icontains=query)
    else:
        reklamlar = Reklam.objects.all()
    
    # Reklam ekleme formu
    form = ReklamForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('reklamlar')  # 'reklamlar' URL ismini kontrol edin

    # Grafik için verileri JSON formatına çevirme
    reklamlar_json = serialize('json', reklamlar, fields=('isim', 'goruntuleme_sayisi', 'tiklama_sayisi'))

    # Sonuçları template'e gönderme
    return render(request, 'tweetapp/list.html', {
        'form': form,
        'reklamlar': reklamlar,
        'reklamlar_json': reklamlar_json
    })



def reklam_sil(request, reklam_id):
    reklam = get_object_or_404(Reklam, pk=reklam_id)
    reklam.delete()
    return redirect('tweetapp:reklamlar') 

def reklam_grafik_view(request):
    # Reklamları çekiyoruz
    reklamlar = Reklam.objects.all()
    # Verileri JSON formatına çeviriyoruz
    reklamlar_json = serialize('json', reklamlar, fields=('rating', 'goruntuleme_sayisi'))
    return render(request, 'tweetapp/grafik.html',  {'reklamlar_json': reklamlar_json})

def reklam_suresi_hesapla(request, id):
    reklam = Reklam.objects.get(id=id)
    fark = reklam.bitis_tarihi - reklam.yayinlanma_tarihi
    return render(request, 'tweetapp/list.html', {'reklam': reklam, 'süre': fark.days})


def reklam_guncelle(request, pk):
    reklam = get_object_or_404(Reklam, pk=pk)
    if request.method == 'POST':
        form = ReklamForm(request.POST, instance=reklam)
        if form.is_valid():
            form.save()
            return redirect('tweetapp:reklamlar')
    else:
        form = ReklamForm(instance=reklam)
    return render(request, 'tweetapp/reklam_guncelle.html', {'form': form})


connection_string = settings.AZURE_COMMUNICATION_SERVICE_CONNECTION_STRING
client = CommunicationIdentityClient.from_connection_string(connection_string)



def get_communication_token(request):
    connection_string = settings.AZURE_COMMUNICATION_SERVICE_CONNECTION_STRING
    client = CommunicationIdentityClient.from_connection_string(connection_string)
    user = client.create_user()
    token_response = client.get_token(user, scopes=["voip"])
    return JsonResponse({'token': token_response.token, 'userId': user.properties['id']}, safe=False)




def index(request):
    return render(request, 'tweetapp/index.html', {'connection_string': connection_string})

    