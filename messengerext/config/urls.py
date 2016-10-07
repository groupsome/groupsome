"""gamelibrary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
import home

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/home')),
    url(r'^', include('pages.urls', namespace='pages')),
    url(r'^', include('accounts.urls', namespace='accounts')),
    url(r'^home/?', include('home.urls', namespace='home')),
    url(r'^bot/', include('bot.urls', namespace='bot')),
    url(r'^gallery/', include('gallery.urls', namespace='gallery')),
    url(r'^events/', include('events.urls', namespace='events')),
    url(r'^admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    url(r'^groupsomeadmin/', include(admin.site.urls)),
    url(r'^media/', include('serve_media.urls', namespace='media')),
    url(r'^groups/', include('groups.urls', namespace='groups')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^user/', include('userprofile.urls', namespace='userprofile')),
    url(r'^surveys/', include('surveys.urls', namespace='surveys')),
    url(r'^chatlog/', include('chatlog.urls', namespace='chatlog')),
]
