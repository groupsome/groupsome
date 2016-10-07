from django.shortcuts import render, redirect
from django.views.generic import View
from bot.models import TelegramUser
from . import models
from gallery.models import Album
from accounts.views import LoginRequiredMixin, AnnonymusRequiredMixin
from operator import attrgetter
from itertools import chain
from django.utils import translation
import datetime


def get_feed_items(groups):
    photos = models.Photo.objects.filter(group__in=groups)
    links = models.Link.objects.filter(group__in=groups)
    audio = models.Audio.objects.filter(group__in=groups)
    video = models.Video.objects.filter(group__in=groups)

    feed = sorted(chain(photos, links, audio, video), key=attrgetter('timestamp'), reverse=True)
    return feed


def get_feed_items_in_time_range(groups, timestamp_from):
    timestamp_from = timestamp_from + datetime.timedelta(seconds=1)
    photos = models.Photo.objects.filter(group__in=groups)\
        .filter(timestamp__range=(timestamp_from, datetime.datetime.now()))
    links = models.Link.objects.filter(group__in=groups)\
        .filter(timestamp__range=(timestamp_from, datetime.datetime.now()))
    audio = models.Audio.objects.filter(group__in=groups)\
        .filter(timestamp__range=(timestamp_from, datetime.datetime.now()))
    video = models.Video.objects.filter(group__in=groups)\
        .filter(timestamp__range=(timestamp_from, datetime.datetime.now()))

    feed = sorted(chain(photos, links, audio, video), key=attrgetter('timestamp'), reverse=True)
    return feed


class HomeView(LoginRequiredMixin, View):
    template = 'home/home.html'
    feed_template = 'home/feed.html'
    not_authenticated_redirect_url = 'pages:landing'

    def _get_media_content(self, groups):
        return get_feed_items(groups)

    def _get_media_content_in_time_range(self, groups, timestamp_from):
        return get_feed_items_in_time_range(groups, timestamp_from)

    def _get_user_groups(self, user):
        return models.Group.objects.filter(users=user)

    def _get_specific_groups(self, user, group_id):
        return models.Group.objects.filter(users=user, id__in=group_id)

    def _get_albums(self, user_groups):
        return Album.objects.filter(group__in=user_groups)

    def get(self, request):
        user_groups = self._get_user_groups(request.user)
        selected_group_ids = request.GET.getlist('group')
        newest_item_timestamp = request.GET.get('newest-item-timestamp', '')
        if newest_item_timestamp:
            newest_item_timestamp = datetime.datetime.strptime(newest_item_timestamp, '%Y-%m-%d-%H:%M:%S')
        feed = []

        t_user = TelegramUser.objects.filter(user=request.user)[0]
        t_user.language = translation.get_language()
        t_user.save()

        # if request is ajax, only render content, not the whole page
        if self.request.is_ajax():
            self.template = self.feed_template
            if selected_group_ids:
                selected_groups = self._get_specific_groups(request.user, selected_group_ids)
                if selected_groups:
                    if newest_item_timestamp:
                        feed = self._get_media_content_in_time_range(selected_groups, newest_item_timestamp)
                    else:
                        feed = self._get_media_content(selected_groups)
                else:
                    redirect('home:home')
            else:
                if newest_item_timestamp:
                    feed = self._get_media_content_in_time_range(user_groups, newest_item_timestamp)
                else:
                    feed = self._get_media_content(user_groups)

        albums = self._get_albums(user_groups)
        context = {
            'user_groups': user_groups,
            'feed_list': feed,
            'albums': albums,
            'feed_template': self.feed_template
        }

        return render(request, self.template, context)
