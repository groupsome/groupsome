import telepot
import json
import logging
from django.views.generic import View
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.conf import settings
from .bot import MessageHandler


class WebhookView(View):
    def post(self, request, secret):
        if secret != settings.TELEGRAM_WEBHOOK_SECRET:
            raise Http404()

        if not request.META["CONTENT_TYPE"].startswith("application/json"):
            return HttpResponse("invalid content type", status=415)

        try:
            update = json.loads(request.body.decode("utf-8"))
        except:
            return HttpResponseBadRequest("invalid json")

        bot = telepot.Bot(settings.TELEGRAM_TOKEN)
        handler = MessageHandler(bot, bot_user_id=settings.TELEGRAM_TOKEN.split(":")[0])
        # TODO: handle inline_query, chosen_inline_result and callback_query

        try:
            if "message" in update:
                handler.handle(update["message"])
            elif "callback_query" in update:
                handler.handle(update["callback_query"])
        except Exception as e:
            # this is our last line of defense, just log the error ignore it and hope everything will still be fine
            # this is to ensure that a HttpResponse will be sent so that telegram will not resend the message
            logging.exception("error")
            pass

        return HttpResponse("")
