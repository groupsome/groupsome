from django.shortcuts import render, redirect
from accounts.views import LoginRequiredMixin
from django.views.generic import View
from home.models import Group
from . import models
from events.models import Attending
from django.http import Http404, HttpResponseRedirect, JsonResponse
from operator import attrgetter
from bot.bot import bot_sendMessage
from bot.models import TelegramUser
import json
from django.contrib import messages
import datetime
import pytz
import django_rq
import dateparser
import telepot
from events.models import Event
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.translation import ugettext as _
import locale


def set_timezone_for_events(events, user):
    for event in events:
        event.start = event.start + datetime.timedelta(minutes=user.timezone_offset)
    return events


def get_telegram_user_from_request(request):
    return TelegramUser.objects.filter(user=request.user)[0]


def get_attending_events(events, user):
    attending = models.Attending.objects.filter(user=user).filter(status='yes')
    return events.filter(attending__in=attending)


def get_not_attending_events(events, user):
    attending = models.Attending.objects.filter(user=user).filter(status='no')
    return events.filter(attending__in=attending)


class EventView(LoginRequiredMixin, View):

    def _get_events_for_groups(self, groups):
        return models.Event.objects.filter(group__in=groups)

    def _get_user_groups(self, user):
        return Group.objects.filter(users=user)

    def _get_only_upcoming_events(self, events):
        # TODO: Haendisch auf hour/minute fuer today abpruefen?
        return events.filter(start__gt=datetime.datetime.now()).order_by('start')

    def get(self, request):
        user_groups = self._get_user_groups(request.user)
        t_user = get_telegram_user_from_request(request)
        entries = self._get_events_for_groups(user_groups)
        # for colorcoding attendance for past events in calendar
        attending = get_attending_events(entries, request.user)
        notattending = get_not_attending_events(entries, request.user)

        json_list = []

        for entry in entries:
            id = entry.id
            title = entry.name
            start = (entry.start + datetime.timedelta(minutes=t_user.timezone_offset)).isoformat()
            allDay = entry.allday
            location = entry.location
            description = str(entry.group)
            if entry in attending:
                color = 'green'
            else:
                if entry in notattending:
                    color = 'red'
                else:
                    color = 'blue'

            json_entry = {'id': id, 'start': start, 'allDay': allDay, 'title': title, 'location': location,
                          'description': description, 'color': color}
            json_list.append(json_entry)

        events = json.dumps(json_list)
        entries = self._get_only_upcoming_events(entries)
        entries = set_timezone_for_events(entries, t_user)
        attending = get_attending_events(entries, request.user)
        notattending = get_not_attending_events(entries, request.user)
        context = {
            'attending': attending,
            'notattending': notattending,
            'events': events,
            'eventlist': entries,
            'user_groups': user_groups
        }
        return render(request, 'events/events.html', context)

    def post(self, request):
        return CreateEventView.post(self, request)


class DeleteEventView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        user_groups = Group.objects.filter(users=request.user)
        event = models.Event.objects.filter(id=event_id).filter(group__in=user_groups)
        attendings = models.Attending.objects.filter(event__in=event)
        if event:
            django_rq.get_scheduler('default').cancel(event[0].job_id)
            for at in attendings:
                at.delete()
            event.delete()
            return JsonResponse({'message': _('Successfully deleted Event')})
        else:
            return JsonResponse({'message': _('Something went wrong')})


class AttendEventView(LoginRequiredMixin, View):
    def get(self, request, event_id, status):
        possible_status = {'yes', 'maybe', 'no'}
        if status in possible_status:
            user_groups = Group.objects.filter(users=request.user)
            event = models.Event.objects.filter(id=event_id).filter(group__in=user_groups)
            if event:
                attending = models.Attending.objects.filter(event__in=event).filter(user=request.user)
                if attending:
                    attending[0].status = status
                    attending[0].save()
                else:
                    entry = Attending.create_and_save(user=request.user, status=status)
                    entry.event.add(event[0])
                    entry.save()

                attending = get_attending_events(event, request.user)
                notattending = get_not_attending_events(event, request.user)

                context = {
                    'attending': attending,
                    'notattending': notattending,
                    'event': event[0],
                }

                return render(request, "events/eventlist.html", context)
            else:
                return JsonResponse({'message': _('Something went wrong')})
        else:
            return JsonResponse({'message': _('Something went wrong')})


