from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^(?P<user_id>[0-9]+)/?$', views.UserprofileView.as_view(), name='user'),
]
