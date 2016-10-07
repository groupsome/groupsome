from django.test import TestCase, RequestFactory
from django.core.urlresolvers import resolve, reverse
from django.http import HttpRequest
from django.test.client import Client
from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.core.cache import cache
from . import models
from . import views
from . import bot
import events
import datetime
from accounts.models import LoginToken
from home.models import Photo, File, Audio, Sticker
import telepot
import json
import home
import mock
import os
import events
from surveys.models import Survey, Choice, Vote
import django_rq
import rq_scheduler
from groups.tests import create_user, create_group
from bot.models import TelegramUser


def mock_has_call_with(mock, arg):
    for call in mock.mock_calls:
        if list(call)[1][0] == arg:
            return True
    return False


class TelegramLogEntry(TestCase):
    def test_TelegramLogEntry_create(self):
        log = models.TelegramLogEntry.create_and_save(json='{"chat": {"first_name": "Jon", "id": "123456789", '
                                                           '"last_name": "Doe", "type": "private"}, '
                                                           '"date": "1463868575", "from": {"first_name": "Jon", '
                                                           '"id": "123456789", "last_name": "Doe"}, '
                                                           '"message_id": "27", "text": "/register"}')
        self.assertEquals(len(models.TelegramLogEntry.objects.all()), 1)
        self.assertEquals(log.json, '{"chat": {"first_name": "Jon", "id": "123456789", "last_name": "Doe", '
                                    '"type": "private"}, "date": "1463868575", "from": {"first_name": "Jon", '
                                    '"id": "123456789", "last_name": "Doe"}, "message_id": "27", '
                                    '"text": "/register"}')


class TestTelegramUserModel(TestCase):
    def test_TelegramUserModel_create(self):
        # User
        user = User.objects.create_user('Superuser', 'superuser@super.com', 'Password')
        user.save()
        telegramUser = models.TelegramUser.create_and_save(user, "100")
        self.assertEquals(len(models.TelegramUser.objects.all()), 1)
        self.assertEquals(telegramUser.user, user)
        self.assertEquals(telegramUser.telegram_id, "100")