class CreateEventView(LoginRequiredMixin, View):
    def _get_group_from_name_and_user(self, group, user):
        return Group.objects.filter(users=user, name=group)

    def get(self, request):
        user_groups = Group.objects.filter(users=request.user)
        context = {
            'user_groups': user_groups
        }

        return render(request, 'events/create_event.html', context)

    def post(self, request):
        user = request.user
        occasion = request.POST.get('occasion')
        group_name = request.POST.get('group')
        location = request.POST.get('location')
        date = request.POST.get('date')
        time = request.POST.get('time')
        t_user = TelegramUser.objects.filter(user=user)[0]
        tz = pytz.timezone(t_user.timezone_setting)
        allday = request.POST.get('allday')

        language = t_user.language
        if language == "de":
            language = "de_DE.utf8"
            locale.setlocale(locale.LC_TIME, language)

        if allday is None:
            allday = False

        if allday:
            time = '00:00:00'

        try:
            timestamp = tz.localize(dateparser.parse(date + 'at' + time, settings={'DATE_ORDER': 'DMY'}))
        except AttributeError:
            messages.error(request, _('Error while parsing the date/time!'))
            return HttpResponseRedirect(reverse('events:events'))

        group = self._get_group_from_name_and_user(group_name, user)

        if len(group) > 0:
            group = group[0]
        else:
            messages.error(request, _('No group found!'))
            return HttpResponseRedirect(reverse('events:events'))

        if occasion.strip() == "":
            messages.error(request, _('Event Name can`t be empty!'))
            return HttpResponseRedirect(reverse('events:events'))

        new_event = Event(group=group, start=timestamp.astimezone(pytz.utc), name=occasion, location=location,
                          allday=allday)

        reminder_time = new_event.start - datetime.timedelta(hours=1)

        if reminder_time > datetime.datetime.utcnow().replace(tzinfo=pytz.utc):
            reminder_job = (django_rq.get_scheduler('default')
                            .enqueue_at(reminder_time, bot_sendMessage, new_event.group.telegram_id,
                                        _("{} is in 1 hour at {}").format(new_event.name, new_event.location)))
            new_event.job_id = reminder_job.id
        new_event.save()

        inline_keyboard = {'inline_keyboard': [[{'text': _('yes'), 'callback_data': str(new_event.id)+'-yes-event'},
                                                {'text': _('maybe'), 'callback_data': str(new_event.id)+'-maybe-event'},
                                                {'text': _('no'), 'callback_data': str(new_event.id)+'-no-event'}]]}
        bot = telepot.Bot(settings.TELEGRAM_TOKEN)
        if allday:
            bot.sendMessage(new_event.group.telegram_id,
                            _("{0} created an all-day event for {1} at {2} on {3:%A}, {3:%x}\n" +
                              "Will you attend?").format(user.username, new_event.name, new_event.location,
                                                         new_event.start.astimezone(tz)),
                            reply_markup=inline_keyboard)
        else:
            bot.sendMessage(new_event.group.telegram_id, _("{0} created an event for {1} at {2} on {3:%A}, {3:%x} at "
                                                           "{3:%H}:{3:%M}\n" + "Will you attend?")
                            .format(user.username, new_event.name, new_event.location, new_event.start.astimezone(tz)),
                            reply_markup=inline_keyboard)

        return HttpResponseRedirect(reverse('events:events'))


