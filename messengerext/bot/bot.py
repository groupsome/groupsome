import telepot
import json
import os
import datetime
import dateparser
import pytz
import re
import mimetypes
import requests
import shutil
import django_rq
import subprocess
from collections import OrderedDict
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.core.cache import caches
from .models import TelegramLogEntry, TelegramUser, Feedback
from home.models import Group, Text, Photo, File, Audio, Sticker, Link, Video
from surveys.models import Survey, Choice, Vote
from events.models import Event, Attending
from accounts.models import LoginToken
from django.utils.translation import ugettext as _
from django.utils import translation
import urllib
from accounts.commands import RegisterCommand, NewPasswordCommand, LoginCommand
from events.commands import NewEventCommand, ShowEventsCommand, DeleteEventCommand, handle_event_callback
from surveys.commands import ShowSurveyCommand, ShowResultsCommand, CloseSurveyCommand, NewSurveyCommand
from surveys.commands import handle_survey_callback
from .commands import StatefulCommand, FeedbackCommand, HelpCommand, CancelCommand


def download_file(file_id, file_path):
    bot = telepot.Bot(settings.TELEGRAM_TOKEN)
    bot.download_file(file_id, file_path)


def generate_video_thumbnail(video_path, thumb_path):
    os.system("ffmpeg -n -ss 1 -i {} -vframes 1 -q:v 2 {}".format(video_path, thumb_path))


def convert_sticker_to_png(sticker_file):
    png_file = re.sub("\.webp$", ".png", sticker_file)
    os.system("dwebp {} -o {}".format(sticker_file, png_file))


def encode_video(video_path):
    path, name = os.path.split(video_path)
    name, extension = os.path.splitext(name)

    temp_path = "{}/{}-out.mp4".format(path, name)

    os.system("ffmpeg -n -i {} -map 0:0 -map 0:a -acodec aac -ac 2 -ab 128k -strict experimental "
              "-vcodec libx264 -preset fast "
              "-level:v 4.1 -f mp4 -crf 22 -movflags faststart {}".format(video_path, temp_path))
    os.remove(video_path)
    os.rename(temp_path, "{}/{}.mp4".format(path, name))


def save_video(user, group, timestamp, message_id, video_path, video_url, thumbnail_url):
    file_info = subprocess.check_output("ffprobe -v error -select_streams v:0 -show_entries "
                                        "stream=width,height -show_entries format=duration "
                                        "-of default=noprint_wrappers=1:nokey=1 {}"
                                        .format(video_path), shell=True).splitlines()

    duration = int(float(file_info[2]))
    width = int(file_info[0])
    heigh = int(file_info[1])

    Video.create_and_save(user.user, group, timestamp, video_url, duration, width, heigh, thumbnail_url, message_id)


def encode_audio(audio_path):
    path, name = os.path.split(audio_path)
    name, extension = os.path.splitext(name)

    temp_path = "{}/{}-out.ogg".format(path, name)

    os.system("ffmpeg -i {} -map 0:0 -c:a libopus -b:a 128000 {}".format(audio_path, temp_path))
    os.remove(audio_path)
    os.rename(temp_path, "{}/{}.ogg".format(path, name))


def generate_image_thumbnail(image_path, thumb_path):
    os.system("ffmpeg -n -i {} -vf scale=1920:-1 -q:v 2 {}".format(image_path, thumb_path))


def bot_sendMessage(telegram_id, message):
    bot = telepot.Bot(settings.TELEGRAM_TOKEN)
    bot.sendMessage(telegram_id, message)


