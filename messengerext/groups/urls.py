from django.conf.urls import url, include
from . import views
from gallery import views as gallery_views
from files import views as files_views

urlpatterns = [
    url(r'^$', views.GroupListView.as_view(), name='list'),
    url(r'^(?P<group_id>[0-9]+)/?$', views.GroupFeedView.as_view(), name='feed'),
    url(r'^(?P<group_id>[0-9]+)/settings/?$', views.GroupSettingsView.as_view(), name='settings'),
    # url(r'^(?P<group_id>[0-9]+)/settings/sync_admins?$', views.GroupSettingsSyncAdminsView.as_view(),
    #    name='settings_sync_admins'),

    url(r'^(?P<group_id>[0-9]+)/photos/?$', gallery_views.GroupView.as_view(), name='photo_overview'),
    url(r'^(?P<group_id>[0-9]+)/photos/(?P<photo_id>[0-9]+)/?$', gallery_views.PhotoDetailView.as_view(),
        name='photo_detail'),
    url(r'^(?P<group_id>[0-9]+)/photos/albums/(?P<album_id>[0-9]+)/?$', gallery_views.GroupAlbumDetailView.as_view(),
        name='photo_album'),
    url(r'^(?P<group_id>[0-9]+)/photos/albums/(?P<album_id>[0-9]+)/(?P<photo_id>[0-9]+)/?$',
        gallery_views.AlbumPhotoDetailView.as_view(),
        name='photo_album_photo_detail'),
    
    url(r'^(?P<group_id>[0-9]+)/files/?$', files_views.DirectoryView.as_view(), name='file_overview'),
    url(r'^(?P<group_id>[0-9]+)/files/(?P<file_id>[0-9]+)/move/?$', files_views.MoveFileView.as_view(),
        name='file_move'),
    url(r'^(?P<group_id>[0-9]+)/files/(?P<file_id>[0-9]+)/delete/?$', files_views.DeleteFileView.as_view(),
        name='file_delete'),
    
    url(r'^(?P<group_id>[0-9]+)/files/directories/create/?$', files_views.CreateDirectoryView.as_view(),
        name='file_directory_create'),
    url(r'^(?P<group_id>[0-9]+)/files/directories/(?P<directory_id>[0-9]+)/?$', files_views.DirectoryView.as_view(),
        name='file_directory'),
    url(r'^(?P<group_id>[0-9]+)/files/directories/(?P<directory_id>[0-9]+)/move/?$',
        files_views.MoveDirectoryView.as_view(), name='file_directory_move'),
    url(r'^(?P<group_id>[0-9]+)/files/directories/(?P<directory_id>[0-9]+)/delete/?$',
        files_views.DeleteDirectoryView.as_view(), name='file_directory_delete'),

    url(r'^(?P<group_id>[0-9]+)/links/?$', views.GroupLinksView.as_view(), name='links'),
    url(r'^(?P<group_id>[0-9]+)/links/(?P<link_id>[0-9]+)/delete/?$', views.DeleteLinkView.as_view(),
        name='link_delete'),
    url(r'^(?P<group_id>[0-9]+)/audios/?$', views.GroupAudiosView.as_view(), name='audios'),
    url(r'^(?P<group_id>[0-9]+)/audios/(?P<audio_id>[0-9]+)/delete/?$', views.DeleteAudioView.as_view(),
        name='audio_delete'),
    url(r'^(?P<group_id>[0-9]+)/videos(/[0-9]+)?/?$', views.GroupVideosView.as_view(), name='videos'),
    url(r'^(?P<group_id>[0-9]+)/videos/(?P<video_id>[0-9]+)/delete/?$', views.DeleteVideoView.as_view(),
        name='video_delete'),
]
