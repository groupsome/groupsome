from bot.commands import Command, StatefulCommand
from django.utils.translation import ugettext as _
from django.conf import settings
from events.models import Event, Attending
import telepot
import pytz
import datetime
import dateparser
import locale


def bot_sendMessage(telegram_id, message):
    bot = telepot.Bot(settings.TELEGRAM_TOKEN)
    bot.sendMessage(telegram_id, message)


def handle_event_callback(query_id, index, status, user, user_groups, bot):
    event = Event.objects.filter(id=index).filter(group__in=user_groups)
    if not event:
        return bot.answerCallbackQuery(query_id, _("Event not found."))
        
    attending = Attending.objects.filter(event__in=event).filter(user=user.user)
    if attending:
        attending[0].status = status
        attending[0].save()
    else:
        entry = Attending.create_and_save(user=user.user, status=status)
        entry.event.add(event[0])
        entry.save()

    if status == "yes":
        status = _("Yes")
    elif status == "maybe":
        status = _("Maybe")
    else:
        status = _("No")

    bot.answerCallbackQuery(query_id, _("You selected: ") + status)


class NewEventCommand(StatefulCommand, Command):
    required_role = "admin"
    key = "_state"

    def handle_initial_state(self):
        self.cache.set(str(self.user.telegram_id) + "_event", Event(group=self.group))
        self.set_state(0)
        self.handle_state(0)

    def handle_state(self, state):
        user = self.user
        text = self.text
        new_event = self.cache.get(str(user.telegram_id) + "_event")
        tz = pytz.timezone(user.timezone_setting)

        if state is None or new_event is None:
            self.reset_state()
            self.cache.delete(str(user.telegram_id) + "_event")
            return

        language = self.user.language
        if language == "de":
            language = "de_DE.utf8"
            locale.setlocale(locale.LC_TIME, language)

        if state == 0:
            self.reply(_("At which date and time do you want to plan an event?\n\n" + "You can type /cancel to cancel"),
                       reply_markup={'hide_keyboard': True}, private=True)
            self.set_state(1)
        elif state == 1:
            # since this looks confusing, explanation:
            # we interpret all user input as their local time (while the parse library defaults to UTC)
            # so for relative times we have to provide the current local time for the user as a BaseException
            # however this provided time must be naive otherwise the library would convert it back to utc time
            date = dateparser.parse(text, settings={'RELATIVE_BASE': datetime.datetime.now(tz).replace(tzinfo=None)})
            if date is None:
                self.reply(_("Could not understand the date and time\n\nYou can type /cancel to cancel"), private=True)
                return
            date = tz.localize(date)
            if date is None:
                self.reply(_("Could not understand the date and time\n\nYou can type /cancel to cancel"), private=True)
                return
            new_event.start = date.astimezone(pytz.utc)
            new_event.allday = False
            self.reply(_("Ok I will plan an event on {0:%A}, {0:%x} at {0:%H}:{0:%M}\nWhat's the occasion?\n\nYou can"
                         " type /cancel to cancel").format(new_event.start.astimezone(tz)), private=True)
            self.cache.set(str(user.telegram_id) + "_event", new_event)
            self.set_state(2)
        elif state == 2:
            if len(text) >= 100:
                self.reply(_("The event name is too long!\n\nYou can type /cancel to cancel"), private=True)
                return

            new_event.name = text
            self.reply(_("Ok I will plan event for {0} on {1:%A}, {1:%x} at {1:%H}:{1:%M}\nWhere will it be?\n\nYou "
                         "can type /cancel to cancel")
                       .format(new_event.name, new_event.start.astimezone(tz)), private=True)
            self.cache.set(str(user.telegram_id) + "_event", new_event)
            self.set_state(3)
        elif state == 3:
            if len(text) >= 100:
                self.reply(_("The event location is too long!\n\nYou can type /cancel to cancel"), private=True)
                return

            new_event.location = text

            reminder_time = new_event.start - datetime.timedelta(hours=1)

            if reminder_time > datetime.datetime.utcnow().replace(tzinfo=pytz.utc):
                reminder_job = self.message_handler.scheduler.enqueue_at(reminder_time, bot_sendMessage,
                                                                         new_event.group.telegram_id,
                                                                         _("{0} is in 1 hour at {1}").format(
                                                                             new_event.name, new_event.location))
                new_event.job_id = reminder_job.id

            new_event.save()
            self.reply(_("Ok I created an event for {0} at {1} on {2:%A}, {2:%x} at {2:%H}:{2:%M}")
                       .format(new_event.name, new_event.location, new_event.start.astimezone(tz)), private=True)

            inline_keyboard = {'inline_keyboard': [[{'text': _('yes'), 'callback_data': str(new_event.id) +
                                                     '-yes-event'},
                                                    {'text': _('maybe'), 'callback_data': str(new_event.id) +
                                                     '-maybe-event'},
                                                    {'text': _('no'), 'callback_data': str(new_event.id) +
                                                     '-no-event'}]]}
            self.bot.sendMessage(new_event.group.telegram_id,
                                 _("{0} created an event for {1} at {2} on {3:%A}, {3:%x} at {3:%H}:{3:%M}\n" +
                                   "Will you attend?").format(user.user.username, new_event.name, new_event.location,
                                                              new_event.start
                                                              .astimezone(tz)),
                                 reply_markup=inline_keyboard)
            self.reset_state()
            self.cache.delete(str(user.telegram_id) + "_event")


class ShowEventsCommand(Command):
    def handle(self):
        events = self.group.event_set.filter(start__gt=datetime.datetime.now()).order_by('start')
        message = ""
        position = 0

        language = self.user.language
        if language == "de":
            language = "de_DE.utf8"
            locale.setlocale(locale.LC_TIME, language)

        for event in events:
            message += (_("{0}: {1} at {2} on {3:%A} {3:%x} at {3:%H}:{3:%M}\n")
                        .format(event.pk, event.name, event.location,
                                event.start.astimezone(pytz.timezone(self.user.timezone_setting))))
            position += 1
        if len(events) == 0:
            message += _("No events in this group. Write /newevent to start an event.")
        else:
            message += _("Write /deleteevent <number> to delete an event.")
        self.reply(message)


class DeleteEventCommand(Command):
    required_role = "admin"

    def handle(self):
        try:
            index = int(self.args[0])
            event = Event.objects.filter(pk=index)
            attendings = Attending.objects.filter(event__in=event)
            self.message_handler.scheduler.cancel(event[0].job_id)
            for at in attendings:
                at.delete()
            event.delete()
        except BaseException as e:
            self.reply(_("Event not found, write /deleteevent <number> to delete an event."))
            return
        self.reply(_("Event {} has been deleted.").format(index))
