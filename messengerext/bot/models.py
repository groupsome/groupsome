import hashlib
import datetime
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse


class TelegramLogEntry(models.Model):
    json = models.TextField(_("JSON"))
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True,
                                     auto_now=False)

    @classmethod
    def create_and_save(cls, json):
        entry = cls.objects.create(json=json)
        entry.save()
        return entry


class TelegramUser(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    telegram_id = models.IntegerField(_("Telegram ID"), unique=True)
    avatar_file_id = models.CharField(_("Avatar File ID"), max_length=100, null=True, blank=True)
    avatar_version = models.IntegerField("Avatar Version", default=0)
    timezone_offset = models.IntegerField(_("Timezone Offset"), default=0)
    timezone_setting = models.CharField(_("TZ Setting"), max_length=50, default="UTC")
    language = models.CharField(_("Language"), max_length=8, default="en-us")

    @classmethod
    def create_and_save(cls, user, telegram_id):
        entry = cls.objects.create(user=user, telegram_id=telegram_id)
        entry.save()
        return entry

    @property
    def avatar_url(self):
        return reverse("media:avatar", kwargs={"user_id": self.user_id})+"?_="+str(self.avatar_version)

    def get_default_avatar(self, me):
        d = hashlib.md5(("%d%d" % (self.telegram_id, me.telegramuser.telegram_id))[:15].encode("utf-8")).digest()
        index = d[self.telegram_id % len(d)] % 8
        return "/static/img/avatar/%d.png" % index


class Feedback(models.Model):
    user = models.ForeignKey(User)
    feedback = models.CharField(_("Feedback Text"), max_length=1000, blank=True)

    @classmethod
    def create_and_save(cls, user, feedback):
        entry = cls.objects.create(user=user, feedback=feedback)
        entry.save()
        return entry
