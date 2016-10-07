from django.shortcuts import render
from accounts.views import LoginRequiredMixin
from django.views.generic import View
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from home import models
from gallery.models import Album
from . import queries
from groups.views import get_group, prepare_context, require_role
from events.views import get_telegram_user_from_request
from django.conf import settings
import os
import django_rq


class AddPhotoView(LoginRequiredMixin, View):

    # /gallery/album_id/add/photo_id : adds photo with photo_id to album with album_id
    def post(self, request, album_id, photo_id, group_id):
        album = queries.get_album_with_id_if_user_is_allowed(request.user, album_id)
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)
        if album is not None and photo is not None:
            require_role(request.user, album.group, "admin")
            if photo in album.photos.all():
                return JsonResponse({'message': _('Already in album')})
            album.photos.add(photo)

            group = get_group(group_id, request.user)
            albums = queries.get_albums_with_covers(Album.objects.filter(group=group))
            context = {
                "albums": albums,
                "photo": photo,
                "group": group,
            }
            return render(request, "assets/photo_options.html", context)
        else:
            return JsonResponse({'message': _('Something went wrong')})


class DeletePhotoFromAlbumView(LoginRequiredMixin, View):

    # /gallery/album_id/delete_from_album/photo_id : removes photo with photo_id from album with album_id
    def get(self, request, album_id, photo_id, group_id):
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)
        require_role(request.user, photo.group, "admin")

        if queries.delete_photo_from_album_if_user_is_allowed(request.user, album_id, photo_id):
            group = get_group(group_id, request.user)
            albums = queries.get_albums_with_covers(Album.objects.filter(group=group))
            context = {
                "albums": albums,
                "photo": photo,
                "group": group,
            }
            return render(request, "assets/photo_options.html", context)
        else:
            return JsonResponse({'message': _('Something went wrong')})

    # /gallery/album_id/delete_from_album/photo_id : removes photo with photo_id from album with album_id
    def post(self, request, album_id, photo_id, group_id):
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)
        require_role(request.user, photo.group, "admin")

        if queries.delete_photo_from_album_if_user_is_allowed(request.user, album_id, photo_id):
            return JsonResponse({'message': _('Successfully removed from album')})
        else:
            return JsonResponse({'message': _('Something went wrong')})


class GroupView(LoginRequiredMixin, View):
    def get(self, request, group_id):
        group = get_group(group_id, request.user)
        t_user = get_telegram_user_from_request(request)
        albums = queries.get_albums_with_covers(Album.objects.filter(group=group))
        photos = models.Photo.objects.filter(group=group)

        context = {
            "albums": albums,
            "photos": photos,
        }

        return render(request, "gallery/group/overview.html", prepare_context(group, t_user, context))

    def post(self, request, group_id):
        if 'new_album' in request.POST:
            group = queries.get_specific_group(request.user, group_id)
            require_role(request.user, group, "admin")
            name = request.POST.get('album_name')
            description = request.POST.get('album_description', "")
            if len(name) > 2 and group is not None:
                Album.create_and_save(name, description, group)
            return HttpResponseRedirect(reverse('groups:photo_overview', kwargs={"group_id": group_id}))

        elif 'delete_album' in request.POST:
            group = queries.get_specific_group(request.user, group_id)
            require_role(request.user, group, "admin")
            album_id = request.POST.get('album_id')
            album = queries.get_album_with_id_if_user_is_allowed(request.user, album_id)
            if album is not None and album.group == group:
                album.delete()
                messages.success(request, _("Album deleted successfully!"))
            return HttpResponseRedirect(reverse('groups:photo_overview', kwargs={"group_id": group_id}))


class GroupAlbumDetailView(LoginRequiredMixin, View):
    def get(self, request, group_id, album_id):
        group = get_group(group_id, request.user)
        t_user = get_telegram_user_from_request(request)
        album = get_object_or_404(Album, id=album_id)
        if album.group != group:
            raise Http404
        albums = queries.get_other_albums(group_id, album_id)
        photos = album.photos.all()
        cover = queries.get_album_cover(album, photos)

        context = {
            "album": album,
            "albums": albums,
            "cover": cover,
            "photos": photos,
        }

        return render(request, "gallery/group/album.html", prepare_context(group, t_user, context))


