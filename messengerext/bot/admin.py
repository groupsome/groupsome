from django.contrib import admin
from bot.models import TelegramLogEntry, TelegramUser

# Register your models here.
admin.site.register(TelegramLogEntry)
admin.site.register(TelegramUser)
