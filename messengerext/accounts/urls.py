from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import logout

from . import views

urlpatterns = [
    url(r'^login(/(?P<token_string>[a-zA-Z0-9]+)|/)?$', views.LoginView.as_view(), name='login'),
    url(r'^logout/?$', logout, name='logout'),
    url(r'^token/(?P<token>[a-zA-Z0-9]+)/?$', csrf_exempt(views.TokenView.as_view()), name='token'),
    url(r'^settings/?$', views.SettingsView.as_view(), name='settings'),
    url(r'^settings/update_avatar/?$', views.SettingsUpdateAvatarView.as_view(), name='settings_update_avatar'),
    url(r'^settings/update_timezone/?$', views.SettingsUpdateTimeZoneView.as_view(), name='settings_update_timezone'),
    url(r'^legal/?$', views.LegalView.as_view(), name='legal'),
]
