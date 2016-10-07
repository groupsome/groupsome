from django.conf.urls import url, include
from django.views.generic import RedirectView
from serve_media.views import PhotoView, PhotoThumbnailView, StickerView, FileView, AudioView, VideoView, \
    VideoThumbnailView, AvatarView, LinkPreviewView, GroupHeaderView, GroupChatPhotoView

urlpatterns = [
    url(r'^photo/(?P<photo_id>[0-9]+)/?$', PhotoView.as_view(), name='photo'),
    url(r'^photo/thumbnail/(?P<photo_id>[0-9]+)/?$', PhotoThumbnailView.as_view(), name='photo_thumbnail'),
    url(r'^sticker/(?P<sticker_id>[0-9]+)/?$', StickerView.as_view(), name='sticker'),
    url(r'^file/(?P<file_id>[0-9]+)/?$', FileView.as_view(), name='file'),
    url(r'^audio/(?P<audio_id>[0-9]+)/?$', AudioView.as_view(), name='audio'),
    url(r'^video/(?P<video_id>[0-9]+)/?$', VideoView.as_view(), name='video'),
    url(r'^video/thumbnail/(?P<video_id>[0-9]+)/?$', VideoThumbnailView.as_view(), name='video_thumbnail'),
    url(r'^avatar/(?P<user_id>[0-9]+)/?$', AvatarView.as_view(), name='avatar'),
    url(r'^link/preview/(?P<link_id>[0-9]+)/?$', LinkPreviewView.as_view(), name='link_preview'),
    url(r'^group/header/(?P<group_id>[0-9]+)/?$', GroupHeaderView.as_view(), name='group_header'),
    url(r'^chat_photo/(?P<group_id>[0-9]+)/?$', GroupChatPhotoView.as_view(), name='group_chat_photo'),
]
