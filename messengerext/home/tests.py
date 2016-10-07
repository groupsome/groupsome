from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.auth.models import User
from django.db import models
from . import models
from gallery.models import Album
from events.models import Event
from bot.models import TelegramUser
import hashlib


def create_user():
    username = 'Superuser'
    user = User.objects.create_user(username, 'superuser@super.com', 'Password')
    user.save()
    telegram_id = int(hashlib.md5(user.username.encode("utf-8")).hexdigest()[:8], 16)
    TelegramUser.create_and_save(user=user, telegram_id=telegram_id)
    return user


class TestHomeView(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_redirect_to_home_works_for_authenticated_user(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/', follow=True)
        self.assertRedirects(response, reverse('home:home'))

    def test_login_needed_before_home(self):
        response = self.client.get('/', follow=True)
        self.assertRedirects(response, reverse('pages:landing'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Not logged in.')

    def test_home_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('home:home'))
        self.assertTemplateUsed(response, 'home/home.html')

    def test_home_view_uses_user_groups(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="abc", telegram_id=1)
        group.users.add(self.user)
        photo = models.Photo.create_and_save(user=self.user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.jpg", thumbnail="TODO")
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('home:home'))
        self.assertTrue(response.context['user_groups'])

    def test_home_view_shows_nothing_for_user_in_no_groups(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('home:home'))
        self.assertFalse(response.context['feed_list'])

    def test_home_view_returns_no_user_content_when_not_using_ajax(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="abc", telegram_id=2)
        group.users.add(self.user)
        photo = models.Photo.create_and_save(user=self.user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.jpg", thumbnail="TODO")
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('home:home'))
        self.assertEquals(response.context['feed_list'], [])
        self.assertTemplateUsed(response, 'home/home.html')

    def test_home_view_returns_user_content_when_using_ajax(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="abc", telegram_id=2)
        group.users.add(self.user)
        photo = models.Photo.create_and_save(user=self.user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.jpg", thumbnail="TODO")
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('home:home'), {'group': group.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(response.context['feed_list'])
        self.assertTemplateUsed(response, 'home/feed.html')

    def test_home_view_uses_audio_player_for_audio(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="abc", telegram_id=2)
        group.users.add(self.user)
        audio = models.Audio.create_and_save(user=self.user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.mp3", duration_sec="300", title="Meteora", interpret="Linkin Park",
                                             telegram_id=2004)
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('home:home'), {'group': group.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateUsed(response, 'assets/audio_player.html')

    def test_ajax_request(self):
        self.client.force_login(user=self.user)
        response = self.client.post('/home', {"page": "2", "querystring_key": "page"},
                                    **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertTemplateUsed('home/feed.html')

    def test_authenticated_user_is_not_redirected_to_landing(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/', follow=True)
        self.assertRedirects(response, reverse('home:home'))

    def test_authenticated_user_is_not_redirected_to_login(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/', follow=True)
        self.assertRedirects(response, reverse('home:home'))

    def test_newest_item_timestamp_in_request(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="abc", telegram_id=2)
        group.users.add(self.user)
        link1 = models.Link.create_and_save(user=self.user, group=group, timestamp="2016-05-22 12:59:10+01:00",
                                            url="https://www.thisOneNot.de/")
        link2 = models.Link.create_and_save(user=self.user, group=group, timestamp="2016-05-24 12:59:10+01:00",
                                            url="https://www.thisOneShouldBeIn.de/")
        self.client.force_login(user=self.user)
        response = self.client.get('/home', {"newest-item-timestamp": "2016-05-23-11:00:41", 'group': group.id},
                                   **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertTrue(len(response.context['feed_list']) == 1)

    def test_newest_item_timestamp_in_request_without_specified_group(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="abc", telegram_id=2)
        group.users.add(self.user)
        link1 = models.Link.create_and_save(user=self.user, group=group, timestamp="2016-05-22 12:59:10+01:00",
                                            url="https://www.thisOneNot.de/")
        link2 = models.Link.create_and_save(user=self.user, group=group, timestamp="2016-05-24 12:59:10+01:00",
                                            url="https://www.thisOneShouldBeIn.de/")
        self.client.force_login(user=self.user)
        response = self.client.get('/home', {"newest-item-timestamp": "2016-05-23-11:00:41"},
                                   **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertTrue(len(response.context['feed_list']) == 1)


class TestHomeGroupView(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_home_view_uses_right_groups(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="abc", telegram_id=3)
        group.users.add(self.user)
        group_2 = models.Group.create_and_save(name="Relegationsspiel", picture="", description="abc", telegram_id=4)
        group_2.users.add(self.user)
        photo = models.Photo.create_and_save(user=self.user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.jpg", thumbnail="TODO")
        photo_2 = models.Photo.create_and_save(user=self.user, group=group_2, timestamp="2016-05-25 12:59:10+01:00",
                                               file="2.jpg", thumbnail="TODO")
        self.client.force_login(user=self.user)
        response = self.client.get('/home', {'group': group.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(len(response.context['feed_list']), 1)

    def test_home_view_uses_all_groups(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="abc", telegram_id=5)
        group.users.add(self.user)
        group_2 = models.Group.create_and_save(name="Relegationsspiel", picture="", description="abc", telegram_id=6)
        group_2.users.add(self.user)
        photo = models.Photo.create_and_save(user=self.user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.jpg", thumbnail="TODO")
        photo_2 = models.Photo.create_and_save(user=self.user, group=group_2, timestamp="2016-05-25 12:59:10+01:00",
                                               file="2.jpg", thumbnail="TODO")
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('home:home'), {'group': [group.id, group_2.id]},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateUsed('home/feed.html')
        self.assertEquals(len(response.context['feed_list']), 2)


class TestGroupModel(TestCase):
    def test_group_create(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="id", description="Crazy trip",
                                             telegram_id=7)
        self.assertEquals(len(models.Group.objects.all()), 1)
        self.assertEquals(group.name, "Croatia 2016")
        self.assertEquals(group.chat_photo_file_id, "id")
        self.assertEquals(group.description, "Crazy trip")
        self.assertEquals(group.telegram_id, 7)

    def test_string_representation(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="TODO", description="Crazy trip",
                                             telegram_id=8)
        self.assertEquals(str(group), "Croatia 2016")

    def test_many_users(self):
        username1 = 'Superuser1'
        user1 = User.objects.create_user(username1, 'superuser1@super.com', 'Password')
        user1.save()
        telegram_id = int(hashlib.md5(username1.encode("utf-8")).hexdigest()[:8], 16)
        TelegramUser.create_and_save(user=user1, telegram_id=telegram_id)
        username2 = 'Superuser2'
        user2 = User.objects.create_user(username2, 'superuser2@super.com', 'Password')
        user2.save()
        telegram_id = int(hashlib.md5(username2.encode("utf-8")).hexdigest()[:8], 16)
        TelegramUser.create_and_save(user=user2, telegram_id=telegram_id)
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=122)
        group.users.add(user1)
        group.users.add(user2)
        self.assertEquals(len(group.users.all()), 2)


class TestPhotoModel(TestCase):
    def test_photo_create(self):
        # User
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=9)
        photo = models.Photo.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.jpg", thumbnail="1_thumb.jpg")
        self.assertEquals(len(models.Photo.objects.all()), 1)
        self.assertEquals(photo.user, user)
        self.assertEquals(photo.group, group)
        self.assertEquals(photo.timestamp, "2016-05-25 12:59:10+01:00")
        self.assertEquals(photo.file, "1.jpg")
        self.assertEquals(photo.thumbnail, "1_thumb.jpg")


class TestTextModel(TestCase):
    def test_text_create(self):
        # User
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=10)
        text = models.Text.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                           content="When do we start?")
        self.assertEquals(len(models.Text.objects.all()), 1)
        self.assertEquals(text.user, user)
        self.assertEquals(text.group, group)
        self.assertEquals(text.timestamp, "2016-05-25 12:59:10+01:00")
        self.assertEquals(text.content, "When do we start?")

    def test_string_representation(self):
        # User
        user = User.objects.create_user('Superuser', 'superuser@super.com', 'Password')
        user.save()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=11)
        text = models.Text.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                           content="When do we start?")
        self.assertEquals(str(text), "When do we start?")


class TestAlbumModel(TestCase):
    def test_album_create(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=111)
        album = Album.create_and_save(name="Croatia 2016 Pag", description="Holidays", group=group)
        self.assertEquals(len(Album.objects.all()), 1)
        self.assertEquals(album.name, "Croatia 2016 Pag")
        self.assertEquals(album.description, "Holidays")

    def test_string_representation(self):
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=111)
        album = Album.create_and_save(name="Croatia 2016 Pag", description="Holidays", group=group)
        self.assertEquals(str(album), "Croatia 2016 Pag")


class TestAudioModel(TestCase):
    def test_audio_create(self):
        # User
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=12)
        audio = models.Audio.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.mp3", duration_sec="300", title="Meteora", interpret="Linkin Park",
                                             telegram_id=2000)
        self.assertEquals(len(models.Audio.objects.all()), 1)
        self.assertEquals(audio.user, user)
        self.assertEquals(audio.group, group)
        self.assertEquals(audio.timestamp, "2016-05-25 12:59:10+01:00")
        self.assertEquals(audio.file, "1.mp3")
        self.assertEquals(audio.duration_sec, "300")
        self.assertEquals(audio.title, "Meteora")
        self.assertEquals(audio.interpret, "Linkin Park")


class TestVideoModel(TestCase):
    def test_video_create(self):
        # User
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=13)
        video = models.Video.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                             file="1.mkv", duration_sec="300", width="1920", height="1080",
                                             thumbnail="1_thumb.jpg")
        self.assertEquals(len(models.Video.objects.all()), 1)
        self.assertEquals(video.user, user)
        self.assertEquals(video.group, group)
        self.assertEquals(video.timestamp, "2016-05-25 12:59:10+01:00")
        self.assertEquals(video.file, "1.mkv")
        self.assertEquals(video.duration_sec, "300")
        self.assertEquals(video.width, "1920")
        self.assertEquals(video.height, "1080")
        self.assertEquals(video.thumbnail, "1_thumb.jpg")


class TestLinkModel(TestCase):
    def test_link_create(self):
        # User
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=14)
        link = models.Link.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                           url="https://www.google.de/")
        self.assertEquals(len(models.Link.objects.all()), 1)
        self.assertEquals(link.user, user)
        self.assertEquals(link.group, group)
        self.assertEquals(link.timestamp, "2016-05-25 12:59:10+01:00")
        self.assertEquals(link.url, "https://www.google.de/")

    def test_string_representation(self):
        # User
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=15)
        link = models.Link.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                           url="https://www.google.de/")
        self.assertEquals(str(link), "https://www.google.de/")


class TestFileModel(TestCase):
    def test_file_create(self):
        # User
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=16)
        file = models.File.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                           other_file="Overview.pdf", file_name='overview', doc_type="JPEG",
                                           telegram_id='3000')
        self.assertEquals(len(models.File.objects.all()), 1)
        self.assertEquals(file.user, user)
        self.assertEquals(file.group, group)
        self.assertEquals(file.timestamp, "2016-05-25 12:59:10+01:00")
        self.assertEquals(file.other_file, "Overview.pdf")
        self.assertEquals(file.doc_type, "JPEG")

    def test_string_representation(self):
        # User
        user = User.objects.create_user('Superuser', 'superuser@super.com', 'Password')
        user.save()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=17)
        file = models.File.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                           other_file="Overview.pdf", file_name='overview', doc_type="JPEG",
                                           telegram_id='3001')
        self.assertEquals(str(file), "Overview.pdf")


