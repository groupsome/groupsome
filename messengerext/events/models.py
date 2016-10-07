from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from home.models import Group
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class Event(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    start = models.DateTimeField(_("Start"))
    location = models.CharField(_("Location"), max_length=100)
    group = models.ForeignKey(Group)
    allday = models.NullBooleanField(_("Allday"))
    job_id = models.CharField(max_length=50, null=True)

    @classmethod
    def create_and_save(cls, name, group, location, allday, start):
        event = cls.objects.create(name=name, group=group, location=location,
                                   allday=allday, start=start)
        event.save()
        return event

    @python_2_unicode_compatible
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")


class Attending(models.Model):
    user = models.ForeignKey(User)
    status = models.CharField(_("Status"), max_length=8, default="maybe")
    event = models.ManyToManyField(Event, related_name="attending")

    @classmethod
    def create_and_save(cls, user, status):
        attending = cls.objects.create(user=user, status=status)
        attending.save()
        return attending

    class Meta:
        verbose_name = _("Attending")
        verbose_name_plural = _("Attending")
