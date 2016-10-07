from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^(?P<content_type>(text|photo|audio|video|file|sticker|link))/(?P<content_id>\d+)/?$',
        views.ChatlogView.as_view(), name='chatlog'),
    url(r'^(?P<content_type>(text|photo|audio|video|file|sticker|link))/(?P<content_id>\d+)/'
        r'(?P<direction>(older|newer))/?$',
        views.ChatlogPagerView.as_view(), name='chatlog_pager'),
]
