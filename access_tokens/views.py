from django.shortcuts import render
import os
from django.http import HttpResponse
from .models import UserIdentity
from azure.communication.identity import CommunicationIdentityClient
from azure.identity import DefaultAzureCredential
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from azure.communication.identity import CommunicationUserIdentifier, CommunicationIdentityClient
from .forms import TokenRequestForm
from datetime import timedelta
from .forms import TokenRenewalForm
from django.http import JsonResponse

def index(request):
    return render(request, 'tweetapp/index.html')

def issue_access_tokens(request):
    if request.method == 'POST':
        form = TokenRequestForm(request.POST)
        if form.is_valid():
            hours = form.cleaned_data['hours']
            try:
                print("Azure Communication Services - Access Tokens Quickstart")

                # Ortam değişkenlerinden bağlantı dizesini al
                connection_string = os.getenv('COMMUNICATION_SERVICES_CONNECTION_STRING')

                if not connection_string:
                    return HttpResponse("Bağlantı dizesi bulunamadı.", status=500)

                # İstemciyi başlat
                client = CommunicationIdentityClient.from_connection_string(connection_string)

                # Kullanıcı oluştur ve kimliği al
                user = client.create_user()
                identity_id = user.properties['id']

                # Erişim belirteci süresini belirle
                token_expires_in = timedelta(hours=hours)

                # Erişim belirteci ver
                token_result = client.get_token(CommunicationUserIdentifier(identity_id), ["voip"], token_expires_in=token_expires_in)
                token = token_result.token
                expires_on = token_result.expires_on

                # Kimliği ve belirteci veritabanında sakla
                user_identity = UserIdentity(identity_id=identity_id, token=token, expires_on=expires_on)
                user_identity.save()

                response_message = (
                    f"Created an identity with ID: {identity_id}\n"
                    f"Issued an access token with 'voip' scope that expires at {expires_on}:\n"
                    f"{token}"
                )

                return HttpResponse(response_message)
            except Exception as ex:
                print("Exception:")
                print(ex)
                return HttpResponse(f"Bir hata oluştu: {ex}", status=500)
    else:
        form = TokenRequestForm()

    return render(request, 'access_tokens/issue_access_tokens.html', {'form': form})
    
def list_user_identities(request):
    user_identities = UserIdentity.objects.all()
    return render(request, 'access_tokens/list_user_identities.html', {'user_identities': user_identities})

def delete_user_identity(request, identity_id):
    user_identity = get_object_or_404(UserIdentity, identity_id=identity_id)
    user_identity.delete()
    return redirect('list_user_identities')


def renew_access_token(request):
    if request.method == 'POST':
        form = TokenRenewalForm(request.POST)
        if form.is_valid():
            identity_id = form.cleaned_data['identity_id']
            hours = form.cleaned_data['hours']
            try:
                print("Azure Communication Services - Renew Access Token")

                # Ortam değişkenlerinden bağlantı dizesini al
                connection_string = os.getenv('COMMUNICATION_SERVICES_CONNECTION_STRING')

                if not connection_string:
                    return HttpResponse("Bağlantı dizesi bulunamadı.", status=500)

                # İstemciyi başlat
                client = CommunicationIdentityClient.from_connection_string(connection_string)

                # Mevcut kimlik için CommunicationUserIdentifier nesnesi oluştur
                identity = CommunicationUserIdentifier(identity_id)

                # Erişim belirteci süresini belirle
                token_expires_in = timedelta(hours=hours)

                # Erişim belirteci ver
                token_result = client.get_token(identity, ["voip"], token_expires_in=token_expires_in)
                token = token_result.token
                expires_on = token_result.expires_on

                # Kimliği ve belirteci veritabanında güncelle
                user_identity = UserIdentity.objects.get(identity_id=identity_id)
                user_identity.token = token
                user_identity.expires_on = expires_on
                user_identity.save()

                response_message = (
                    f"Renewed access token for identity ID: {identity_id}\n"
                    f"Issued a new access token with 'voip' scope that expires at {expires_on}:\n"
                    f"{token}"
                )

                return HttpResponse(response_message)
            except UserIdentity.DoesNotExist:
                return HttpResponse("Kimlik bulunamadı.", status=404)
            except Exception as ex:
                print("Exception:")
                print(ex)
                return HttpResponse(f"Bir hata oluştu: {ex}", status=500)
    else:
        form = TokenRenewalForm()

    return render(request, 'access_tokens/renew_access_token.html', {'form': form})

def get_access_token(request):
    connection_string = os.getenv('COMMUNICATION_SERVICES_CONNECTION_STRING')
    if not connection_string:
        return JsonResponse({'error': 'COMMUNICATION_SERVICES_CONNECTION_STRING environment variable not set'}, status=500)

    identity_client = CommunicationIdentityClient.from_connection_string(connection_string)
    
    try:
        identity_token_result = identity_client.create_user_and_token(["voip"], token_expires_in=timedelta(hours=24))
        user_identity = identity_token_result[0]
        token = identity_token_result[1].token
        expires_on = identity_token_result[1].expires_on

        response_data = {
            'identity': user_identity.properties['id'],
            'token': token,
            'expires_on': expires_on.isoformat()
        }
        return JsonResponse(response_data)
    except Exception as ex:
        return JsonResponse({'error': str(ex)}, status=500)
