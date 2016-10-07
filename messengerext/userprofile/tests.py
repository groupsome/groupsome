from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.auth.models import User
from home.models import Group, Link
from bot.models import TelegramUser
from events.models import Event, Attending
import hashlib
import datetime


def create_user_with_name(username):
    user = User.objects.create_user(username, username+'@super.com', 'Password')
    user.save()
    telegram_id = int(hashlib.md5(user.username.encode("utf-8")).hexdigest()[:8], 16)
    TelegramUser.create_and_save(user=user, telegram_id=telegram_id)
    return user


class TestHomeView(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user1 = create_user_with_name('Superuser')
        self.user2 = create_user_with_name('Seconduser')
        self.user3 = create_user_with_name('Thirduser')  # this user has no groups
        self.group1 = Group.create_and_save(name="Gruppe", picture="", description="foo", telegram_id=11111111)
        self.group1.users.add(self.user1)
        self.group1.users.add(self.user2)
        self.group2 = Group.create_and_save(name="Gruppe2", picture="", description="foo", telegram_id=22222222)
        self.group2.users.add(self.user1)
        self.link1 = Link.create_and_save(user=self.user1, group=self.group1, timestamp="2016-05-25 12:59:10+01:00",
                                          url="www.1.com")
        self.link2 = Link.create_and_save(user=self.user2, group=self.group1, timestamp="2016-05-25 12:59:11+01:00",
                                          url="www.2.com")

    def test_userprofile_mapping_works_when_users_are_in_one_group_together(self):
        self.client.force_login(user=self.user1)
        response = self.client.get(reverse('userprofile:user', kwargs={'user_id': self.user2.id}), follow=True)
        self.assertTemplateUsed(response, 'userprofile/userprofile.html')

    def test_userprofile_is_not_shown_when_users_are_in_different_groups(self):
        self.client.force_login(user=self.user1)
        response = self.client.get(reverse('userprofile:user', kwargs={'user_id': self.user3.id}), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_view_returns_only_content_from_the_desired_user(self):
        self.client.force_login(user=self.user1)
        response = self.client.get(reverse('userprofile:user', kwargs={'user_id': self.user2.id}), follow=True)
        self.assertTrue(len(response.context['feed_list']) == 1)

    def test_view_returns_only_common_groups(self):
        self.client.force_login(user=self.user1)
        response = self.client.get(reverse('userprofile:user', kwargs={'user_id': self.user2.id}), follow=True)
        self.assertTrue(len(response.context['user_groups']) == 1)

    def test_ajax_request(self):
        self.client.force_login(user=self.user1)
        response = self.client.post(reverse('userprofile:user', kwargs={'user_id': self.user2.id}),
                                    {"page": "2", "querystring_key": "page"},
                                    **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertTemplateUsed('home/feed.html')

    def test_event_panel_shows_common_events(self):
        time = datetime.datetime.now() + datetime.timedelta(hours=3)
        event = Event.create_and_save(group=self.group1, start=time, allday=False, name="Olympia", location="Rio")
        attend = Attending.create_and_save(user=self.user2, status="yes")
        attend.event.add(event)
        time = datetime.datetime.now() + datetime.timedelta(hours=5)
        event = Event.create_and_save(group=self.group1, start=time, allday=False, name="EM", location="Paris")
        self.client.force_login(user=self.user1)
        response = self.client.get(reverse('userprofile:user', kwargs={'user_id': self.user2.id}), follow=True)
        self.assertTrue(len(response.context['upcoming_events']) == 2)

    def test_event_panel_excludes_events_user_is_not_participating(self):
        time = datetime.datetime.now() + datetime.timedelta(hours=3)
        event = Event.create_and_save(group=self.group1, start=time, allday=False, name="Olympia", location="Rio")
        attend = Attending.create_and_save(user=self.user2, status="no")
        attend.event.add(event)
        time = datetime.datetime.now() + datetime.timedelta(hours=5)
        event = Event.create_and_save(group=self.group1, start=time, allday=False, name="EM", location="Paris")
        self.client.force_login(user=self.user1)
        response = self.client.get(reverse('userprofile:user', kwargs={'user_id': self.user2.id}), follow=True)
        self.assertTrue(len(response.context['upcoming_events']) == 1)
