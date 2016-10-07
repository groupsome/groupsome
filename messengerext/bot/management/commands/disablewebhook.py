import telepot
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from home.bot import MessageHandler
from home.models import TelegramLogEntry


class Command(BaseCommand):
    help = 'Disables telegram webhook'

    def handle(self, *args, **options):
        if settings.TELEGRAM_TOKEN is None:
            raise CommandError("TELEGRAM_TOKEN is not defined in settings")

        bot = telepot.Bot(settings.TELEGRAM_TOKEN)
        bot.setWebhook()
