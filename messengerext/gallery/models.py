from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from home.models import Photo, Video, Group
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class Album(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    description = models.CharField(_("Description"), max_length=200,
                                   null=True, blank=True)
    photos = models.ManyToManyField(Photo, related_name="albums")
    videos = models.ManyToManyField(Video)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    cover = models.ForeignKey(Photo, null=True, on_delete=models.SET_NULL, related_name="cover_of_albums")

    @classmethod
    def create_and_save(cls, name, description, group):
        album = cls.objects.create(name=name, description=description, group=group)
        album.save()
        return album

    @python_2_unicode_compatible
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Album")
        verbose_name_plural = _("Albums")
