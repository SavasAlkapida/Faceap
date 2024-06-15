from django import forms
from. models import Advertisement

class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = [
            'image',
            'reklam_verme_tarihi', 
            'tiklama_sayisi_face', 
            'goruntuleme_sayisi_face', 
            'tiklama_sayisi_instg', 
            'goruntuleme_sayisi_instgr', 
            'satis_orani', 
            'site_raytingi'
        ]
           
class SearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=200, required=False)        
    
class UploadFileForm(forms.Form):
    file = forms.FileField()  
    
