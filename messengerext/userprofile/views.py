from django.shortcuts import render, get_object_or_404
from accounts.views import LoginRequiredMixin
from django.views.generic import View
from home.models import Group, Photo, Link, Audio, Video
from events.models import Attending, Event
from django.contrib.auth.models import User
from django.http import Http404
from operator import attrgetter
from itertools import chain
import datetime


class UserprofileView(LoginRequiredMixin, View):
    def _get_feed_for_user(self, groups, user):
        photos = Photo.objects.filter(group__in=groups).filter(user=user)
        links = Link.objects.filter(group__in=groups).filter(user=user)
        audio = Audio.objects.filter(group__in=groups).filter(user=user)
        video = Video.objects.filter(group__in=groups).filter(user=user)

        feed = sorted(chain(photos, links, audio, video), key=attrgetter('timestamp'), reverse=True)
        return feed

    def _get_common_groups(self, user, requestuser):
        return Group.objects.filter(users=requestuser).filter(users=user)

    def _get_user(self, user_id):
        return get_object_or_404(User, id=user_id)

    def _get_upcoming_events_for_groups(self, groups):
        return Event.objects.filter(group__in=groups, start__gt=datetime.datetime.now()).order_by('start')

    def _get_maybe_and_attending_events(self, events, user):
        return events.exclude(attending__user=user, attending__status="no")

    def get(self, request, user_id):
        user = self._get_user(user_id)
        common_groups = self._get_common_groups(user, request.user)
        if not common_groups:
            raise Http404()

        feed = self._get_feed_for_user(common_groups, user)

        events = self._get_upcoming_events_for_groups(common_groups)
        common_upcoming_events = self._get_maybe_and_attending_events(events, user)

        context = {
            'feed_list': feed,
            'user_groups': common_groups,
            'user': user,
            'upcoming_events': common_upcoming_events
        }
        if request.is_ajax():
            return render(request, "home/feed.html", context)

        return render(request, 'userprofile/userprofile.html', context)
