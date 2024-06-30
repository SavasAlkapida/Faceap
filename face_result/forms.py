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
    file = forms.FileField(label='Excel Dosyasını Yükleyin')

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError("Yalnızca .xlsx uzantılı dosyalar yükleyebilirsiniz.")
        return file

class UploadFileForm2(forms.Form):
    file = forms.FileField(label='Excel Dosyasını Yükleyin')

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError("Yalnızca .xlsx uzantılı dosyalar yükleyebilirsiniz.")
        return file    
    