class EditEventView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        user_groups = Group.objects.filter(users=request.user)
        event = models.Event.objects.filter(id=event_id).filter(group__in=user_groups)
        if event:
            t_user = get_telegram_user_from_request(request)
            event = set_timezone_for_events(event, t_user)
            event = event[0]
        else:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('events:events'))

        context = {
            'event': event,
        }
        if request.is_ajax():
            return render(request, 'events/assets/edit_event_content.html', context)

        return render(request, 'events/edit_event.html', context)

    def post(self, request, event_id):
        user_groups = Group.objects.filter(users=request.user)
        event = models.Event.objects.filter(id=event_id).filter(group__in=user_groups)
        if event is None:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('events:events'))

        event = event[0]
        user = request.user
        occasion = request.POST.get('occasion')
        location = request.POST.get('location')
        date = request.POST.get('date')
        time = request.POST.get('time')
        allday = request.POST.get('allday')
        t_user = TelegramUser.objects.filter(user=user)[0]

        language = t_user.language
        if language == "de":
            language = "de_DE.utf8"
            locale.setlocale(locale.LC_TIME, language)

        if allday is None:
            allday = False

        if allday:
            time = '00:00:00'

        try:
            timestamp = dateparser.parse(date + " at " + time, date_formats=['%d.%m.%y at %H:%M'],
                                         settings={'DATE_ORDER': 'DMY'}).replace(tzinfo=pytz.utc)
        except AttributeError:
            messages.error(request, _('Error while parsing the date/time!'))
            return HttpResponseRedirect(reverse('events:events'))

        if occasion.strip() == "":
            messages.error(request, _('Event Name can`t be empty!'))
            return HttpResponseRedirect(reverse('events:events'))

        t_user = TelegramUser.objects.filter(user=user)[0]

        old_allday = event.allday
        old_name = event.name
        old_location = event.location
        old_start = event.start
        event.name = occasion
        event.start = timestamp - datetime.timedelta(minutes=t_user.timezone_offset)
        event.location = location
        event.allday = allday

        if old_start != event.start:
            django_rq.get_scheduler('default').cancel(event.job_id)
            reminder_time = event.start - datetime.timedelta(hours=1)
            if reminder_time > datetime.datetime.utcnow().replace(tzinfo=pytz.utc):
                reminder_job = (django_rq.get_scheduler('default')
                                .enqueue_at(reminder_time, bot_sendMessage, event.group.telegram_id,
                                            "{} is in 1 hour at {}".format(event.name, event.location)))
                event.job_id = reminder_job.id
        event.save()

        bot = telepot.Bot(settings.TELEGRAM_TOKEN)
        if allday and not old_allday:
            bot.sendMessage(event.group.telegram_id,
                            _("{0} changed event {1} at {2} on {3:%A}, {3:%x} at {3:%H}:{3:%M} to an all-day event {4} "
                              "at {5} on {6:%A}, {6:%x} \n")
                            .format(user.username, old_name, old_location,
                                    old_start + datetime.timedelta(minutes=t_user.timezone_offset), event.name,
                                    event.location, event.start + datetime.timedelta(minutes=t_user.timezone_offset)))
        elif not allday and old_allday:
            bot.sendMessage(event.group.telegram_id,
                            _("{0} changed all-day event {1} at {2} on {3:%A}, {3:%x} to {4} at {5} on {6:%A}, {6:%x} "
                              "at {6:%H}:{6:%M} \n")
                            .format(user.username, old_name, old_location,
                                    old_start + datetime.timedelta(minutes=t_user.timezone_offset), event.name,
                                    event.location, event.start + datetime.timedelta(minutes=t_user.timezone_offset)))
        elif allday and old_allday:
            bot.sendMessage(event.group.telegram_id,
                            _("{0} changed all-day event {1} at {2} on {3:%A}, {3:%x} to an all-day event {4} at {5} on"
                              " {6:%A}, {6:%x} \n")
                            .format(user.username, old_name, old_location,
                                    old_start + datetime.timedelta(minutes=t_user.timezone_offset), event.name,
                                    event.location, event.start + datetime.timedelta(minutes=t_user.timezone_offset)))
        else:
            bot.sendMessage(event.group.telegram_id, _("{0} changed event {1} at {2} on {3:%A}, {3:%x} at {3:%H}:{3:%M}"
                                                       " to {4} at {5} on {6:%A}, {6:%x} at {6:%H}:{6:%M} \n")
                            .format(user.username, old_name, old_location, old_start +
                                    datetime.timedelta(minutes=t_user.timezone_offset), event.name, event.location,
                                    event.start + datetime.timedelta(minutes=t_user.timezone_offset)))

        return HttpResponseRedirect(reverse('events:events'))
