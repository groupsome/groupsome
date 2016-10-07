from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^(?P<group_id>[0-9]+)/(?P<album_id>[0-9]+)/add/(?P<photo_id>[0-9]+)$', views.AddPhotoView.as_view(),
        name='album_add_photo'),
    url(r'^(?P<group_id>[0-9]+)/(?P<album_id>[0-9]+)/delete_from_album/(?P<photo_id>[0-9]+)$',
        views.DeletePhotoFromAlbumView.as_view(), name='album_delete_photo'),
    url(r'^(?P<album_id>[0-9]+)/(?P<photo_id>[0-9]+)/cover/?$',
        views.SetCoverView.as_view(), name='album_set_cover'),
    url(r'^photos/(?P<photo_id>[0-9]+)/delete/?$', views.DeletePhotoView.as_view(), name='photo_delete'),
    url(r'^photos/(?P<photo_id>[0-9]+)/rotate/right/?$', views.RotatePhotoRightView.as_view(),
        name='photo_rotate_right'),
    url(r'^photos/(?P<photo_id>[0-9]+)/rotate/left/?$', views.RotatePhotoLeftView.as_view(), name='photo_rotate_left'),
]
