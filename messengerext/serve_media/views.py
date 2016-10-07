import os
from django.views.generic import View
from django.http import HttpResponse, Http404, HttpResponseRedirect, FileResponse, HttpResponseForbidden
from home.models import Photo, Sticker, File, Audio, Video, Link, Group
from accounts.views import LoginRequiredMixin
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


def create_media_response(filename, prettyname, content_type, media_type):
    filename = str(filename)

    if settings.MEDIA_SERVE_USING_NGINX:
        response = HttpResponse()
        response['Content-Disposition'] = "inline; filename=%s" % prettyname
        response['Content-Type'] = content_type
        response['X-Accel-Redirect'] = "/_media/%s/%s" % (media_type, filename)
    else:
        # Content-Type kann nur gesetzt werden wenn auch Content-Disposition gesetzt wird
        # andere Header werden von NGINX ignoriert/ueberschrieben
        response = FileResponse(open(os.path.join(settings.MEDIA_ROOT, media_type, filename), "rb"))
        response['Content-Disposition'] = "inline; filename=%s" % prettyname
        response['Content-Type'] = content_type
    return response


def can_access_group(user, group):
    for g in user.memberships.all():
        if g == group:
            return True
    return False


def get_content_type(extension):
    known_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".png": "image/png",
        ".webp": "image/webp",

        ".mp4": "video/mp4",
        ".ogv": "video/ogg",

        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".oga": "audio/ogg",
    }

    return known_types.get(extension, "application/octet-stream")


def get_media(media_class, media_id, user):
    media = get_object_or_404(media_class, id=media_id)

    if not can_access_group(user, media.group):
        raise PermissionDenied

    return media


def serve_media(media_type, media_id, file):
    file_name, file_extension = os.path.splitext(str(file))
    prettyname = "%s-%s%s" % (media_type, media_id, file_extension)
    content_type = get_content_type(file_extension)
    return create_media_response(file, prettyname, content_type, media_type)


class PhotoView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, photo_id):
        photo = get_media(Photo, photo_id, request.user)
        return serve_media("photo", photo_id, photo.file)


class PhotoThumbnailView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, photo_id):
        photo = get_media(Photo, photo_id, request.user)
        return serve_media("photo-thumbnail", photo_id, photo.thumbnail)


class StickerView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, sticker_id):
        if "webp" in request.META.get("HTTP_ACCEPT"):
            extension = ".webp"
            content_type = "image/webp"
        else:
            extension = ".png"
            content_type = "image/png"

        sticker = get_media(Sticker, sticker_id, request.user)
        short_name = str(sticker.file).split('.')[0]
        filename = os.path.join(settings.MEDIA_ROOT, "sticker", short_name + extension)
        if not os.path.exists(filename):
            raise Http404

        return create_media_response(short_name + extension, short_name + extension, content_type, "sticker")


class FileView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, file_id):
        file = get_media(File, file_id, request.user)
        return serve_media("file", file_id, file.other_file)


class AudioView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, audio_id):
        audio = get_media(Audio, audio_id, request.user)
        return serve_media("audio", audio_id, audio.file)


class VideoView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, video_id):
        video = get_media(Video, video_id, request.user)
        return serve_media("video", video_id, video.file)


class VideoThumbnailView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, video_id):
        video = get_media(Video, video_id, request.user)
        return serve_media("video-thumbnail", video_id, video.thumbnail)


class AvatarView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        if user.telegramuser.avatar_file_id is None:
            return HttpResponseRedirect(user.telegramuser.get_default_avatar(request.user))

        return create_media_response(user.telegramuser.avatar_file_id + ".jpg", user.telegramuser.avatar_file_id +
                                     ".jpg", "image/jpeg", "avatar")


class LinkPreviewView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, link_id):
        link = get_media(Link, link_id, request.user)
        return serve_media("link-preview", link_id, link.file)


class GroupHeaderView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        if not group.header:  # TODO
            return HttpResponseRedirect("/static/img/avatar/0.png")
        return serve_media("group-header", group_id, group.header)


class GroupChatPhotoView(LoginRequiredMixin, View):
    @cache_control(max_age=60*60*24*7)
    def get(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        if not group.chat_photo_file_id:
            return HttpResponseRedirect(reverse("media:group_header", kwargs={"group_id": group_id}))  # TODO
        return serve_media("chat-photo", group_id, group.chat_photo_file_id + ".jpg")
