import telepot
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from bot.bot import MessageHandler


class Command(BaseCommand):
    help = 'Poll new messages from telegram (only for development)'

    def handle(self, *args, **options):
        if settings.TELEGRAM_TOKEN is None:
            raise CommandError("TELEGRAM_TOKEN is not defined in settings")

        bot = telepot.Bot(settings.TELEGRAM_TOKEN)
        me = bot.getMe()
        handler = MessageHandler(bot, bot_user_id=me["id"], print_incoming_messages=True, debug=True)

        self.stdout.write("start polling updates as @%s" % me["username"])
        bot.setWebhook()
        handler.message_loop()
