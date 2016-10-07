from django.views.generic import View
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.core.exceptions import PermissionDenied
from accounts.views import LoginRequiredMixin
from home.models import Text, Photo, Audio, Video, File, Sticker, Link
from operator import attrgetter
from itertools import chain


def get_content_or_404(content_type, content_id):
    models = {
        "text": Text,
        "photo": Photo,
        "audio": Audio,
        "video": Video,
        "file": File,
        "sticker": Sticker,
        "link": Link,
    }
    
    if content_type not in models:
        raise Http404
    
    content = get_object_or_404(models[content_type], id=content_id)
    
    if content.type == "link":
        content = get_object_or_404(Text, telegram_id=content.telegram_id)
    
    return content


def is_content_accessible(content, user):
    return content.group in user.memberships.all()


def get_content_older_than(group, timestamp, limit=10):
    query = {"group": group, "timestamp__lte": timestamp}
    feed = sorted(chain(Text.objects.filter(**query), Photo.objects.filter(**query),
                  Audio.objects.filter(**query), Video.objects.filter(**query),
                  File.objects.filter(**query), Sticker.objects.filter(**query)),
                  key=attrgetter("timestamp"), reverse=True)
    return feed[:limit+1]


def get_content_newer_than(group, timestamp, limit=10):
    query = {"group": group, "timestamp__gte": timestamp}
    feed = sorted(chain(Text.objects.filter(**query), Photo.objects.filter(**query),
                  Audio.objects.filter(**query), Video.objects.filter(**query),
                  File.objects.filter(**query), Sticker.objects.filter(**query)),
                  key=attrgetter("timestamp"))
    return feed[:limit+1]


class ChatlogView(LoginRequiredMixin, View):
    def get(self, request, content_type, content_id):
        content = get_content_or_404(content_type, content_id)
        if not is_content_accessible(content, request.user):
            raise PermissionDenied
        
        older = get_content_older_than(content.group, content.timestamp)
        newer = get_content_newer_than(content.group, content.timestamp)
        feed = sorted(set(chain(older, [content], newer)), key=attrgetter("timestamp"))
        
        return render(request, "chatlog/chatlog.html", {
            "content": content,
            "feed": feed,
        })


class ChatlogPagerView(LoginRequiredMixin, View):
    def get(self, request, content_type, content_id, direction):
        content = get_content_or_404(content_type, content_id)
        if not is_content_accessible(content, request.user):
            raise PermissionDenied
        
        if direction == "older":
            feed = get_content_older_than(content.group, content.timestamp)
        else:
            feed = get_content_newer_than(content.group, content.timestamp)
        feed = sorted(filter(lambda item: item != content, feed), key=attrgetter("timestamp"))
        
        return render(request, "chatlog/chatlog_items.html", {
            "content": content,
            "feed": feed,
        })
