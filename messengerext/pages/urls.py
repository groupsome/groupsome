from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^landing/?$', views.LandingView.as_view(), name='landing'),
    url(r'^registration/?$', views.RegistrationView.as_view(), name='registration'),
    url(r'^legal_notice/?$', views.LegalNoticeView.as_view(), name='legal_notice'),
]
