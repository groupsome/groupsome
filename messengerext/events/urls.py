from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^$', views.EventView.as_view(), name='events'),
    url(r'^(?P<event_id>[0-9]+)/delete$', views.DeleteEventView.as_view(), name='event_delete'),
    url(r'^(?P<event_id>[0-9]+)/edit_event$', views.EditEventView.as_view(), name='edit_event'),
    url(r'^(?P<event_id>[0-9]+)/(?P<status>\w+)/?$', views.AttendEventView.as_view(), name='event_attend'),
    url(r'^create_event$', views.CreateEventView.as_view(), name='create_event'),
]
