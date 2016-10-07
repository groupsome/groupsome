from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

# User class from Django maybe to extend


class Group(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    chat_photo_file_id = models.CharField(_("Chat Photo File ID"), max_length=100, null=True, blank=True)
    header = models.ImageField(_("Header Image"), null=True, blank=True)
    header_version = models.IntegerField(_("Header Image Version"), default=0)
    description = models.CharField(_("Description"), max_length=200, null=True, blank=True)
    users = models.ManyToManyField(User, related_name="memberships")
    telegram_id = models.IntegerField(_("Telegram ID"), unique=True)
    creator = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    admins = models.ManyToManyField(User, related_name="admin_of")
    everyone_is_admin = models.BooleanField(default=True)

    @classmethod
    def create_and_save(cls, name, picture, description, telegram_id, everyone_is_admin=True):
        group = cls.objects.create(name=name, chat_photo_file_id=picture,
                                   description=description, telegram_id=telegram_id,
                                   everyone_is_admin=everyone_is_admin)
        group.save()
        return group

    @python_2_unicode_compatible
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")

    @property
    def header_media_url(self):
        return reverse("media:group_header", kwargs={"group_id": self.id})+"?_="+str(self.header_version)

    @property
    def chat_photo_media_url(self):
        return reverse("media:group_chat_photo", kwargs={"group_id": self.id})

    @property
    def url(self):
        return reverse("groups:feed", kwargs={"group_id": self.id})

    def has_role(self, user, role):
        # legacy
        if self.creator is None and not self.admins.count():
            return True

        if role == "creator":
            return user == self.creator
        
        if role == "admin":
            if self.everyone_is_admin or user == self.creator:
                return True
            
            return user in self.admins.all()

        return False


# abstract class for all message types
class Message(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    # Format: YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]
    timestamp = models.DateTimeField(_("Timestamp"))
    telegram_id = models.IntegerField(_("Telegram ID"), null=True)

    class Meta:
        abstract = True


class Photo(Message):
    file = models.ImageField(_("File"))
    thumbnail = models.ImageField(_("Thumbnail"), null=True, blank=True)
    type = models.CharField(_("Type"), max_length=10, default="photo")
    version = models.IntegerField(_("Photo Version"), default=0)

    @classmethod
    def create_and_save(cls, user, group, timestamp, file, thumbnail, telegram_id=None):
        photo = cls.objects.create(user=user, group=group, timestamp=timestamp, file=file, thumbnail=thumbnail,
                                   telegram_id=telegram_id)
        photo.save()
        return photo

    class Meta:
        verbose_name = _("Photo")
        verbose_name_plural = _("Photos")

    @property
    def media_url(self):
        return reverse("media:photo", kwargs={"photo_id": self.id})+"?_="+str(self.version)

    @property
    def thumbnail_media_url(self):
        if str(self.file).endswith(".gif"):
            return self.media_url

        return reverse("media:photo_thumbnail", kwargs={"photo_id": self.id})+"?_="+str(self.version)

    def get_albums(self):
        albums = []
        for a in self.albums.all():
            albums.append(a.id)
        return albums


class Text(Message):
    content = models.TextField(_("Content"))
    type = models.CharField(_("Type"), max_length=10, default="text")

    @classmethod
    def create_and_save(cls, user, group, timestamp, content, telegram_id=None):
        text = cls.objects.create(user=user, group=group, timestamp=timestamp, content=content, telegram_id=telegram_id)
        text.save()
        return text

    @python_2_unicode_compatible
    def __str__(self):
        return self.content

    class Meta:
        verbose_name = _("Text")
        verbose_name_plural = _("Texts")


class Audio(Message):
    file = models.FileField(_("File"))
    duration_sec = models.PositiveIntegerField(_("DurationSeconds"), null=True, blank=True)
    title = models.CharField(_("Title"), max_length=150, null=True, blank=True)
    interpret = models.CharField(_("Interpret"), max_length=150, null=True, blank=True)
    type = models.CharField(_("Type"), max_length=10, default="audio")

    @classmethod
    def create_and_save(cls, user, group, timestamp, file, duration_sec, title, interpret, telegram_id):
        audio = cls.objects.create(user=user, group=group, timestamp=timestamp, file=file, duration_sec=duration_sec,
                                   title=title, interpret=interpret, telegram_id=telegram_id)
        audio.save()
        return audio

    class Meta:
        verbose_name = _("Audio")
        verbose_name_plural = _("Audios")

    @property
    def media_url(self):
        return reverse("media:audio", kwargs={"audio_id": self.id})

    @property
    def full_title(self):
        if self.interpret:
            return self.title + " - " + self.interpret
        return self.title


class Video(Message):
    file = models.FileField(_("File"))
    duration_sec = models.PositiveIntegerField(_("DurationSeconds"), null=True, blank=True)
    width = models.PositiveIntegerField(_("Width"), null=True, blank=True)
    height = models.PositiveIntegerField(_("Height"), null=True, blank=True)
    thumbnail = models.ImageField(_("Thumbnail"), null=True, blank=True)
    type = models.CharField(_("Type"), max_length=10, default="video")

    @classmethod
    def create_and_save(cls, user, group, timestamp, file, duration_sec, width, height, thumbnail, telegram_id=None):
        video = cls.objects.create(user=user, group=group, timestamp=timestamp, file=file, duration_sec=duration_sec,
                                   width=width, height=height, thumbnail=thumbnail, telegram_id=telegram_id)
        video.save()
        return video

    class Meta:
        verbose_name = _("Video")
        verbose_name_plural = _("Videos")

    @property
    def media_url(self):
        return reverse("media:video", kwargs={"video_id": self.id})

    @property
    def thumbnail_media_url(self):
        return reverse("media:video_thumbnail", kwargs={"video_id": self.id})


class Link(Message):
    url = models.URLField()
    type = models.CharField(_("Type"), max_length=10, default="link")
    title = models.CharField(_("Title"), max_length=255, default=None, null=True)
    description = models.TextField(_("Description"), default=None, null=True)
    file = models.FileField(_("File"), default=None, null=True)  # TODO URLField to FileField

    @classmethod
    def create_and_save(cls, user, group, timestamp, url, telegram_id=None, title=None, description=None, file=None):
        link = cls.objects.create(user=user, group=group, timestamp=timestamp, url=url, telegram_id=telegram_id,
                                  title=title, description=description, file=file)
        link.save()
        return link

    @python_2_unicode_compatible
    def __str__(self):
        return self.url

    class Meta:
        verbose_name = _("Link")
        verbose_name_plural = _("Links")

    @property
    def link_preview_media_url(self):
        return reverse("media:link_preview", kwargs={"link_id": self.id})


class Directory(models.Model):
    group = models.ForeignKey(Group, related_name='directories')
    name = models.CharField(_("Name"), max_length=100)
    parent = models.ForeignKey("self", null=True, related_name='childs', on_delete=models.CASCADE)

    @classmethod
    def create_and_save(cls, group, name, parent=None):
        entry = cls.objects.create(group=group, name=name, parent=parent)
        entry.save()
        return entry


class File(Message):
    other_file = models.FileField(_("File"))
    doc_type = models.CharField(_("Type"), max_length=50)
    file_name = models.CharField(_("Filename"), max_length=100)
    directory = models.ForeignKey(Directory, null=True, on_delete=models.CASCADE)
    type = "file"

    def __str__(self):
        return self.other_file.name

    @classmethod
    def create_and_save(cls, user, group, timestamp, other_file, doc_type, file_name, telegram_id, directory=None):
        file = cls.objects.create(user=user, group=group, timestamp=timestamp, other_file=other_file, doc_type=doc_type,
                                  file_name=file_name, telegram_id=telegram_id, directory=directory)
        file.save()
        return file

    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")

    @property
    def media_url(self):
        return reverse("media:file", kwargs={"file_id": self.id})

    @property
    def icon(self):
        known_mimetypes = {
            "application/pdf": "file-pdf-o",

            "application/gzip": "file-archive-o",
            "application/x-tar": "file-archive-o",
            "application/zip": "file-archive-o",
            "application/x-bzip-compressed-tar": "file-archive-o",
        }

        if self.doc_type.startswith("image/"):
            return "file-picture-o"
        elif self.doc_type.startswith("audio/"):
            return "file-audio-o"
        elif self.doc_type.startswith("video/"):
            return "file-movie-o"
        elif self.doc_type.startswith("text/"):
            return "file-text-o"
        else:
            return known_mimetypes.get(self.doc_type, "file-o")

    @property
    def icon_alt(self):
        icons = {
            "file-pdf-o": "file",
            "file-archive-o": "archive",
            "file-picture-o": "picture-o",
            "file-audio-o": "volume-up",
            "file-movie-o": "video-camera",
            "file-text-o": "file-text",
            "file-o": "file",
        }

        return icons.get(self.icon, self.icon)


class Sticker(Message):
    file = models.ImageField(_("File"))
    type = models.CharField(_("Type"), max_length=10, default="sticker")

    @classmethod
    def create_and_save(cls, user, group, timestamp, file, telegram_id):
        sticker = cls.objects.create(user=user, group=group, timestamp=timestamp, file=file, telegram_id=telegram_id)
        sticker.save()
        return sticker

    class Meta:
        verbose_name = _("Sticker")
        verbose_name_plural = _("Stickers")

    @property
    def media_url(self):
        return reverse("media:sticker", kwargs={"sticker_id": str(self.id)})
