import datetime
import mock
import bot
import hashlib
from django.test import TestCase, RequestFactory
from django.core.urlresolvers import resolve, reverse
from django.http import HttpRequest
from django.test.client import Client
from django.contrib.auth.models import User
from home.models import Group, Photo, Link, Audio, Video
from events.models import Event
from gallery.models import Album
from bot.models import TelegramUser
import json


def create_user(username="Test", email="test@test.test"):
    user = User.objects.create_user(username, email, "test")
    user.save()
    
    telegram_id = int(hashlib.md5(username.encode("utf-8")).hexdigest()[:8], 16)
    
    TelegramUser.create_and_save(user=user, telegram_id=telegram_id)
    return user


def create_group(user=None, is_admin=False, users=None, admins=None, telegram_id=1, name="Test"):
    group = Group.create_and_save(name=name, picture="", description="foo", telegram_id=telegram_id,
                                  everyone_is_admin=False)

    if user is not None:
        group.users.add(user)
        
        if is_admin:
            group.admins.add(user)
            group.creator = user
            group.save()
    
    if users is not None:
        for u in users:
            group.users.add(u)
    
    if admins is not None:
        for a in admins:
            group.admins.add(a)

    return group


def create_photo(user, group):
    return Photo.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                 file="1.jpg", thumbnail="foo")


def create_event(group):
    return Event.create_and_save(group=group, start=datetime.datetime.now(),
                                 allday=False, name="Party", location="Paris")


def create_album(group, photo=None):
    album = Album.create_and_save(name="Test", description="Test", group=group)

    if photo is not None:
        album.photos.add(photo)

    return album


def create_link(user, group):
    return Link.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                url="https://www.google.de/")


def create_audio(user, group):
    return Audio.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                 file="1.mp3", duration_sec="300", title="Meteora", interpret="Linkin Park",
                                 telegram_id=2000)


def create_video(user, group):
    return Video.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00", file="1.mkv",
                                 duration_sec="300", width="1920", height="1080", thumbnail="1_thumb.jpg")


