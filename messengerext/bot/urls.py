from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import logout

from . import views

urlpatterns = [
    url(r'^webhook/(?P<secret>[a-zA-Z0-9]+)/?$', csrf_exempt(views.WebhookView.as_view()), name='webhook'),
]