class TestWebhook(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.webhook_url = reverse('bot:webhook', kwargs={"secret": settings.TELEGRAM_WEBHOOK_SECRET})
        self.wrong_webook_url = reverse('bot:webhook', kwargs={"secret": "bla"})

    def test_get(self):
        response = self.client.get(self.wrong_webook_url)
        self.assertEquals(response.status_code, 405)

    def test_wrong_secret(self):
        response = self.client.post(self.wrong_webook_url)
        self.assertEquals(response.status_code, 404)

    def test_invalid_content_type(self):
        response = self.client.post(self.webhook_url, content_type="application/x-www-form-urlencoded")
        self.assertEquals(response.status_code, 415)

    def test_invalid_json(self):
        response = self.client.post(self.webhook_url, data="[}", content_type="application/json")
        self.assertEquals(response.status_code, 400)

    @mock.patch("bot.bot.MessageHandler.handle")
    def test_message(self, handle_method):
        update = '{"update_id":746461354,\n"message":{"message_id":59,"from":{"id":123456789,"first_name":"Jon"},' \
                 '"chat":{"id":-987654321,"title":"Groupsome Test","type":"group"},"date":1463867713,"text":"test"}}'
        response = self.client.post(self.webhook_url, data=update, content_type="application/json")
        self.assertEquals(response.status_code, 200)
        handle_method.assert_called()


class TestBot():
    def __init__(self):
        self.messageSent = False

    def sendMessage(self, chat_id, text, reply_markup=None, reply_to_message_id=None):
        self.messageSent = True
        return {"text": "sometext", "from": {"id": 123456789, "first_name": "Jon"},
                "date": 1473851534, "chat": {"title": "TestGroup", "id": -117883109, "type": "group"},
                "entities": [{"offset": 0, "length": 24, "type": "bot_command"}], "message_id": 894}

    def getUserProfilePhotos(self, user_id):
        return {'total_count': 0, 'photos': []}

    def download_file(self, file_id, file_name):
        pass

    def answerCallbackQuery(self, query_id, message):
        pass

    def editMessageText(self, chat_msg_id, query):
        pass
    
    def getChatAdministrators(self, group_id):
        return []
    
    def getChatMember(self, user_id):
        return {}


def noop_update_user_avatar(telegram_user, bot):
    pass


def noop_get_group_creator_and_admins(group, bot):
    return None, []


@mock.patch("bot.bot.update_user_avatar", new=noop_update_user_avatar)
@mock.patch("bot.bot.get_group_creator_and_admins", new=noop_get_group_creator_and_admins)
class TestMessageHandler(TestCase):
    def test_register(self):
        b = TestBot()
        handler = bot.MessageHandler(b, bot_user_id=0)
        msg = json.loads('{"chat": {"first_name": "Jon", "id": "123456789", "last_name": "Doe", '
                         '"type": "private"}, "date": "1463868575", "from": {"first_name": "Jon", "id": "123456789", '
                         '"last_name": "Doe"}, "message_id": "27", "text": "/register"}')
        handler.handle(msg)
        user = User.objects.get(username="Jon_Doe")
        self.assertIsNotNone(user.password)
        self.assertTrue(b.messageSent)

    def test_newpass(self):
        b = TestBot()
        handler = bot.MessageHandler(b, bot_user_id=0)
        msg = json.loads('{"chat": {"first_name": "Jon", "id": "123456789", "last_name": "Doe", '
                         '"type": "private"}, "date": "1463868575", "from": {"first_name": "Jon", "id": "123456789", '
                         '"last_name": "Doe"}, "message_id": "27", "text": "/register"}')
        handler.handle(msg)
        user = User.objects.get(username="Jon_Doe")
        password = user.password
        msg = json.loads('{"chat": {"first_name": "Jon", "id": "123456789", "last_name": "Doe", '
                         '"type": "private"}, "date": "1463868575", "from": {"first_name": "Jon", "id": "123456789", '
                         '"last_name": "Doe"}, "message_id": "27", "text": "/newpassword"}')
        handler.handle(msg)
        user = User.objects.get(username="Jon_Doe")
        self.assertNotEqual(password, user.password)
        self.assertTrue(b.messageSent)

    def test_group_text(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "test1", "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))
        self.assertEquals(home.models.Text.objects.filter(telegram_id=122).count(), 1)

    # @mock.patch('os.rename')
    @mock.patch('urllib.request.urlretrieve')
    @mock.patch("bot.bot.get_open_graph_tags")
    def test_group_text_with_link(self, get_open_graph_tags, url_retrieve):
        get_open_graph_tags.return_value = {'og:title': 'Google',
                                            'og:description': '117. Geburtstag von Lotte Reiniger #GoogleDoodle',
                                            'og:image:width': '391', 'og:image': 'http://www.google.com/logos/doodles/'
                                                                                 '2016/lotte-reinigers-117th-birthday-'
                                                                                 '5079873255112704.5-thp.png',
                                            'og:image:height': '220'}

        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"entities": [{"offset": 35, "type": "url", "length": 9}], "text": "hey check diese '
                                  'coole website aus: google.de", "from": {"id": 123456789, "first_name": "Jon"}, '
                                  '"chat": {"title": "Groupsome Test", "id": -987654321, "type": "group"}, '
                                  '"message_id": 197, "date": 1464874655}'))

        text = home.models.Text.objects.get(telegram_id=197)
        self.assertEquals(text.content, "hey check diese coole website aus: google.de")

        link = home.models.Link.objects.get(telegram_id=197)
        # url_retrieve.return_value = (str(link.telegram_id) + '.png'), {'Content-Type': 'image/png'}

        self.assertEquals(link.url, "http://google.de")
        self.assertEquals(link.title, "Google")
        self.assertEquals(link.description, "117. Geburtstag von Lotte Reiniger #GoogleDoodle")
        # self.assertEquals(link.file, str(link.telegram_id) + '.png')
        url_retrieve.assert_called_with('http://www.google.com/logos/doodles/2016/lotte-reinigers-117th-birthday-'
                                        '5079873255112704.5-thp.png')

    def test_private_message(self):
        b = TestBot()
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"date": 1464532947, "text": "privat", "chat": {"type": "private", "id": 123456789, '
                                  '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                                  '"message_id": 124}'))
        self.assertTrue(b.messageSent)

    def test_group_join(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"from": {"first_name": "Jon", "id": 123456789}, "new_chat_member": {"first_name": '
                                  '"Firstname", "last_name": "Lastname", "id": 172233927}, "message_id": 129, '
                                  '"date": 1464533248, "chat": {"id": -987654321, "title": "Groupsome Test", "type": '
                                  '"group"}, "new_chat_participant": {"first_name": "Firstname", "last_name": '
                                  '"Lastname", "id": 172233927}}'))
        group = home.models.Group.objects.get(telegram_id=-987654321)

        found = False
        for user in group.users.all():
            if user.username == "Firstname_Lastname":
                found = True
        self.assertTrue(found)

    def test_group_leave(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"from": {"first_name": "Jon", "id": 123456789}, "new_chat_member": '
                                  '{"first_name": "Firstname", "last_name": "Lastname", "id": 172233927}, "message_id":'
                                  ' 129, "date": 1464533248, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}, "new_chat_participant": {"first_name": "Firstname", '
                                  '"last_name": "Lastname", "id": 172233927}}'))
        handler.handle(json.loads('{"from": {"first_name": "Jon", "id": 123456789}, "left_chat_participant": '
                                  '{"first_name": "Firstname", "last_name": "Lastname", "id": 172233927}, "message_id":'
                                  '130, "date": 1464533256, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}, "left_chat_member": {"first_name": "Firstname", "last_name": '
                                  '"Lastname", "id": 172233927}}'))
        group = home.models.Group.objects.get(telegram_id=-987654321)

        found = False
        for user in group.users.all():
            if user.username == "Firstname_Lastname":
                found = True
        self.assertFalse(found)

    def test_group_leave_untracked_user(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"from": {"first_name": "Jon", "id": 123456789}, "left_chat_participant": '
                                  '{"first_name": "Test", "last_name": "Test", "id": 181259920}, "message_id": 130, '
                                  '"date": 1464533256, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}, "left_chat_member": {"first_name": "Firstname", "last_name": '
                                  '"Lastname", "id": 172233927}}'))
        # no exceptions

    def test_group_join_bot(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=237961645)
        handler.handle(json.loads('{"chat": {"title": "Groupsome Test", "type": "group", "id": -987654321}, '
                                  '"new_chat_participant": {"username": "groupsomeJonbot", "first_name": '
                                  '"groupsome (Jon)", "id": 237961645}, "new_chat_member": '
                                  '{"username": "groupsomeJonbot", "first_name": "groupsome (Jon)", '
                                  '"id": 237961645}, "message_id": 134, "from": {"first_name": "Jon", '
                                  '"id": 123456789}, "date": 1464534570}'))
        group = home.models.Group.objects.get(telegram_id=-987654321)

        found = False
        for user in group.users.all():
            if user.username == "groupsomeJonbot":
                found = True
        self.assertFalse(found)

    def test_changed_username(self):
        b = TestBot()
        handler = bot.MessageHandler(b, bot_user_id=0)
        msg = json.loads('{"chat": {"first_name": "Jon", "id": "123456789", "last_name": "Doe", '
                         '"type": "private"}, "date": "1463868575", "from": {"first_name": "Jon", "id": "123456789", '
                         '"last_name": "Doe"}, "message_id": "27", "text": "/register"}')
        handler.handle(msg)
        user = User.objects.get(username="Jon_Doe")
        user.username = "Anders"
        handler.handle(msg)
        # TODO check reply uses the changed username

    @mock.patch("django_rq.enqueue")
    def test_group_photo(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)
        b.getFile.return_value = {"file_path": "foo.jpg"}
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"date": 1464540012, "from": {"id": 123456789, "first_name": "Jon"}, '
                                  '"message_id": 146, "chat": {"id": -987654321, "type": "group", '
                                  '"title": "Groupsome Test"}, "photo": [{"file_size": 1848, "height": 90, '
                                  '"file_path": "photo/file_5.jpg", "file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_'
                                  'v2Rw0ABGn3KICDyKODQscAAgI", "width": 90}, {"file_size": 24129, "height": 320, '
                                  '"file_path": "photo/file_7.jpg", "file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_'
                                  'v2Rw0ABKBpm-IkDT1jQ8cAAgI", "width": 320}, {"file_size": 96927, "height": 800, '
                                  '"file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABLL_aW6tRB6RRMcAAgI", '
                                  '"width": 800}, {"file_size": 204815, "height": 1280, '
                                  '"file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABAmY6A3gEJWMQccAAgI", '
                                  '"width": 1280}, {"file_size": 432200, "height": 2560, '
                                  '"file_path": "photo/file_6.jpg", "file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_'
                                  'v2Rw0ABGs7A9BeSM3cQMcAAgI", "width": 2560}]}'))

        filename = os.path.join(settings.MEDIA_ROOT, "photo",
                                "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABGs7A9BeSM3cQMcAAgI.jpg")
        enqueue.assert_any_call(bot.download_file, "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABGs7A9BeSM3cQMcAAgI", filename)
        self.assertTrue(mock_has_call_with(enqueue, Photo.create_and_save))

    @mock.patch("django_rq.enqueue")
    def test_group_photo_without_file_path(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)
        b.getFile.return_value = {"file_path": "foo.jpg"}
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"date": 1464540012, "from": {"id": 123456789, "first_name": "Jon"}, '
                                  '"message_id": 146, "chat": {"id": -987654321, "type": "group", '
                                  '"title": "Groupsome Test"}, "photo": [{"file_size": 1848, "height": 90, '
                                  '"file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABGn3KICDyKODQscAAgI", "width": 90}, '
                                  '{"file_size": 24129, "height": 320, "file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_'
                                  'v2Rw0ABKBpm-IkDT1jQ8cAAgI", "width": 320}, {"file_size": 96927, "height": 800, '
                                  '"file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABLL_aW6tRB6RRMcAAgI", '
                                  '"width": 800}, {"file_size": 204815, "height": 1280, '
                                  '"file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABAmY6A3gEJWMQccAAgI", '
                                  '"width": 1280}, {"file_size": 432200, "height": 2560, '
                                  '"file_id": "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABGs7A9BeSM3cQMcAAgI", '
                                  '"width": 2560}]}'))

        filename = os.path.join(settings.MEDIA_ROOT, "photo",
                                "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABGs7A9BeSM3cQMcAAgI.jpg")
        enqueue.assert_any_call(bot.download_file, "AgADAgAD6KoxG85dhAOkTYCWBVvyk_v2Rw0ABGs7A9BeSM3cQMcAAgI", filename)
        self.assertTrue(mock_has_call_with(enqueue, Photo.create_and_save))

    @mock.patch("django_rq.enqueue")
    def test_group_document_photo(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)
        b.getFile.return_value = {"file_path": "foo.jpg"}
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"from": {"first_name": "Jon", "id": 123456789}, "date": 1464814467, '
                                  '"chat": {"type": "group", "id": -987654321, "title": "Groupsome Test"}, '
                                  '"message_id": 191, "document": {"file_size": 60072, '
                                  '"file_id": "BQADAgADTgADzl2EA4wpFcit9iTCAg", "mime_type": "image/jpeg", '
                                  '"file_name": "SlipperyPerkyLaughingthrush-poster.jpg", "thumb": {"file_size": 9823, '
                                  '"file_id": "AAQCABOjvIIqAAS3DkK6OhpS9gQTAgABAg", "width": 200, "height": 200}}}'))

        filename = os.path.join(settings.MEDIA_ROOT, "photo", "BQADAgADTgADzl2EA4wpFcit9iTCAg.jpg")
        enqueue.assert_any_call(bot.download_file, "BQADAgADTgADzl2EA4wpFcit9iTCAg", filename)
        self.assertTrue(mock_has_call_with(enqueue, Photo.create_and_save))

    @mock.patch("django_rq.enqueue")
    def test_group_document(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"from": {"id": 123456789, "first_name": "Jon"}, "message_id": 192, '
                                  '"chat": {"id": -987654321, "title": "Groupsome Test", "type": "group"}, '
                                  '"document": {"file_id": "BQADAgADTwADzl2EA_tRyicOEhLBAg", '
                                  '"mime_type": "application/octet-stream", "file_size": 10485760, '
                                  '"file_name": "testfile.img"}, "date": 1464815418}'))

        filename = os.path.join(settings.MEDIA_ROOT, "file", "BQADAgADTwADzl2EA_tRyicOEhLBAg.img")
        enqueue.assert_any_call(bot.download_file, "BQADAgADTwADzl2EA_tRyicOEhLBAg", filename)
        self.assertTrue(mock_has_call_with(enqueue, File.create_and_save))

    @mock.patch("django_rq.enqueue")
    def test_group_audio_mp3(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"audio": {"title": "Ghostbusters (Kill Paris Remix)", "mime_type": "audio/mpeg", '
                                  '"file_id": "BQADAgADUQADzl2EA0aZHumwX0-nAg", "file_size": 8574071, "duration": 201, '
                                  '"performer": "Kill Paris"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                                  '"date": 1464816741, "message_id": 194, "chat": {"title": "Groupsome Test", '
                                  '"id": -987654321, "type": "group"}}'))

        self.assertTrue(mock_has_call_with(enqueue, bot.download_file))
        self.assertTrue(mock_has_call_with(enqueue, bot.encode_audio))
        self.assertTrue(mock_has_call_with(enqueue, Audio.create_and_save))

    @mock.patch("django_rq.enqueue")
    def test_group_audio_mp3_without_id3_tags(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"from": {"first_name": "Jon", "id": 123456789}, "message_id": 193, '
                                  '"chat": {"title": "Groupsome Test", "type": "group", "id": -987654321}, '
                                  '"audio": {"file_size": 954, "duration": 0, "mime_type": "audio/mpeg", '
                                  '"file_id": "BQADAgADUAADzl2EAx474ZPR2YhuAg"}, "date": 1464816567}'))

        self.assertTrue(mock_has_call_with(enqueue, bot.download_file))
        self.assertTrue(mock_has_call_with(enqueue, bot.encode_audio))
        self.assertTrue(mock_has_call_with(enqueue, Audio.create_and_save))

    @mock.patch("django_rq.enqueue")
    def test_group_voice(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"voice": {"mime_type": "audio/ogg", "duration": 1, '
                                  '"file_id": "AwADAgADUgADzl2EAyaoKcrF2dsYAg", "file_size": 12060}, '
                                  '"date": 1464817944, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}, "message_id": 196, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}}'))

        self.assertTrue(mock_has_call_with(enqueue, bot.download_file))
        self.assertTrue(mock_has_call_with(enqueue, Audio.create_and_save))

    @mock.patch("django_rq.enqueue")
    def test_group_sticker(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"sticker": {"file_size": 13942, "emoji": "\ud83d\ude0a", "height": 512, '
                                  '"file_id": "BQADBAADZQMAAuJy2QAB_DMZrKyLlRIC", '
                                  '"thumb": {"file_id": "AAQEABMGWYwwAATWgMIxpU77Pf8YAAIC", "file_size": 2608, '
                                  '"width": 128, "height": 128}, "width": 512}, "date": 1464540797, '
                                  '"chat": {"id": -987654321, "type": "group", "title": "Groupsome Test"}, '
                                  '"from": {"id": 123456789, "first_name": "Jon"}, "message_id": 148}'))

        self.assertTrue(mock_has_call_with(enqueue, bot.download_file))
        self.assertTrue(mock_has_call_with(enqueue, bot.convert_sticker_to_png))
        self.assertTrue(mock_has_call_with(enqueue, Sticker.create_and_save))

    @mock.patch("django_rq.enqueue")
    def test_group_video(self, enqueue):
        b = mock.Mock(spec=telepot.Bot)

        def side_effect(file_id):
            if file_id == "BAADAgADaAADzl2EAxb3BbNdR1tqAg":
                return {"file_path": "foo/bar.mp4"}
            elif file_id == "AAQCABO8MEgNAASnOVTVhILgldo_AQABAg":
                return {"file_path": "foo/bar.jpg"}
            else:
                return None
        b.getFile.side_effect = side_effect

        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"from": {"id": 123456789, "first_name": "Jon"}, "chat": {"id": -987654321, '
                                  '"title": "Groupsome Test", "type": "group"}, "date": 1466362222, '
                                  '"message_id": 269, "video": {"height": 640, "thumb": {"file_size": 2659, '
                                  '"height": 90, "width": 50, "file_id": "AAQCABO8MEgNAASnOVTVhILgldo_AQABAg"}, '
                                  '"width": 360, "file_id": "BAADAgADaAADzl2EAxb3BbNdR1tqAg", "file_size": 202528, '
                                  '"duration": 1}}'))

        self.assertTrue(mock_has_call_with(enqueue, bot.download_file))
        self.assertTrue(mock_has_call_with(enqueue, bot.generate_video_thumbnail))
        self.assertTrue(mock_has_call_with(enqueue, bot.encode_video))
        self.assertTrue(mock_has_call_with(enqueue, bot.save_video))

    def test_group_chat_photo_update(self):
        b = mock.Mock(spec=telepot.Bot)
        handler = bot.MessageHandler(b, bot_user_id=0)
        msg = json.loads('{"chat": {"title": "Gruppenphoto Test", "type": "group", "id": -160923564}, '
                         '"date": 1470750917, "message_id": 622, "from": {"first_name": "Stefan", "id": 204185475}, '
                         '"new_chat_photo": [{"file_size": 12575, "width": 160, "height": 160, "file_id": '
                         '"AgADAgADB6gxG4OfKwxGa8ITt0WkdZwIcQ0ABPHUxc2JiG4aN_MAAgI"}, '
                         '{"file_size": 44710, "width": 320,'
                         ' "height": 320, "file_id": "AgADAgADB6gxG4OfKwxGa8ITt0WkdZwIcQ0ABNqUGYNhoQodOPMAAgI"}, '
                         '{"file_size": 99710, "width": 640, "height": 640, "file_id": '
                         '"AgADAgADB6gxG4OfKwxGa8ITt0WkdZwIcQ0ABFUwLh4MGxMiOfMAAgI"}]}')
        handler.handle(msg)
        b.download_file.assert_called()

    def test_group_chat_photo_no_update_if_already_downloaded(self):
        b = mock.Mock(spec=telepot.Bot)
        home.models.Group.create_and_save(name="Gruppenphoto Test",
                                          picture="AgADAgADB6gxG4OfKwxGa8ITt0WkdZwIcQ0ABNqUGYNhoQodOPMAAgI",
                                          description="abc", telegram_id=-160923564)
        handler = bot.MessageHandler(b, bot_user_id=0)
        msg = json.loads('{"chat": {"title": "Gruppenphoto Test", "type": "group", "id": -160923564}, '
                         '"date": 1470750917, "message_id": 622, "from": {"first_name": "Stefan", "id": 204185475}, '
                         '"new_chat_photo": [{"file_size": 12575, "width": 160, "height": 160, "file_id": '
                         '"AgADAgADB6gxG4OfKwxGa8ITt0WkdZwIcQ0ABPHUxc2JiG4aN_MAAgI"}, '
                         '{"file_size": 44710, "width": 320,'
                         ' "height": 320, "file_id": "AgADAgADB6gxG4OfKwxGa8ITt0WkdZwIcQ0ABNqUGYNhoQodOPMAAgI"}, '
                         '{"file_size": 99710, "width": 640, "height": 640, "file_id": '
                         '"AgADAgADB6gxG4OfKwxGa8ITt0WkdZwIcQ0ABFUwLh4MGxMiOfMAAgI"}]}')
        handler.handle(msg)
        b.download_file.assert_not_called()

    def test_login_token(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)

        token = LoginToken.objects.create(token="nucR5mqotd")
        token.save()

        handler.handle(json.loads('{"message_id": 171, "chat": {"first_name": "Jon", "id": 123456789, '
                                  '"type": "private"}, "from": {"first_name": "Jon", "id": 123456789}, '
                                  '"entities": [{"length": 6, "type": "bot_command", "offset": 0}], '
                                  '"text": "/start login-nucR5mqotd", "date": 1464553076}'))

        token = LoginToken.objects.get(token="nucR5mqotd")
        self.assertIsNotNone(token.user)

        telegram_user = models.TelegramUser.objects.get(user_id=token.user.id)
        self.assertEquals(telegram_user.telegram_id, 123456789)

    def test_login_token_scan(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)

        token = LoginToken.objects.create(token="nucR5mqotd")
        token.save()

        handler.handle(json.loads('{"message_id": 171, "chat": {"first_name": "Jon", "id": 123456789, '
                                  '"type": "private"}, "from": {"first_name": "Jon", "id": 123456789}, '
                                  '"entities": [{"length": 6, "type": "bot_command", "offset": 0}], '
                                  '"text": "/start login-nucR5mqotd-scan", "date": 1464553076}'))

        token = LoginToken.objects.get(token="nucR5mqotd")
        self.assertIsNotNone(token.user)

        telegram_user = models.TelegramUser.objects.get(user_id=token.user.id)
        self.assertEquals(telegram_user.telegram_id, 123456789)

    def test_login_token_unknown(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"message_id": 171, "chat": {"first_name": "Jon", "id": 123456789, '
                                  '"type": "private"}, "from": {"first_name": "Jon", "id": 123456789}, '
                                  '"entities": [{"length": 6, "type": "bot_command", "offset": 0}], '
                                  '"text": "/start login-nucR5mqotd", "date": 1464553076}'))
        # no exception


