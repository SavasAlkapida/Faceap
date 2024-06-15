# access_tokens/forms.py

from django import forms

class TokenRequestForm(forms.Form):
    hours = forms.IntegerField(label='Token Validity (hours)', min_value=1, max_value=24, initial=1)
    
class TokenRenewalForm(forms.Form):
    identity_id = forms.CharField(label='Identity ID', max_length=255)
    hours = forms.IntegerField(label='Token Validity (hours)', min_value=1, max_value=24, initial=1)    
