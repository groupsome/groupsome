from django.test import TestCase, RequestFactory
from django.core.urlresolvers import resolve, reverse
from django.test.client import Client
from django.contrib.auth.models import User
from events.models import Event
from groups.tests import create_user, create_group
from bot import models
import datetime
import dateparser
import pytz
import mock
import telepot


def send_message(arg1, arg2, arg3, **kwargs):
    pass


class TestAEventsView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_not_authenticated_user_is_redirected_to_login(self):
        response = self.client.get(reverse('events:events'), follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_events_mapping_works(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('events:events'))
        self.assertEquals(response.status_code, 200)

    def test_events_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('events:events'))
        self.assertTemplateUsed(response=response, template_name='events/events.html')


class TestCreateEventView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.user.timezone_offset = 0

    def test_not_authenticated_user_is_redirected_to_login(self):
        response = self.client.get(reverse('events:events'), follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_create_event_mapping_works(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('events:create_event'))
        self.assertEquals(response.status_code, 200)

    def test_create_event_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('events:create_event'))
        self.assertTemplateUsed(response=response, template_name='events/create_event.html')

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_create_event(self):
        self.client.force_login(user=self.user)

        timestamp = dateparser.parse("in 3 hours").replace(tzinfo=pytz.utc)
        time = ("{0:%H}:{0:%M}").format(timestamp)
        date = ("{0:%d}.{0:%m}.{0:%Y}").format(timestamp)

        response = self.client.post(
            reverse('events:create_event'),
            {'occasion': 'Testen', 'group': 'Test', 'location': 'Hier',
             'date': date, 'time': time, },
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

        event = Event.objects.get(group=self.group)

        self.assertEqual(event.allday, False)
        self.assertEqual(event.name, 'Testen')
        self.assertEqual(event.location, 'Hier')
        self.assertEqual(event.start.__format__('%d.%m.%Y %H:%M'), timestamp.__format__('%d.%m.%Y %H:%M'))

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_create_event_allday(self):
        self.client.force_login(user=self.user)

        timestamp = dateparser.parse("in 3 hours").replace(tzinfo=pytz.utc)
        time = ("{0:%H}:{0:%M}").format(timestamp)
        date = ("{0:%d}.{0:%m}.{0:%Y}").format(timestamp)
        time_assert = dateparser.parse(date + " at " + "00:00:00", date_formats=['%d.%m.%y at %H:%M'],
                                       settings={'DATE_ORDER': 'DMY'}).replace(tzinfo=pytz.utc)

        response = self.client.post(
            reverse('events:create_event'),
            {'occasion': 'Testen', 'group': 'Test', 'location': 'Hier',
             'date': date, 'time': time, 'allday': True},
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

        event = Event.objects.get(group=self.group)

        self.assertEqual(event.allday, True)
        self.assertEqual(event.name, 'Testen')
        self.assertEqual(event.location, 'Hier')
        self.assertEqual(event.start.__format__('%d.%m.%Y'), timestamp.__format__('%d.%m.%Y'))
        self.assertEqual(event.start.__format__('%H:%M'), time_assert.__format__('%H:%M'))

    def test_create_event_empty_name_failure(self):
        self.client.force_login(user=self.user)

        timestamp = dateparser.parse("in 3 hours").replace(tzinfo=pytz.utc)
        time = ("{0:%H}:{0:%M}").format(timestamp)
        date = ("{0:%d}.{0:%m}.{0:%Y}").format(timestamp)

        response = self.client.post(
            reverse('events:create_event'),
            {'occasion': '', 'group': 'Test', 'location': 'Hier',
             'date': date, 'time': time},
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Event Name can`t be empty!')

    def test_create_event_wrong_group_failure(self):
        self.client.force_login(user=self.user)

        timestamp = dateparser.parse("in 3 hours").replace(tzinfo=pytz.utc)
        time = ("{0:%H}:{0:%M}").format(timestamp)
        date = ("{0:%d}.{0:%m}.{0:%Y}").format(timestamp)

        response = self.client.post(
            reverse('events:create_event'),
            {'occasion': '', 'group': 'NotAGroup', 'location': 'Hier',
             'date': date, 'time': time},
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'No group found!')

    def test_create_event_bad_timestamp_failure(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            reverse('events:create_event'),
            {'occasion': '', 'group': 'NotAGroup', 'location': 'Hier',
             'date': 'not a', 'time': 'real time'},
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Error while parsing the date/time!')


class TestEditEventView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.user.timezone_offset = 0

        new_event = Event(group=self.group, start=datetime.datetime.now().replace(tzinfo=pytz.utc),
                          allday=False, name='TestEvent', location='', id=0)
        new_event.save()

    def test_not_authenticated_user_is_redirected_to_login(self):
        response = self.client.get('/events/0/edit_event', follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_edit_event_mapping_works(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/events/0/edit_event')
        self.assertEquals(response.status_code, 200)

    def test_edit_event_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/events/0/edit_event')
        self.assertTemplateUsed(response=response, template_name='events/edit_event.html')

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_edit_event(self):
        self.client.force_login(user=self.user)

        timestamp = dateparser.parse("in 3 hours").replace(tzinfo=pytz.utc)
        time = ("{0:%H}:{0:%M}").format(timestamp)
        date = ("{0:%d}.{0:%m}.{0:%Y}").format(timestamp)

        response = self.client.post(
            '/events/0/edit_event',
            {'occasion': 'Testen', 'group': 'Test', 'location': 'Hier',
             'date': date, 'time': time, },
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

        event = Event.objects.get(group=self.group)

        self.assertEqual(event.allday, False)
        self.assertEqual(event.name, 'Testen')
        self.assertEqual(event.location, 'Hier')
        self.assertEqual(event.start.__format__('%d.%m.%Y %H:%M'), timestamp.__format__('%d.%m.%Y %H:%M'))

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_edit_event_allday(self):
        self.client.force_login(user=self.user)

        timestamp = dateparser.parse("in 3 hours").replace(tzinfo=pytz.utc)
        time = ("{0:%H}:{0:%M}").format(timestamp)
        date = ("{0:%d}.{0:%m}.{0:%Y}").format(timestamp)
        time_assert = dateparser.parse(date + " at " + "00:00:00", date_formats=['%d.%m.%y at %H:%M'],
                                       settings={'DATE_ORDER': 'DMY'}).replace(tzinfo=pytz.utc)

        response = self.client.post(
            '/events/0/edit_event',
            {'occasion': 'Testen', 'group': 'Test', 'location': 'Hier',
             'date': date, 'time': time, 'allday': True, },
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

        event = Event.objects.get(group=self.group)

        self.assertEqual(event.allday, True)
        self.assertEqual(event.name, 'Testen')
        self.assertEqual(event.location, 'Hier')
        self.assertEqual(event.start.__format__('%d.%m.%Y'), timestamp.__format__('%d.%m.%Y'))
        self.assertEqual(event.start.__format__('%H:%M'), time_assert.__format__('%H:%M'))

    def test_edit_event_empty_name_failure(self):
        self.client.force_login(user=self.user)

        timestamp = dateparser.parse("in 3 hours").replace(tzinfo=pytz.utc)
        time = ("{0:%H}:{0:%M}").format(timestamp)
        date = ("{0:%d}.{0:%m}.{0:%Y}").format(timestamp)

        response = self.client.post(
            '/events/0/edit_event',
            {'occasion': '', 'group': 'Test', 'location': 'Hier',
             'date': date, 'time': time},
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Event Name can`t be empty!')

    def test_edit_event_bad_timestamp_failure(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            '/events/0/edit_event',
            {'occasion': 'Testen', 'group': 'Test', 'location': 'Hier',
             'date': 'not a', 'time': 'real time'},
            follow=True)

        self.assertRedirects(response, reverse('events:events'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Error while parsing the date/time!')
