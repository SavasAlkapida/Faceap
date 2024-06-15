from django import forms
from django.forms import ModelForm
from tweetapp.models import Tweet
from .models import Reklam

class AddTweetForm(forms.Form):
    nickname_input = forms.CharField(label="Nickname",max_length=50)
    message_input = forms.CharField(label="Message",max_length=100,
                                    widget=forms.Textarea(attrs={"class":"tweetmessage"}))
    

class AddTweetModelForm(ModelForm):
    class Meta:
        model = Tweet
        fields = ["username","message"]
        
     
        
class ReklamForm(forms.ModelForm):
    class Meta:
        model = Reklam
        fields = ['isim', 'yayinlanma_tarihi', 'bitis_tarihi', 'rating','goruntuleme_sayisi','tiklama_sayisi']
        widgets = {
            'isim': forms.TextInput(attrs={'class': 'form-control'}),
            'yayinlanma_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bitis_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control'}),
            'goruntuleme_sayisi': forms.NumberInput(attrs={'class': 'form-control'}),
            'tiklama_sayisi': forms.NumberInput(attrs={'class': 'form-control'}),
        }        