from home.models import Photo, Audio, Video, Link, File, Sticker
from django.conf import settings
from os import listdir, remove
from os.path import isfile, isdir, join


def get_media_files_except(media_type, filenames):
    path = join(settings.MEDIA_ROOT, media_type)
    if not isdir(path):
        return []
    for file in listdir(path):
        if isfile(join(path, file)) and file not in filenames:
            yield file


def delete_files(media_type, filenames):
    for file in filenames:
        remove(join(settings.MEDIA_ROOT, media_type, file))


def cleanup_media():
    photos = Photo.objects.all()
    photo_files = set([str(photo.file) for photo in photos])
    thumbnail_files = set([str(photo.thumbnail) for photo in photos])
    delete_files("photo", get_media_files_except("photo", photo_files))
    delete_files("photo-thumbnail", get_media_files_except("photo-thumbnail", thumbnail_files))
    
    audio_files = set([str(audio.file) for audio in Audio.objects.all()])
    delete_files("audio", get_media_files_except("audio", audio_files))
    
    videos = Video.objects.all()
    video_files = set([str(video.file) for video in videos])
    thumbnail_files = set([str(video.thumbnail) for video in videos])
    delete_files("video", get_media_files_except("video", video_files))
    delete_files("video-thumbnail", get_media_files_except("video-thumbnail", thumbnail_files))
    
    link_files = set([str(link.file) for link in Link.objects.all()])
    delete_files("link-preview", get_media_files_except("link-preview", link_files))
    
    file_files = set([str(file.other_file) for file in File.objects.all()])
    delete_files("file", get_media_files_except("file", file_files))
    
    stickers = Sticker.objects.all()
    sticker_files = set([str(s.file) for s in stickers]) | set([str(s.file).split('.')[0] + ".png" for s in stickers])
    delete_files("sticker", get_media_files_except("sticker", sticker_files))
