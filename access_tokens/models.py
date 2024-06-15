from django.db import models

# access_tokens/models.py

from django.db import models

class UserIdentity(models.Model):
    identity_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.TextField(null=True, blank=True)
    expires_on = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.identity_id

