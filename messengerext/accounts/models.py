import random
import string
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class LoginToken(models.Model):
    token = models.CharField(_("Token"), max_length=100, primary_key=True)
    user = models.ForeignKey(User, null=True, default=None)
    created = models.DateTimeField(_("Created"), auto_now_add=True, auto_now=False)
    latestPoll = models.DateTimeField(_("LatestPoll"), auto_now_add=True, auto_now=False)
    host = models.CharField(_("Host"), max_length=50, null=True)

    @classmethod
    def generate_random_string(cls):
        return "".join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
                       for _ in range(10))

    @classmethod
    def create_and_save(cls, host=None):
        token = cls.generate_random_string()
        while (cls.objects.filter(token=token).count()):
            token = cls.generate_random_string()

        entry = cls.objects.create(token=token, host=host)
        entry.save()
        return entry

    def get_url(self):
        return "https://telegram.me/"+settings.TELEGRAM_BOT_USERNAME+"?start=login-"+self.token
        
    def get_scan_url(self):
        return "https://telegram.me/"+settings.TELEGRAM_BOT_USERNAME+"?start=login-"+self.token+"-scan"
