from home import models
from django.core.exceptions import ObjectDoesNotExist
from operator import attrgetter
from itertools import chain
from gallery.models import Album


ADD_PICTURE_SYMBOL = '/static/img/add-pictures.jpg'


# returns the album with the id album_id if user is a member of the corresponding group
def get_album_with_id_if_user_is_allowed(user, album_id):
    user_groups = get_user_groups(user)
    try:
        album = Album.objects.filter(group__in=user_groups).get(id=album_id)
        return album
    except ObjectDoesNotExist:
        return None


# returns the photo with the id photo_id if user is a member of the corresponding group
def get_photo_with_id_if_user_is_allowed(user, photo_id):
    user_groups = get_user_groups(user)
    try:
        photo = models.Photo.objects.filter(group__in=user_groups).get(id=photo_id)
        return photo
    except ObjectDoesNotExist:
        return None


# returns the number of photos and one photo as a cover for a group
def get_group_photo_count_and_cover(group):
    count_images = models.Photo.objects.filter(group=group).count()
    if count_images > 0:
        cover = models.Photo.objects.filter(group=group).first().media_url
        return count_images, cover
    else:
        return 0, ADD_PICTURE_SYMBOL


def get_albums(user):
    user_groups = get_user_groups(user)
    return Album.objects.filter(group__in=user_groups)


# returns all albums except the given album
def get_other_albums(user, album_id):
    all_albums = get_albums(user)
    return all_albums.exclude(id=album_id)


# returns a list of the users albums and groups including an album cover for each element
def get_user_albums_and_covers(user):
    user_groups = get_user_groups(user)
    albums = Album.objects.filter(group__in=user_groups)
    album_list = list()
    for group in user_groups:
        (count_images, photo_file) = get_group_photo_count_and_cover(group)
        album_list.append({'name': group.name,
                           'type': 'group',
                           'id': group.id,
                           'description': 'photos of ' + group.name,
                           'photo_file': photo_file,
                           'photo_count': count_images,
                           })
    album_list = album_list + get_albums_with_covers(albums)
    return album_list


def get_albums_with_covers(albums):
    album_list = list()
    for album in albums:
        count_images = album.photos.count()
        photo_file = None
        if album.cover is not None:
            photo_file = album.cover.media_url
        elif count_images == 0:
            photo_file = ADD_PICTURE_SYMBOL
        else:
            photo_file = album.photos.first().media_url
        album_list.append({'name': album.name,
                           'type': 'album',
                           'id': album.id,
                           'description': album.description,
                           'photo_file': photo_file,
                           'photo_count': count_images,
                           })
    return album_list


def get_album_cover(album, photos):
    count_images = photos.count()
    if album.cover is not None:
        return album.cover.media_url
    elif count_images == 0:
        return ADD_PICTURE_SYMBOL

    return photos.first().media_url


# returns the groups the user is in
def get_user_groups(user):
    return models.Group.objects.filter(users=user)


# returns the group object for a group_id, if the user is in that group
def get_specific_group(user, group_id):
    group = models.Group.objects.filter(users=user, id=group_id)
    if len(group) > 0:
        return group.first()
    else:
        return None


# check if user is in this group before calling this method
def get_media_content(group):
    photos = models.Photo.objects.filter(group=group)
    videos = models.Video.objects.filter(group=group)
    feed = sorted(chain(photos, videos), key=attrgetter('timestamp'), reverse=True)
    return feed


# returns true if photo was deleted from album
def delete_photo_from_album_if_user_is_allowed(user, album_id, photo_id):
    user_groups = get_user_groups(user)
    try:
        album = Album.objects.filter(group__in=user_groups).get(id=album_id)
        photo = models.Photo.objects.filter(group__in=user_groups).get(id=photo_id)
        album.photos.remove(photo)
        return True
    except:
        return False