class TestAvatarUpdate(TestCase):
    @mock.patch("os.remove")
    @mock.patch("os.path.isfile")
    def test_first_avatar(self, is_file, remove_file):
        b = mock.Mock(spec=telepot.Bot)
        b.getUserProfilePhotos.return_value = {'total_count': 1,
                                               'photos': [[{'height': 160, 'width': 160, 'file_size': 438,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABCAGqe2Dpsz'
                                                                       'a2wMBAAEC'},
                                                           {'height': 320, 'width': 320, 'file_size': 888,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABNi7dp-Fkzo'
                                                                       '23AMBAAEC'},
                                                           {'height': 640, 'width': 640, 'file_size': 2688,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABMeXAmMxids'
                                                                       '83QMBAAEC'}]]}
        is_file.return_value = False

        user = models.TelegramUser()
        user.telegram_id = 1
        user.avatar_file_id = None
        user.avatar_version = 0
        bot.update_user_avatar(user, b)

        remove_file.assert_not_called()
        b.download_file.assert_called()
        self.assertEquals(user.avatar_file_id, "AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABNi7dp-Fkzo23AMBAAEC")
        self.assertEquals(user.avatar_version, 1)

    @mock.patch("os.remove")
    @mock.patch("os.path.isfile")
    def test_new_avatar(self, is_file, remove_file):
        b = mock.Mock(spec=telepot.Bot)
        b.getUserProfilePhotos.return_value = {'total_count': 1,
                                               'photos': [[{'height': 160, 'width': 160, 'file_size': 438,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABCAGqe2Dpsz'
                                                                       'a2wMBAAEC'},
                                                           {'height': 320, 'width': 320, 'file_size': 888,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABNi7dp-Fkzo'
                                                                       '23AMBAAEC'},
                                                           {'height': 640, 'width': 640, 'file_size': 2688,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABMeXAmMxids'
                                                                       '83QMBAAEC'}]]}

        def side_effect(path):
            name = os.path.basename(path)
            return name == "old.jpg"
        is_file.side_effect = side_effect

        user = models.TelegramUser()
        user.telegram_id = 1
        user.avatar_file_id = "old"
        user.avatar_version = 1
        bot.update_user_avatar(user, b)

        remove_file.assert_called()
        b.download_file.assert_called()
        self.assertEquals(user.avatar_file_id, "AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABNi7dp-Fkzo23AMBAAEC")
        self.assertEquals(user.avatar_version, 2)

    @mock.patch("os.remove")
    @mock.patch("os.path.isfile")
    def test_no_new_avatar(self, is_file, remove_file):
        b = mock.Mock(spec=telepot.Bot)
        b.getUserProfilePhotos.return_value = {'total_count': 1,
                                               'photos': [[{'height': 160, 'width': 160, 'file_size': 438,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABCAGqe2Dpsz'
                                                                       'a2wMBAAEC'},
                                                           {'height': 320, 'width': 320, 'file_size': 888,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABNi7dp-Fkzo'
                                                                       '23AMBAAEC'},
                                                           {'height': 640, 'width': 640, 'file_size': 2688,
                                                            'file_id': 'AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABMeXAmMxids'
                                                                       '83QMBAAEC'}]]}

        def side_effect(path):
            name = os.path.basename(path)
            return name == "old.jpg"
        is_file.side_effect = side_effect

        user = models.TelegramUser()
        user.telegram_id = 1
        user.avatar_file_id = "AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABNi7dp-Fkzo23AMBAAEC"
        user.avatar_version = 1
        bot.update_user_avatar(user, b)

        remove_file.assert_not_called()
        b.download_file.assert_not_called()
        self.assertEquals(user.avatar_file_id, "AgADAgADMKsxG85dhAOLS2qZIVDchYLURw0ABNi7dp-Fkzo23AMBAAEC")
        self.assertEquals(user.avatar_version, 1)

    @mock.patch("os.remove")
    @mock.patch("os.path.isfile")
    def test_no_more_avatar(self, is_file, remove_file):
        b = mock.Mock(spec=telepot.Bot)
        b.getUserProfilePhotos.return_value = {'total_count': 0, 'photos': []}
        is_file.return_value = True

        user = models.TelegramUser()
        user.telegram_id = 1
        user.avatar_file_id = "old"
        user.avatar_version = 2
        bot.update_user_avatar(user, b)

        remove_file.assert_called()
        self.assertIsNone(user.avatar_file_id)
        self.assertEquals(user.avatar_version, 3)