def get_open_graph_tags(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        return {}

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return {}

        og = {}

        document = BeautifulSoup(response.text, "html.parser")
        for tag in document.html.head.findAll(property=re.compile("^og:")):
            if tag.has_attr("property") and tag.has_attr("content"):
                og[tag["property"]] = tag["content"]

        if "og:title" not in og:
            for tag in document.html.head.findAll("title"):
                og["og:title"] = tag.text

        return og
    except:
        return {}


def convert_timestamp(unixtimestamp):
    return timezone.make_aware(datetime.datetime.fromtimestamp(unixtimestamp), timezone.UTC())


def is_valid_file_id(file_id):
    return re.compile("^[a-zA-Z0-9_-]+$").match(file_id)


def get_file_extension_of_file_id(bot, file_id):
    info = bot.getFile(file_id)
    unused, file_extension = os.path.splitext(info["file_path"])
    return file_extension


def get_file_extension(file_type=None, file_name=None, media_type="file"):
    if file_name is not None:
        unused, file_extension = os.path.splitext(file_name)
        if file_extension != "":
            return file_extension

    known_extensions = {
        "audio/ogg": ".ogg",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
    }

    file_extension_fixes = {
        ".mp2": ".mp3",
        ".oga": ".ogg",
    }

    if file_type is not None:
        file_extension = known_extensions.get(file_type) or mimetypes.guess_extension(file_type)
        if file_extension is not None:
            return file_extension_fixes.get(file_extension, file_extension)

    defaults = {
        "photo": ".jpg",
        "photo-thumbnail": ".jpg",
        "audio": ".ogg",
        "group-header": ".jpg",
    }

    return defaults.get(media_type, ".dat")


def get_media_path(group, media_type, file_id, file_type=None, file_name=None, file_extension=None):
    if file_extension is None:
        file_extension = get_file_extension(file_type, file_name, media_type)

    path = os.path.join(settings.MEDIA_ROOT, media_type, file_id + file_extension)

    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    return path


def get_media_url(group, media_type, file_id, file_type=None, file_name=None, file_extension=None):
    if file_extension is None:
        file_extension = get_file_extension(file_type, file_name, media_type)

    return file_id + file_extension


def get_media_path_and_url(group, media_type, file_id, file_type=None, file_name=None, file_extension=None):
    if file_extension is None:
        file_extension = get_file_extension(file_type, file_name, media_type)
    media_path = get_media_path(group, media_type, file_id, file_extension=file_extension)
    media_url = get_media_url(group, media_type, file_id, file_extension=file_extension)
    return media_path, media_url


def update_user_avatar(telegram_user, bot):
    avatars = bot.getUserProfilePhotos(telegram_user.telegram_id)

    def remove_old_avatar(telegram_user):
        if telegram_user.avatar_file_id is not None:
            old_avatar_file = get_media_path(None, "avatar", telegram_user.avatar_file_id, file_extension=".jpg")
            if os.path.isfile(old_avatar_file):
                os.remove(old_avatar_file)
            telegram_user.avatar_file_id = None

    if len(avatars["photos"]):
        avatar_id = avatars["photos"][0][1]["file_id"]  # 320x320px
        avatar_file = get_media_path(None, "avatar", avatar_id, file_extension=".jpg")

        if avatar_id == telegram_user.avatar_file_id:
            return

        if not is_valid_file_id(avatar_id):
            return

        remove_old_avatar(telegram_user)

        if not os.path.isfile(avatar_file):
            bot.download_file(avatar_id, avatar_file)

        telegram_user.avatar_file_id = avatar_id
        telegram_user.avatar_version += 1
        telegram_user.save()
    else:
        remove_old_avatar(telegram_user)
        telegram_user.avatar_version += 1
        telegram_user.save()


def get_or_create_user(msg_from, bot):
    try:
        telegram_user = TelegramUser.objects.get(telegram_id=msg_from["id"])
    except TelegramUser.DoesNotExist:
        if "username" in msg_from:
            name = msg_from["username"]
        else:
            name = msg_from["first_name"]
            if "last_name" in msg_from:
                name += " " + msg_from["last_name"]

        username = name.replace(" ", "_")
        i = 1
        while User.objects.filter(username=username).count():
            i = i + 1
            username = name.replace(" ", "_") + str(i)

        user = User.objects.create(username=username)
        user.save()
        telegram_user = TelegramUser.objects.create(user=user, telegram_id=msg_from["id"])
        telegram_user.save()

        update_user_avatar(telegram_user, bot)

    return telegram_user


def get_group_creator_and_admins(group, bot):
    # wenn eine Gruppe nicht explizit Admins definiert hat (was alle zu Admins macht)
    # liefert getChatAdminstrators trotzdem nur nur den Creator der Gruppe zurueck,
    # daher zusaetzlich getChatMember

    def get_member(user):
        return bot.getChatMember(group.telegram_id, user.telegramuser.telegram_id)

    memberships = bot.getChatAdministrators(group.telegram_id) + list(map(get_member, list(group.users.all())))

    # remove duplicates
    memberships = {v["user"]["id"]: v for v in memberships}.values()

    creator = None
    admins = []

    for membership in memberships:
        user = get_or_create_user(membership["user"], bot)
        if membership["status"] == "creator":
            creator = user.user
            admins.append(user.user)
        elif membership["status"] == "administrator":
            admins.append(user.user)

    return creator, admins


class MessageHandler:
    def __init__(self, bot, bot_user_id, print_incoming_messages=False, debug=False):
        self.bot = bot
        self.bot_user_id = bot_user_id
        self.print_incoming_messages = print_incoming_messages
        self.debug = debug
        self.cache = caches["default"]
        self.scheduler = django_rq.get_scheduler('default')

        self.private_commands = OrderedDict([
            ("/register", RegisterCommand),
            ("/newpassword", NewPasswordCommand),
            ("/help", HelpCommand),
            ("/feedback", FeedbackCommand),
            ("/start", LoginCommand),
            ("/cancel", CancelCommand),
        ])
        self.public_commands = OrderedDict([
            ("/register", RegisterCommand),
            ("/newpassword", NewPasswordCommand),
            ("/help", HelpCommand),
            ("/feedback", FeedbackCommand),
            ("/newevent", NewEventCommand),
            ("/deleteevent", DeleteEventCommand),
            ("/showevents", ShowEventsCommand),
            ("/newsurvey", NewSurveyCommand),
            ("/showsurvey", ShowSurveyCommand),
            ("/results", ShowResultsCommand),
            ("/close", CloseSurveyCommand),
        ])

        # not in use, but for automatic translations needed
        self.translations = [
            _("/register"),
            _("/newpassword"),
            _("/help"),
            _("/feedback"),
            _("/start"),
            _("/cancel"),
            _("/newevent"),
            _("/deleteevent"),
            _("/showevents"),
            _("/newsurvey"),
            _("/showsurvey"),
            _("/results"),
            _("/close"),
            _("/done"),
        ]

    def handle_command(self, commands, user, msg, group):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == "text":
            cmd_string = msg["text"].split(" ")[0]
            cmd_string = re.sub(r"@[^\@]+$", "", cmd_string)

            for command, klass in commands.items():
                if cmd_string == _(command) or cmd_string == command:
                    cmd = klass(user=user, group=group, msg=msg, bot=self.bot, cache=self.cache, message_handler=self)
                    if cmd.required_role is not None and group is not None:
                        if not self.require_role(user, group, cmd.required_role):
                            continue
                    if not cmd.validate():
                        continue
                    cmd.handle()
                    return True

            all_commands = set(self.private_commands.values()) | set(self.public_commands.values())
            for klass in all_commands:
                if issubclass(klass, StatefulCommand):
                    state = self.cache.get(str(user.telegram_id) + klass.key)
                    if state is not None:
                        cmd = klass(user=user, group=group, msg=msg, bot=self.bot, cache=self.cache,
                                    message_handler=self)
                        cmd.handle_state(state)
                        return True

        return False

    def handle_private_command(self, user, msg):
        return self.handle_command(self.private_commands, user, msg, None)

    def handle_public_command(self, user, group, msg):
        return self.handle_command(self.public_commands, user, msg, group)

    def get_public_keyboard(self):
        buttons = [{"text": _(cmd)} for cmd in self.public_commands.keys()
                   if not self.public_commands[cmd].hide_in_keyboard]
        return {
            "keyboard": [buttons[i:i+2] for i in range(0, len(buttons), 2)],
            "resize_keyboard": True,
        }

    def get_private_keyboard(self):
        buttons = [{"text": _(cmd)} for cmd in self.private_commands.keys()
                   if not self.private_commands[cmd].hide_in_keyboard]
        return {
            "keyboard": [buttons[i:i+2] for i in range(0, len(buttons), 2)],
            "resize_keyboard": True,
            "one_time_keyboard": True,
            "selective": True,
        }

    def handle(self, msg):
        if self.print_incoming_messages:
            print(json.dumps(msg))

        translation.activate(get_or_create_user(msg["from"], self.bot).language)

        if telepot.flavor(msg) is 'callback_query':
            query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
            user = get_or_create_user(msg["from"], self.bot)
            data = msg["data"]
            index = int(data.split('-')[0])
            status = data.split('-')[1]
            callback_type = data.split('-')[2]

            if msg["message"]["chat"]:
                group = self.get_or_create_group(msg["message"]["chat"])

                if user.user not in group.users.all() and user.telegram_id != self.bot_user_id:
                    group.users.add(user.user)

            user_groups = Group.objects.filter(users=user.user)

            if callback_type == "event":
                handle_event_callback(query_id, index, status, user, user_groups, self.bot)
            elif callback_type == "survey":
                handle_survey_callback(query_id, index, status, user, user_groups, self.bot)
            return

        content_type, chat_type, chat_id = telepot.glance(msg)

        TelegramLogEntry.create_and_save(json.dumps(msg))

        if chat_type == "private":
            user = get_or_create_user(msg["from"], self.bot)
            self.handle_private_message(user, msg)
        elif chat_type == "group":
            group = self.get_or_create_group(msg["chat"])
            user = get_or_create_user(msg["from"], self.bot)

            if user.user not in group.users.all() and user.telegram_id != self.bot_user_id:
                group.users.add(user.user)

            if content_type == "text":
                self.handle_group_text(group, user, msg, chat_id)
            elif content_type == "photo":
                self.handle_group_photo(group, user, msg, msg["photo"][-1], chat_id)
            elif content_type == "document":
                self.handle_group_document(group, user, msg, chat_id)
            elif content_type == "audio":
                self.handle_group_audio(group, user, msg, chat_id)
            elif content_type == "voice":
                self.handle_group_voice(group, user, msg, chat_id)
            elif content_type == "video":
                self.handle_group_video(group, user, msg, msg["video"], chat_id)
            elif content_type == "sticker":
                self.handle_group_sticker(group, user, msg, chat_id)
            elif content_type == "new_chat_member":
                if msg["new_chat_member"]["id"] != self.bot_user_id:
                    target = get_or_create_user(msg["new_chat_member"], self.bot)
                    self.handle_group_join(group, target, msg)
            elif content_type == "left_chat_member":
                if msg["left_chat_member"]["id"] != self.bot_user_id:
                    target = get_or_create_user(msg["left_chat_member"], self.bot)
                    self.handle_group_leave(group, target, msg)
            elif content_type == "new_chat_photo":
                self.handle_group_new_chat_photo(group, msg["new_chat_photo"], chat_id)

    def require_role(self, user, group, role):
        if not group.has_role(user, role):
            self.bot.sendMessage(user.telegram_id, _("You don't have permission to do that"))
            return False

        return True

    def get_or_create_group(self, chat):
        try:
            group = Group.objects.get(telegram_id=chat["id"])
        except Group.DoesNotExist:
            group = Group.objects.create(name=chat["title"], telegram_id=chat["id"])
            group.save()

            creator, admins = get_group_creator_and_admins(group, self.bot)
            group.creator = creator
            group.admins.set(admins)
            group.save()

        return group

    def handle_private_message(self, user, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if self.handle_private_command(user, msg):
            return

        if content_type == "text":
            cmd_string = msg["text"].split(" ")[0]
            if _(cmd_string) in self.public_commands or cmd_string in self.public_commands:
                self.bot.sendMessage(chat_id, _(
                    "You can only use this command in a group chat! Type /help for more information"))
            else:
                self.bot.sendMessage(chat_id, _("Type /help to see all available commands\n Type /register if you want"
                                                " to register for groupso.me"),
                                     reply_markup=self.get_private_keyboard())

    def handle_group_text(self, group, user, msg, chat_id):
        if self.handle_public_command(user, group, msg):
            return

        text = Text.create_and_save(user=user.user, group=group, content=msg["text"],
                                    timestamp=convert_timestamp(msg["date"]), telegram_id=msg["message_id"])

        for entity in msg.get("entities", []):
            if entity["type"] == "url":
                url = msg["text"][entity["offset"]:entity["offset"] + entity["length"]]
                if not re.compile("^[a-z]+://").match(url):
                    url = "http://" + url
                og = get_open_graph_tags(url=url)

                link_preview_url = None
                image_url = og.get("og:image")
                # TODO  if og.get("og:image:secure_url") ..
                if image_url:
                    # some sites like youtube deliver URLs without leading http or https '//s.ytimg..
                    if image_url.startswith('//'):
                        image_url = 'http:' + image_url

                    try:
                        local_file, headers = urllib.request.urlretrieve(image_url)
                        link_preview_path, link_preview_url = get_media_path_and_url(group, "link-preview", file_id=str(
                            msg["message_id"]), file_type=headers["Content-Type"])
                        shutil.move(local_file, link_preview_path)
                        os.chmod(link_preview_path, 0o644)
                    except:
                        pass

                title = og.get("og:title")
                if title is None:
                    title = url

                link = Link.create_and_save(user=user.user, group=group, timestamp=convert_timestamp(msg["date"]),
                                            url=url, telegram_id=msg["message_id"],
                                            title=title, description=og.get("og:description"),
                                            file=link_preview_url)

        if self.debug:
            self.bot.sendMessage(chat_id, "This message was Recorded")

    def handle_group_photo(self, group, user, msg, photo, chat_id):
        file_id = photo["file_id"]
        photo_file, photo_url = get_media_path_and_url(group, "photo", file_id,
                                                       file_extension=get_file_extension_of_file_id(self.bot, file_id))

        thumbnail_file, thumbnail_url = get_media_path_and_url(group, "photo-thumbnail", file_id, file_name=".jpg")

        if not self.validate_file_id(file_id):
            return

        download_job = None
        if not os.path.isfile(photo_file):
            download_job = django_rq.enqueue(download_file, file_id, photo_file)

        thumbnail_job = django_rq.enqueue(generate_image_thumbnail, photo_file, thumbnail_file, depends_on=download_job)
        job = django_rq.enqueue(Photo.create_and_save, user.user, group, convert_timestamp(msg["date"]), photo_url,
                                thumbnail_url, msg["message_id"], depends_on=thumbnail_job)

        if self.debug:
            self.bot.sendMessage(chat_id, "This message was Recorded")

    def handle_group_document(self, group, user, msg, chat_id):
        try:
            doc = msg["document"]
            file_id = doc["file_id"]
            file_name = doc["file_name"]
            file_type = doc["mime_type"]
            timestamp = msg["date"]
        except:
            return

        if not self.validate_file_id(file_id):
            return

        if file_type.startswith("image/"):
            self.handle_group_photo(group, user, msg, doc, chat_id)

        elif file_type.startswith("video/"):
            self.handle_group_video(group, user, msg, doc, chat_id)

        else:
            file_location, file_url = get_media_path_and_url(group, "file", file_id, file_type=file_type,
                                                             file_name=file_name)

            download_job = None
            if not os.path.isfile(file_location):
                download_job = django_rq.enqueue(download_file, file_id, file_location)

            save_job = django_rq.enqueue(File.create_and_save, user.user, group, convert_timestamp(timestamp), file_url,
                                         file_type, file_name, msg["message_id"], depends_on=download_job)

        if self.debug:
            self.bot.sendMessage(chat_id, "This message was Recorded")

    def handle_group_audio(self, group, user, msg, chat_id):
        audio = msg["audio"]
        audio_id = audio["file_id"]
        audio_file, audio_url = get_media_path_and_url(group, "audio", audio_id, file_type=audio["mime_type"])
        # always ogg after conversion
        audio_file_new, audio_url = get_media_path_and_url(group, "audio", audio_id, file_type=".ogg")

        if not self.validate_file_id(audio_id):
            return

        convert_job = None
        if not os.path.isfile(audio_file_new):
            download_job = django_rq.enqueue(download_file, audio_id, audio_file)
            convert_job = django_rq.enqueue(encode_audio, audio_file, depends_on=download_job)

        save_job = django_rq.enqueue(Audio.create_and_save, user.user, group, convert_timestamp(msg["date"]), audio_url,
                                     audio["duration"], audio.get("title"), audio.get("performer"), msg["message_id"],
                                     depends_on=convert_job)

        if self.debug:
            self.bot.sendMessage(chat_id, "This message was Recorded")

    def handle_group_voice(self, group, user, msg, chat_id):
        audio = msg["voice"]
        audio_id = audio["file_id"]
        audio_file, audio_url = get_media_path_and_url(group, "audio", audio_id, file_type=audio["mime_type"])

        if not self.validate_file_id(audio_id):
            return

        download_job = None
        if not os.path.isfile(audio_file):
            download_job = django_rq.enqueue(download_file, audio_id, audio_file)

        save_job = django_rq.enqueue(Audio.create_and_save, user.user, group, convert_timestamp(msg["date"]), audio_url,
                                     audio["duration"], title=None, interpret=None, telegram_id=msg["message_id"],
                                     depends_on=download_job)

        if self.debug:
            self.bot.sendMessage(chat_id, "This message was Recorded")

    def handle_group_video(self, group, user, msg, video, chat_id):
        file_id = video["file_id"]
        video_file, video_url = get_media_path_and_url(group, "video", file_id,
                                                       file_extension=get_file_extension_of_file_id(self.bot, file_id))

        # file is allways mp4 after converison
        video_file_new, video_url = get_media_path_and_url(group, "video", file_id, file_extension=".mp4")

        thumbnail_file, thumbnail_url = get_media_path_and_url(group, "video-thumbnail", file_id, file_extension=".jpg")

        if not self.validate_file_id(file_id):
            return

        convert_job = None
        if not os.path.isfile(video_file_new):
            download_job = django_rq.enqueue(download_file, file_id, video_file)
            thumbnail_job = django_rq.enqueue(generate_video_thumbnail, video_file, thumbnail_file,
                                              depends_on=download_job)
            convert_job = django_rq.enqueue(encode_video, video_file, depends_on=thumbnail_job)

        save_job = django_rq.enqueue(save_video, user, group, convert_timestamp(msg["date"]), msg["message_id"],
                                     video_file_new, video_url, thumbnail_url, depends_on=convert_job)

        if self.debug:
            self.bot.sendMessage(chat_id, "This message was Recorded")

    def handle_group_sticker(self, group, user, msg, chat_id):
        sticker_id = msg["sticker"]["file_id"]
        sticker_file, sticker_url = get_media_path_and_url(group, "sticker", sticker_id, file_extension=".webp")

        if not self.validate_file_id(sticker_id):
            return

        dependency = None
        if not os.path.isfile(sticker_file):
            download_dependency = django_rq.enqueue(download_file, sticker_id, sticker_file)
            dependency = django_rq.enqueue(convert_sticker_to_png, sticker_file, depends_on=download_dependency)

        save_job = django_rq.enqueue(Sticker.create_and_save, user.user, group, convert_timestamp(msg["date"]),
                                     sticker_url, msg["message_id"], depends_on=dependency)

        if self.debug:
            self.bot.sendMessage(chat_id, "This message was Recorded")

    def handle_group_join(self, group, user, msg):
        group.users.add(user.user)

    def handle_group_leave(self, group, user, msg):
        group.users.remove(user.user)

    def handle_group_new_chat_photo(self, group, chat_photo, chat_id):
        def remove_old_chat_photo(group):
            if group.chat_photo_file_id is not None:
                old_chat_photo = get_media_path(None, "chat-photo", group.chat_photo_file_id, file_extension=".jpg")
                if os.path.isfile(old_chat_photo):
                    os.remove(old_chat_photo)
                group.chat_photo_file_id = None

        file_id = chat_photo[1]["file_id"]
        photo_file = get_media_path(group, "chat-photo", file_id, file_extension=".jpg")

        if not self.validate_file_id(file_id):
            return

        if file_id == group.chat_photo_file_id:
            return

        remove_old_chat_photo(group)

        if not os.path.isfile(photo_file):
            self.bot.download_file(file_id, photo_file)
            group.chat_photo_file_id = file_id
            group.save()

        if self.debug:
            self.bot.sendMessage(chat_id, "This message was Recorded(changed grouppicture)")

    def message_loop(self):
        self.bot.message_loop(self.handle, relax=1, run_forever=True)

    def validate_file_id(self, file_id):
        if not is_valid_file_id(file_id):
            print("invalid file_id %s" % file_id)
            return False
        return True
