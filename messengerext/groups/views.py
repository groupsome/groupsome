import os
import datetime
import telepot
from django.shortcuts import render
from django.views.generic import View
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from home.models import Group, Link, Audio, Video
from gallery.models import Album
from events.models import Event
from home.views import get_feed_items
from accounts.views import LoginRequiredMixin
from .forms import GroupSettingsForm
from bot.bot import get_file_extension
import bot.bot
from itertools import chain
from operator import attrgetter
from events.views import set_timezone_for_events, get_telegram_user_from_request
from surveys.models import Survey, Choice, Vote


def get_group(group_id, user):
    group = get_object_or_404(Group, id=group_id)

    if group not in user.memberships.all():
        raise PermissionDenied

    return group


def prepare_context(group, user, context={}):
    context["group"] = group
    context["group_members"] = User.objects.filter(memberships=group)
    startdate = datetime.date.today()
    enddate = startdate + datetime.timedelta(days=13)
    events = Event.objects.filter(group=group, start__range=[startdate, enddate]).order_by('start')
    events = set_timezone_for_events(events, user)

    context["upcoming_events"] = events

    surveys = Survey.objects.filter(group=group, status='open')
    context["surveys_counter"] = len(surveys)
    surveys = surveys.order_by('id').reverse()
    context["surveys"] = surveys[:4]

    return context


def require_role(user, group, role):
    if not group.has_role(user, role):
        raise PermissionDenied()


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    context_object_name = "groups"
    template_name = "groups/list.html"

    def get_queryset(self):
        return Group.objects.filter(users=self.request.user)


class GroupFeedView(LoginRequiredMixin, View):
    def get(self, request, group_id):
        group = get_group(group_id, request.user)
        feed = get_feed_items([group])
        albums = Album.objects.filter(group=group)
        t_user = get_telegram_user_from_request(request)

        context = {
            "feed_list": feed,
            "inside_group": True,
            "albums": albums,
        }

        if request.is_ajax():
            return render(request, "home/feed.html", context)

        return render(request, "groups/feed.html", prepare_context(group, t_user, context))


class GroupSettingsView(LoginRequiredMixin, View):
    def get(self, request, group_id):
        group = get_group(group_id, request.user)
        require_role(request.user, group, "admin")
        t_user = get_telegram_user_from_request(request)

        form = GroupSettingsForm(group, group.has_role(request.user, "creator"), initial={
            "description": group.description,
            "admins": [u.id for u in group.admins.all()],
            "everyone_is_admin": group.everyone_is_admin,
        })
        context = {
            "form": form,
        }

        return render(request, "groups/settings.html", prepare_context(group, t_user, context))

    def post(self, request, group_id):
        group = get_group(group_id, request.user)
        require_role(request.user, group, "admin")
        t_user = get_telegram_user_from_request(request)
        
        form = GroupSettingsForm(group, group.has_role(request.user, "creator"), request.POST, request.FILES, initial={
            "description": group.description,
        })
        context = {
            "form": form,
        }

        if form.is_valid():
            group.description = form.cleaned_data["description"]

            if form.cleaned_data["header"]:
                if group.header:
                    path = os.path.join(settings.MEDIA_ROOT, "group-header", str(group.header))
                    if os.path.isfile(path):
                        os.remove(path)

                upload = form.cleaned_data["header"]
                filename = str(group.id) + get_file_extension(file_type=upload.content_type, media_type="group-header")
                filepath = os.path.join(settings.MEDIA_ROOT, "group-header", filename)
                default_storage.save(filepath, ContentFile(upload.read()))
                group.header = filename
                group.header_version += 1
            
            if group.has_role(request.user, "creator"):
                group.admins.set(User.objects.filter(id__in=form.cleaned_data["admins"]))
                group.everyone_is_admin = form.cleaned_data["everyone_is_admin"]
            
            group.save()

            messages.success(request, _("Settings saved!"))
            return HttpResponseRedirect(reverse("groups:settings", kwargs={"group_id": group_id}))

        return render(request, "groups/settings.html", prepare_context(group, t_user, context))


class GroupSettingsSyncAdminsView(LoginRequiredMixin, View):
    def post(self, request, group_id):
        group = get_group(group_id, request.user)
        require_role(request.user, group, "creator")

        b = telepot.Bot(settings.TELEGRAM_TOKEN)
        # das mocken geht schief wenn man get_group_creator_and_admins nicht absolut aufruft
        creator, admins = bot.bot.get_group_creator_and_admins(group, b)

        group.creator = creator
        group.admins.set(admins)
        group.save()

        messages.success(request, _("Admins synced!"))
        return HttpResponseRedirect(reverse("groups:settings", kwargs={"group_id": group_id}))


class GroupLinksView(LoginRequiredMixin, View):
    def get(self, request, group_id):
        group = get_group(group_id, request.user)
        t_user = get_telegram_user_from_request(request)
        links = sorted(chain(Link.objects.filter(group=group)), key=attrgetter('timestamp'), reverse=True)

        context = {
            "inside_group": True,
            "links": links,
        }

        return render(request, "groups/links.html", prepare_context(group, t_user, context))


class DeleteLinkView(LoginRequiredMixin, View):
    def post(self, request, group_id, link_id):
        group = get_group(group_id, request.user)
        link = get_object_or_404(Link, id=link_id)

        if link is None or link.group != group:
            return JsonResponse({}, status=404)

        link.delete()
        return JsonResponse({'message': _('Link deleted')})


class GroupAudiosView(LoginRequiredMixin, View):
    def get(self, request, group_id):
        group = get_group(group_id, request.user)
        t_user = get_telegram_user_from_request(request)
        audios = sorted(chain(Audio.objects.filter(group=group)), key=attrgetter('timestamp'), reverse=True)

        context = {
            "inside_group": True,
            "audios": audios,
        }

        return render(request, "groups/audios.html", prepare_context(group, t_user, context))


class DeleteAudioView(LoginRequiredMixin, View):
    def post(self, request, group_id, audio_id):
        group = get_group(group_id, request.user)
        audio = get_object_or_404(Audio, id=audio_id)

        if audio is None or audio.group != group:
            return JsonResponse({}, status=404)

        audio.delete()
        return JsonResponse({'message': _('Audio deleted')})


class GroupVideosView(LoginRequiredMixin, View):
    def get(self, request, group_id):
        group = get_group(group_id, request.user)
        t_user = get_telegram_user_from_request(request)
        videos = sorted(chain(Video.objects.filter(group=group)), key=attrgetter('timestamp'), reverse=True)

        context = {
            "inside_group": True,
            "videos": videos,
        }

        return render(request, "groups/videos.html", prepare_context(group, t_user, context))


class DeleteVideoView(LoginRequiredMixin, View):
    def post(self, request, group_id, video_id):
        group = get_group(group_id, request.user)
        video = get_object_or_404(Video, id=video_id)

        if video is None or video.group != group:
            return JsonResponse({}, status=404)

        video.delete()
        return JsonResponse({'message': _('Video deleted')})