class TestStickerModel(TestCase):
    def test_sticker_create(self):
        # User
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Croatia 2016", picture="", description="", telegram_id=18)
        sticker = models.Sticker.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                                 file="TODO", telegram_id="18")
        self.assertEquals(len(models.Sticker.objects.all()), 1)
        self.assertEquals(sticker.user, user)
        self.assertEquals(sticker.group, group)
        self.assertEquals(sticker.timestamp, "2016-05-25 12:59:10+01:00")
        self.assertEquals(sticker.file, "TODO")
        self.assertEquals(sticker.telegram_id, "18")


class TestEventModel(TestCase):
    def test_event_create(self):
        # Group
        group = models.Group.create_and_save(name="Rock im Park", picture="", description="", telegram_id=19)
        event = Event.create_and_save(name="Rock im Park", location="Nürnberg", group=group,
                                      allday=True, start="2016-06-04 8:00+01:00")

        self.assertEquals(len(Event.objects.all()), 1)
        self.assertEquals(event.name, "Rock im Park")
        self.assertEquals(event.location, "Nürnberg")
        self.assertEquals(event.group, group)
        self.assertEquals(event.allday, True)
        self.assertEquals(event.start, "2016-06-04 8:00+01:00")

    def test_string_representation(self):
        # Group
        group = models.Group.create_and_save(name="Rock im Park", picture="", description="", telegram_id=20)
        event = Event.create_and_save(name="Rock im Park", group=group, location="Nürnberg",
                                      allday=True, start="2016-06-04 8:00+01:00")

        self.assertEquals(str(event), "Rock im Park")