class TestFeedback(TestCase):
    def test_feedback(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/feedback", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "private"}}'))
        self.assertEqual(cache.get("123456789_state_feedback"), 1)
        handler.handle(json.loads('{"date": 1464532947, "text": "i love groupsome", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 124}'))
        self.assertIsNotNone(models.Feedback.objects.get(feedback="i love groupsome"))
        self.assertFalse(cache.get("123456789_state_feedback"))


class TestEventCreation(TestCase):
    def test_event_creation_cancel(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/newevent", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))
        self.assertEqual(cache.get("123456789_state"), 1)
        self.assertIsNotNone(cache.get("123456789_event"))
        handler.handle(json.loads('{"date": 1464532947, "text": "/cancel", "chat": {"type": "private", "id": 123456789,'
                                  ' "first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"},'
                                  ' "message_id": 124}'))
        self.assertIsNone(cache.get("123456789_state"))
        self.assertIsNone(cache.get("123456789_event"))

    def test_event_creation(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/newevent", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))
        self.assertEqual(cache.get("123456789_state"), 1)
        self.assertIsNotNone(cache.get("123456789_event"))
        handler.handle(json.loads('{"date": 1464532947, "text": "2/2/12 2:00pm", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 124}'))
        self.assertEqual(cache.get("123456789_state"), 2)
        self.assertIsNotNone(cache.get("123456789_event"))
        handler.handle(json.loads('{"date": 1464532947, "text": "Party!", "chat": {"type": "private", "id": 123456789, '
                                  '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                                  '"message_id": 124}'))
        self.assertEqual(cache.get("123456789_state"), 3)
        self.assertIsNotNone(cache.get("123456789_event"))
        handler.handle(json.loads('{"date": 1464532947, "text": "Party place", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 124}'))
        self.assertIsNone(cache.get("123456789_state"))
        self.assertIsNone(cache.get("123456789_event"))
        self.assertIsNotNone(events.models.Event.objects.get(name="Party!"))

    def test_event_creation_permission_denied(self):
        b = TestBot()
        user = User.objects.create_user("Jon", "Jon@test.test")
        user.save()
        TelegramUser.create_and_save(user=user, telegram_id=123456789)
        admin = create_user()
        group = create_group(user=admin, is_admin=True, users=[user], name="Groupsome Test", telegram_id=-987654321)
        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/newevent", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))
        self.assertIsNone(cache.get("123456789_event"))
        self.assertTrue(b.messageSent)

    def test_max_len_name_and_location(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/newevent", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))
        self.assertEqual(cache.get("123456789_state"), 1)
        self.assertIsNotNone(cache.get("123456789_event"))
        handler.handle(json.loads('{"date": 1464532947, "text": "2/2/12 2:00pm", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 124}'))
        self.assertEqual(cache.get("123456789_state"), 2)
        self.assertIsNotNone(cache.get("123456789_event"))
        handler.handle(json.loads('{"date": 1464532947, "text": '
                                  '"onehundertcharsonehundertcharsonehundertcharsonehundertcharsonehundertcharsone'
                                  'hundertcharsonehundert", "chat": {"type": "private", "id": 123456789, '
                                  '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                                  '"message_id": 124}'))
        self.assertEqual(cache.get("123456789_state"), 2)
        handler.handle(json.loads('{"date": 1464532947, "text": "Party!", "chat": {"type": "private", "id": 123456789, '
                                  '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                                  '"message_id": 124}'))
        handler.handle(json.loads('{"date": 1464532947,'
                                  ' "text": "onehundertcharsonehundertcharsonehundertcharsonehundertcharsonehundert'
                                  'charsonehundertcharsonehundert", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 124}'))
        self.assertEqual(cache.get("123456789_state"), 3)
        handler.handle(json.loads('{"date": 1464532947, "text": "Party place", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 124}'))
        self.assertIsNone(cache.get("123456789_state"))
        self.assertIsNone(cache.get("123456789_event"))
        self.assertIsNotNone(events.models.Event.objects.get(name="Party!"))

    def test_show_event(self):
        group = home.models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                                  telegram_id=-987654321)
        group.save()
        events.models.Event(group=group, name='A', location='B', start=datetime.datetime.now()).save()
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/showevents", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))

    def test_delete_event(self):
        group = home.models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                                  telegram_id=-987654321)
        group.save()
        events.models.Event(group=group, name='A', location='B', start=datetime.datetime.now()).save()
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.scheduler = mock.Mock(spec=rq_scheduler.scheduler.Scheduler)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/deleteevent 1", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))

        self.assertTrue(len(events.models.Event.objects.all()) == 0)

    def test_delete_event_permission_denied(self):
        b = TestBot()
        user = User.objects.create_user("Jon", "Jon@test.test")
        user.save()
        TelegramUser.create_and_save(user=user, telegram_id=123456789)
        admin = create_user()
        group = create_group(user=admin, is_admin=True, users=[user], name="Groupsome Test", telegram_id=-987654321)
        events.models.Event(group=group, name='A', location='B', start=datetime.datetime.now()).save()

        handler = bot.MessageHandler(b, bot_user_id=0)
        handler.scheduler = mock.Mock(spec=rq_scheduler.scheduler.Scheduler)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/deleteevent 1", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))

        self.assertTrue(len(events.models.Event.objects.all()) == 1)
        self.assertTrue(b.messageSent)


@mock.patch("bot.bot.update_user_avatar", new=noop_update_user_avatar)
class TestGroupMemberships(TestCase):
    def test_memberships(self):
        b = mock.Mock(spec=telepot.Bot)
        b.getChatAdministrators.return_value = [{'status': 'creator', 'user': {'id': 123456789, 'first_name': 'Jon'}}]

        def side_effect(group_id, user_id):
            if user_id == 123456789:
                return {'status': 'creator', 'user': {'id': 123456789, 'first_name': 'Jon'}}
            elif user_id == 172233927:
                return {'status': 'administrator', 'user': {'last_name': 'Lastname', 'id': 172233927, 'first_name':
                        'Firstname'}}
        b.getChatMember.side_effect = side_effect

        group = home.models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                                  telegram_id=-987654321)
        group.save()

        admin2 = User.objects.create(username="Firstname Lastname")
        admin2.save()
        telegram_user = models.TelegramUser.objects.create(user=admin2, telegram_id=172233927)
        telegram_user.save()
        group.users.add(admin2)

        creator, admins = bot.get_group_creator_and_admins(group, b)

        owner = models.TelegramUser.objects.get(telegram_id=123456789).user

        self.assertEquals(creator, owner)
        self.assertIn(owner, admins)
        self.assertIn(admin2, admins)


class TestSurveyCreation(TestCase):

    def test_survey_creation(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        # /newsurvey
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/newsurvey", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))
        self.assertEqual(cache.get("123456789_state_survey"), 1)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # Ist das eine Testfrage?
        handler.handle(json.loads('{"date": 1464532947, "text": "Ist das eine Testfrage?", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 130}'))
        self.assertEqual(cache.get("123456789_state_survey"), 2)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # Option 1
        handler.handle(
            json.loads('{"date": 1464532947, "text": "Option 1", "chat": {"type": "private", "id": 123456789, '
                       '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                       '"message_id": 131}'))
        self.assertEqual(cache.get("123456789_state_survey"), 2)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # Option 2
        handler.handle(
            json.loads('{"date": 1464532947, "text": "Option 2", "chat": {"type": "private", "id": 123456789, '
                       '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                       '"message_id": 132}'))

        self.assertEqual(cache.get("123456789_state_survey"), 2)
        self.assertIsNotNone(cache.get("123456789_survey"))
        # /done
        handler.handle(
            json.loads('{"date": 1464532947, "text": "/done", "chat": {"type": "private", "id": 123456789, '
                       '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                       '"message_id": 133}'))
        self.assertEqual(cache.get("123456789_state_survey"), 3)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # /yes
        handler.handle(json.loads('{"date": 1464532947, "text": "/yes", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 134}'))
        self.assertIsNone(cache.get("123456789_state_survey"))
        self.assertIsNone(cache.get("123456789_survey"))
        self.assertIsNone(cache.get("123456789_survey_options"))
        self.assertEqual(len(Survey.objects.get(question="Ist das eine Testfrage?").choices.all()), 2)

    def test_survey_creation_cancel(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        # /newsurvey
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/newsurvey", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))
        self.assertEqual(cache.get("123456789_state_survey"), 1)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # Ist das eine Testfrage?
        handler.handle(json.loads('{"date": 1464532947, "text": "/cancel", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 130}'))

        self.assertIsNone(cache.get("123456789_state_survey"))
        self.assertIsNone(cache.get("123456789_survey"))
        self.assertIsNone(cache.get("123456789_survey_options"))

    def test_survey_creation_max_lengths(self):
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        # /newsurvey
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/newsurvey", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))
        self.assertEqual(cache.get("123456789_state_survey"), 1)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # Ist das eine Testfrage? mehr als 100
        handler.handle(json.loads('{"date": 1464532947, "text": "Ist das eine Testfrage mit mehr als hundert hundert '
                                  'hundert hundert hundert hundert hundert hundert hundert hundert hundert hundert '
                                  'hundert hundert hundert hundert hundert hundert hundert hundert  hundert  hundert", '
                                  '"chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 130}'))
        self.assertEqual(cache.get("123456789_state_survey"), 1)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # Ist das eine Testfrage?
        handler.handle(json.loads('{"date": 1464532947, "text": "Ist das eine Testfrage?","chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 130}'))
        self.assertEqual(cache.get("123456789_state_survey"), 2)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # Option 1
        handler.handle(
            json.loads('{"date": 1464532947, "text": "Option 1", "chat": {"type": "private", "id": 123456789, '
                       '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                       '"message_id": 131}'))
        self.assertEqual(cache.get("123456789_state_survey"), 2)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # Option 2 mehr als 30
        handler.handle(
            json.loads('{"date": 1464532947, "text": "Option 2 mehr als dreßig als dreßig als dreßig als dreßig", '
                       '"chat": {"type": "private", "id": 123456789, '
                       '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                       '"message_id": 132}'))

        self.assertEqual(cache.get("123456789_state_survey"), 2)
        self.assertIsNotNone(cache.get("123456789_survey"))

        # Option 2
        handler.handle(
            json.loads('{"date": 1464532947, "text": "Option 2", "chat": {"type": "private", "id": 123456789, '
                       '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                       '"message_id": 132}'))

        self.assertEqual(cache.get("123456789_state_survey"), 2)
        self.assertIsNotNone(cache.get("123456789_survey"))

        # /done
        handler.handle(
            json.loads('{"date": 1464532947, "text": "/done", "chat": {"type": "private", "id": 123456789, '
                       '"first_name": "Jon"}, "from": {"id": 123456789, "first_name": "Jon"}, '
                       '"message_id": 133}'))
        self.assertEqual(cache.get("123456789_state_survey"), 3)
        self.assertIsNotNone(cache.get("123456789_survey"))
        self.assertIsNotNone(cache.get("123456789_survey_options"))

        # /yes
        handler.handle(json.loads('{"date": 1464532947, "text": "/yes", "chat": {"type": "private", '
                                  '"id": 123456789, "first_name": "Jon"}, "from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "message_id": 134}'))
        self.assertIsNone(cache.get("123456789_state_survey"))
        self.assertIsNone(cache.get("123456789_survey"))
        self.assertIsNone(cache.get("123456789_survey_options"))
        self.assertEqual(len(Survey.objects.get(question="Ist das eine Testfrage?").choices.all()), 2)

    def test_show_survey(self):
        group = home.models.Group.create_and_save(name='TestGroup', picture='', description='test',
                                                  telegram_id=-987654321)
        group.save()
        user = User.objects.create(username="user")
        user.save()
        Survey.create_and_save(question="Ist das eine Testfrage?", creator=user,
                               created=datetime.datetime.now(), group=group, multiselect=True)
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/showsurvey", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "TestGroup", '
                                  '"type": "group"}}'))

    def test_close_survey_as_creator(self):
        group = home.models.Group.create_and_save(name='TestGroup', picture='', description='test',
                                                  telegram_id=-987654321)
        group.save()
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.scheduler = mock.Mock(spec=rq_scheduler.scheduler.Scheduler)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "Create User", '
                                  '"from": {"id": 172233927, '
                                  '"first_name": "user"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))

        user = User.objects.get(username="user")

        Survey.create_and_save(question="Ist das eine Testfrage?", creator=user,
                               created=datetime.datetime.now(), group=group, multiselect=True)

        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/close", '
                                  '"from": {"id": 172233927, '
                                  '"first_name": "user"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))

        self.assertEqual(Survey.objects.get(question="Ist das eine Testfrage?").status, "closed")

    def test_close_survey_not_as_creator(self):
        group = home.models.Group.create_and_save(name='TestGroup', picture='', description='test',
                                                  telegram_id=-987654321)
        group.save()
        user = User.objects.create(username="user")
        user.save()

        Survey.create_and_save(question="Ist das eine Testfrage?", creator=user,
                               created=datetime.datetime.now(), group=group, multiselect=True)
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.scheduler = mock.Mock(spec=rq_scheduler.scheduler.Scheduler)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/close", '
                                  '"from": {"id": 172233927, '
                                  '"first_name": "user"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))

        self.assertEqual(Survey.objects.get(question="Ist das eine Testfrage?").status, "open")

    def test_show_results_survey(self):
        group = home.models.Group.create_and_save(name='TestGroup', picture='', description='test',
                                                  telegram_id=-987654321)
        group.save()
        user = User.objects.create(username="user")
        user.save()
        Survey.create_and_save(question="Ist das eine Testfrage?", creator=user,
                               created=datetime.datetime.now(), group=group, multiselect=True)
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.scheduler = mock.Mock(spec=rq_scheduler.scheduler.Scheduler)
        handler.handle(json.loads('{"message_id": 122, "date": 1464532618, "text": "/results", '
                                  '"from": {"id": 123456789, '
                                  '"first_name": "Jon"}, "chat": {"id": -987654321, "title": "Groupsome Test", '
                                  '"type": "group"}}'))

    def test_vote_callback_multiselect_survey(self):
        user = User.objects.create(username="user")
        user.save()
        group = home.models.Group.create_and_save(name='TestGroup', picture='', description='test',
                                                  telegram_id=-987654321)
        group.save()
        group.users.add(user)
        group.save()

        survey = Survey.create_and_save(question="Ist das eine Testfrage?", creator=user,
                                        created=datetime.datetime.now(), group=group, multiselect=True)
        choice1 = Choice.create_and_save("Option 1", survey)
        choice2 = Choice.create_and_save("Option 2", survey)
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.scheduler = mock.Mock(spec=rq_scheduler.scheduler.Scheduler)
        # select Option1
        handler.handle(json.loads('{"message": {"chat": {"type": "group", "id": -987654321, "title": "TestGroup"}'
                                  ', "message_id": 680, "date": 1473504477, "text": "Jon created a survey:\n\n '
                                  'Ist das eine Testfrage?", "from": {"id": 123454321, "first_name": "JonTestBot", '
                                  '"username": "JonTestBot"}}, "data": "1-1-survey", "id": "1014688584044051627"'
                                  ', "from": {"id": 123456789, "first_name": "Jon"}}', strict=False))

        self.assertEqual(len(choice1.votes.all()), 1)
        # select Option2
        handler.handle(json.loads('{"message": {"chat": {"type": "group", "id": -987654321, "title": "TestGroup"}'
                                  ', "message_id": 680, "date": 1473504477, "text": "Jon created a survey:\n\n '
                                  'Ist das eine Testfrage?", "from": {"id": 123454321, "first_name": "JonTestBot", '
                                  '"username": "JonTestBot"}}, "data": "1-2-survey", "id": "1014688584044051627"'
                                  ', "from": {"id": 123456789, "first_name": "Jon"}}', strict=False))

        self.assertEqual(len(choice2.votes.all()), 1)
        # deselect Option1
        handler.handle(json.loads('{"message": {"chat": {"type": "group", "id": -987654321, "title": "TestGroup"}'
                                  ', "message_id": 680, "date": 1473504477, "text": "Jon created a survey:\n\n '
                                  'Ist das eine Testfrage?", "from": {"id": 123454321, "first_name": "JonTestBot", '
                                  '"username": "JonTestBot"}}, "data": "1-2-survey", "id": "1014688584044051627"'
                                  ', "from": {"id": 123456789, "first_name": "Jon"}}', strict=False))

        self.assertEqual(len(choice2.votes.all()), 0)

    def test_vote_callback_singleselect_survey(self):
        user = User.objects.create(username="user")
        user.save()
        group = home.models.Group.create_and_save(name='TestGroup', picture='', description='test',
                                                  telegram_id=-987654321)
        group.save()
        group.users.add(user)
        group.save()

        survey = Survey.create_and_save(question="Ist das eine Testfrage?", creator=user,
                                        created=datetime.datetime.now(), group=group, multiselect=False)
        choice1 = Choice.create_and_save("Option 1", survey)
        choice2 = Choice.create_and_save("Option 2", survey)
        handler = bot.MessageHandler(TestBot(), bot_user_id=0)
        handler.scheduler = mock.Mock(spec=rq_scheduler.scheduler.Scheduler)
        # select Option1
        handler.handle(json.loads('{"message": {"chat": {"type": "group", "id": -987654321, "title": "TestGroup"}'
                                  ', "message_id": 680, "date": 1473504477, "text": "Jon created a survey:\n\n '
                                  'Ist das eine Testfrage?", "from": {"id": 123454321, "first_name": "JonTestBot", '
                                  '"username": "JonTestBot"}}, "data": "1-1-survey", "id": "1014688584044051627"'
                                  ', "from": {"id": 123456789, "first_name": "Jon"}}', strict=False))

        self.assertEqual(len(choice1.votes.all()), 1)
        # select Option2
        handler.handle(json.loads('{"message": {"chat": {"type": "group", "id": -987654321, "title": "TestGroup"}'
                                  ', "message_id": 680, "date": 1473504477, "text": "Jon created a survey:\n\n '
                                  'Ist das eine Testfrage?", "from": {"id": 123454321, "first_name": "JonTestBot", '
                                  '"username": "JonTestBot"}}, "data": "1-2-survey", "id": "1014688584044051627"'
                                  ', "from": {"id": 123456789, "first_name": "Jon"}}', strict=False))

        self.assertEqual(len(choice1.votes.all()), 0)
        self.assertEqual(len(choice2.votes.all()), 1)

        # select Option2
        handler.handle(json.loads('{"message": {"chat": {"type": "group", "id": -987654321, "title": "TestGroup"}'
                                  ', "message_id": 680, "date": 1473504477, "text": "Jon created a survey:\n\n '
                                  'Ist das eine Testfrage?", "from": {"id": 123454321, "first_name": "JonTestBot", '
                                  '"username": "JonTestBot"}}, "data": "1-2-survey", "id": "1014688584044051627"'
                                  ', "from": {"id": 123456789, "first_name": "Jon"}}', strict=False))

        self.assertEqual(len(choice2.votes.all()), 1)