class TestGroupListView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)

    def test_list(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups", follow=True)
        self.assertTemplateUsed(response, "groups/list.html")
        self.assertIn(self.group, response.context["groups"])


class TestGroupFeedView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.photo = create_photo(self.user, self.group)
        self.event = create_event(self.group)
        self.album = create_album(self.group)

    def test_feed(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1")
        self.assertTemplateUsed(response, "groups/feed.html")
        self.assertEquals(response.context["group"], self.group)
        self.assertIn(self.user, response.context["group_members"])
        self.assertIn(self.photo, response.context["feed_list"])
        self.assertIn(self.event, response.context["upcoming_events"])
        self.assertIn(self.album, response.context["albums"])

    def test_feed_ajax(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertTemplateUsed(response, "home/feed.html")
        self.assertIn(self.photo, response.context["feed_list"])


class TestGroupLinksView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.link = create_link(self.user, self.group)

    def test_links(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/links")
        self.assertTemplateUsed(response, "groups/links.html")
        self.assertIn(self.link, response.context["links"])


class TestDeleteLinkView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.link = create_link(self.user, self.group)

    def test_delete_link(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/links/1/delete")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Link deleted")
        self.assertEquals(Link.objects.filter(pk=self.link.id).count(), 0)

    def test_delete_non_existing_link(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/links/2/delete")
        self.assertEquals(response.status_code, 404)


class TestGroupAudiosView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.audio = create_audio(self.user, self.group)

    def test_audios(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/audios")
        self.assertTemplateUsed(response, "groups/audios.html")
        self.assertIn(self.audio, response.context["audios"])


class TestDeleteAudioView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.audio = create_audio(self.user, self.group)

    def test_delete_audio(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/audios/1/delete")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Audio deleted")
        self.assertEquals(Audio.objects.filter(pk=self.audio.id).count(), 0)

    def test_delete_non_existing_audio(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/audios/2/delete")
        self.assertEquals(response.status_code, 404)


class TestGroupVideosView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.video = create_video(self.user, self.group)

    def test_videos(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/videos")
        self.assertTemplateUsed(response, "groups/videos.html")
        self.assertIn(self.video, response.context["videos"])


class TestDeleteVideoView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.video = create_video(self.user, self.group)

    def test_delete_video(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/videos/1/delete")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Video deleted")
        self.assertEquals(Video.objects.filter(pk=self.video.id).count(), 0)

    def test_delete_non_existing_video(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/videos/2/delete")
        self.assertEquals(response.status_code, 404)


class TestGroupSettingsView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.creator = create_user()
        self.member = create_user("Member", "member@test.test")
        self.admin = create_user("Admin", "admin@test.test")
        self.group = create_group(self.creator, is_admin=True, users=[self.member, self.admin], admins=[self.admin])

    def test_template_member(self):
        self.client.force_login(user=self.member)
        response = self.client.get("/groups/1/settings")
        self.assertEquals(response.status_code, 403)

    def test_template_admin(self):
        self.client.force_login(user=self.admin)
        response = self.client.get("/groups/1/settings")
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/settings.html")
    
    def test_description_update_member(self):
        self.client.force_login(user=self.member)
        response = self.client.post("/groups/1/settings", {"description": "Testdescription"}, follow=True)
        self.assertEquals(response.status_code, 403)
    
    def test_description_update_admin(self):
        self.client.force_login(user=self.admin)
        response = self.client.post("/groups/1/settings", {"description": "Testdescription"}, follow=True)
        self.assertRedirects(response, reverse('groups:settings', kwargs={"group_id": self.group.id}))
        self.group.refresh_from_db()
        self.assertEquals("Testdescription", self.group.description)
    
    @mock.patch("django.core.files.storage.default_storage.save")
    def test_upload_first_header(self, save):
        self.client.force_login(user=self.admin)
        with open("static/img/avatar/0.png", "rb") as file:
            response = self.client.post("/groups/1/settings", {"header": file}, follow=True)
            self.assertRedirects(response, reverse('groups:settings', kwargs={"group_id": self.group.id}))
            self.group.refresh_from_db()
            self.assertEquals(1, self.group.header_version)
            self.assertEquals("1.png", str(self.group.header))
            save.assert_called()
    
    @mock.patch("os.path.isfile")
    @mock.patch("os.remove")
    @mock.patch("django.core.files.storage.default_storage.save")
    def test_upload_new_header(self, save, remove, isfile):
        isfile.return_value = True
        self.group.header = "1.jpg"
        self.group.header_version = 1
        self.group.save()
        
        self.client.force_login(user=self.admin)
        with open("static/img/avatar/0.png", "rb") as file:
            response = self.client.post("/groups/1/settings", {"header": file}, follow=True)
            self.assertRedirects(response, reverse('groups:settings', kwargs={"group_id": self.group.id}))
            self.group.refresh_from_db()
            self.assertEquals(2, self.group.header_version)
            self.assertEquals("1.png", str(self.group.header))
            save.assert_called()
            remove.assert_called()
    
    def test_admins_update(self):
        self.client.force_login(user=self.creator)
        response = self.client.post("/groups/1/settings", {"admins": [self.admin.id]}, follow=True)
        self.assertRedirects(response, reverse('groups:settings', kwargs={"group_id": self.group.id}))
        self.group.refresh_from_db()
        self.assertIn(self.admin, self.group.admins.all())
    
    def test_everyoneIsAdmin_update(self):
        self.client.force_login(user=self.creator)
        response = self.client.post("/groups/1/settings", {"everyone_is_admin": "on"}, follow=True)
        self.assertRedirects(response, reverse('groups:settings', kwargs={"group_id": self.group.id}))
        self.group.refresh_from_db()
        self.assertTrue(self.group.everyone_is_admin)


'''class TestGroupSettingsSyncAdminsView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user, name="self")
        
        self.other_admin = create_user("Test2", "test2@test.test")
        self.other_group = create_group(self.user, telegram_id=2, name="other")
        self.other_group.creator = self.other_admin
        self.other_group.admins.add(self.other_admin)
        self.other_group.save()
    
    def test_sync_admins(self):
        # print("start test 1")
        def side_effect(group, bot):
            # print("called side effect 1")
            if group.id == 1:
                return (self.user, [self.user])
            elif group.id == 2:
                return (self.other_admin, [self.other_admin])
        
        patch = mock.patch("bot.bot.get_group_creator_and_admins", new=mock.MagicMock(side_effect=side_effect))
        get_group_creator_and_admins = patch.start()

        self.client.force_login(user=self.user)
        response = self.client.post("/groups/%d/settings/sync_admins" % self.group.id, follow=True)
        self.assertRedirects(response, reverse('groups:settings', kwargs={"group_id": self.group.id}))

        get_group_creator_and_admins.assert_called()

        self.group.refresh_from_db()
        self.assertEquals(self.user, self.group.creator)
        self.assertIn(self.user, self.group.admins.all())
        
        patch.stop()
    
    def test_requires_creator_role(self):
        # print("start test 2")
        def side_effect(group, bot):
            # print("called side effect 2")
            if group.id == 1:
                return (self.user, [self.user])
            elif group.id == 2:
                return (self.other_admin, [self.other_admin])
        
        patch = mock.patch("bot.bot.get_group_creator_and_admins", new=mock.MagicMock(side_effect=side_effect))
        get_group_creator_and_admins = patch.start()

        self.client.force_login(user=self.user)
        response = self.client.post("/groups/%d/settings/sync_admins" % self.other_group.id, follow=True)
        self.assertEquals(response.status_code, 403)
        get_group_creator_and_admins.assert_not_called()
        
        patch.stop()'''