class SetCoverView(LoginRequiredMixin, View):
    def post(self, request, album_id, photo_id):
        album = queries.get_album_with_id_if_user_is_allowed(request.user, album_id)
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)
        require_role(request.user, album.group, "admin")

        if album is None or photo is None or photo not in album.photos.all():
            messages.error(request, _('Something went wrong'))
            return HttpResponseRedirect(reverse('home:feed'))

        album.cover = photo
        album.save()
        return HttpResponseRedirect(reverse('groups:photo_album',
                                            kwargs={"group_id": album.group.id, "album_id": album.id}))


class DeletePhotoView(LoginRequiredMixin, View):
    def post(self, request, photo_id):
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)

        if photo is None:
            return JsonResponse({}, status=404)

        require_role(request.user, photo.group, "admin")

        photo.delete()
        return JsonResponse({'message': _('Photo deleted')})


def rotate_photo_right(photo):
    photo_path = os.path.join(settings.MEDIA_ROOT, "photo", photo.file.name)
    # -vf 'transpose=x' - parameters for x are
    # 0 = 90CounterCLockwise and Vertical Flip (default)
    # 1 = 90Clockwise, 2 = 90CounterClockwise,  3 = 90Clockwise and Vertical Flip
    os.system("ffmpeg -i {} -y -vf 'transpose=1' {}".format(photo_path, photo_path))
    thumbnail_path = os.path.join(settings.MEDIA_ROOT, "photo-thumbnail", photo.thumbnail.name)
    os.system("ffmpeg -i {} -y -vf 'transpose=1' {}".format(thumbnail_path, thumbnail_path))
    
    photo.version += 1
    photo.save()


def rotate_photo_left(photo):
    photo_path = os.path.join(settings.MEDIA_ROOT, "photo", photo.file.name)
    os.system("ffmpeg -i {} -y -vf 'transpose=2' {}".format(photo_path, photo_path))
    thumbnail_path = os.path.join(settings.MEDIA_ROOT, "photo-thumbnail", photo.thumbnail.name)
    os.system("ffmpeg -i {} -y -vf 'transpose=2' {}".format(thumbnail_path, thumbnail_path))
    
    photo.version += 1
    photo.save()


class RotatePhotoRightView(LoginRequiredMixin, View):
    def post(self, request, photo_id):
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)
        if photo is None:
            return JsonResponse({}, status=404)
        django_rq.enqueue(rotate_photo_right, photo)
        return JsonResponse({'message': _('Photo rotated')})


class RotatePhotoLeftView(LoginRequiredMixin, View):
    def post(self, request, photo_id):
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)
        if photo is None:
            return JsonResponse({}, status=404)
        django_rq.enqueue(rotate_photo_left, photo)
        return JsonResponse({'message': _('Photo rotated')})


class PhotoDetailView(LoginRequiredMixin, View):
    def get(self, request, group_id, photo_id):
        group = get_group(group_id, request.user)
        t_user = get_telegram_user_from_request(request)
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)

        if photo is None:
            raise Http404()

        context = {
            "photo": photo,
        }

        return render(request, "gallery/group/photo.html", prepare_context(group, t_user, context))


class AlbumPhotoDetailView(LoginRequiredMixin, View):
    def get(self, request, group_id, album_id, photo_id):
        group = get_group(group_id, request.user)
        t_user = get_telegram_user_from_request(request)
        album = queries.get_album_with_id_if_user_is_allowed(request.user, album_id)
        photo = queries.get_photo_with_id_if_user_is_allowed(request.user, photo_id)

        if album is None or photo is None or photo not in album.photos.all():
            raise Http404()

        photos = album.photos.all()
        cover = queries.get_album_cover(album, photos)
        photos = list(photos)

        position = photos.index(photo)

        prev = photos[position - 1] if position > 0 else None
        next = photos[position + 1] if position + 1 < len(photos) else None

        context = {
            "photo": photo,
            "album": album,
            "cover": cover,
            "photos": photos,
            "prev": prev,
            "next": next,
        }

        return render(request, "gallery/group/album_photo.html", prepare_context(group, t_user, context))
