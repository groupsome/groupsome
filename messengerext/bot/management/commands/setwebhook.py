import telepot
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from bot.bot import MessageHandler
from bot.models import TelegramLogEntry


class Command(BaseCommand):
    help = 'Sets telegram webhook'

    def add_arguments(self, parser):
        parser.add_argument("hostname", type=str)

    def handle(self, *args, **options):
        if settings.TELEGRAM_TOKEN is None:
            raise CommandError("TELEGRAM_TOKEN is not defined in settings")

        bot = telepot.Bot(settings.TELEGRAM_TOKEN)
        bot.setWebhook("https://"+options["hostname"]+"/bot/webhook/"+settings.TELEGRAM_WEBHOOK_SECRET)
