import telepot
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import LoginToken


class Command(BaseCommand):
    help = 'Deletes old LoginTokens'

    def handle(self, *args, **options):
        LoginToken.objects.filter(latestPoll__lt=timezone.now()-timedelta(seconds=180)).delete()
