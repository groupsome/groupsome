from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^([0-9]+/?)?$', views.SurveyView.as_view(), name='surveys'),
    url(r'^(?P<survey_id>[0-9]+)/delete$', views.DeleteSurveyView.as_view(), name='survey_delete'),
    url(r'^(?P<survey_id>[0-9]+)/edit_survey$', views.EditSurveyView.as_view(), name='edit_survey'),
    # url(r'^(?P<survey_id>[0-9]+)/(?P<status>\w+)/?$', views.AttendSurveyView.as_view(), name='survey_votes'),
    url(r'^create_survey$', views.CreateSurveyView.as_view(), name='create_survey'),
    url(r'^(?P<survey_id>[0-9]+)/(?P<choice_id>([0-9]+-?)*-+)/vote_survey$', views.VoteSurveyView.as_view(),
        name='vote_survey'),
    url(r'^(?P<survey_id>[0-9]+)/close$', views.CloseSurveyView.as_view(), name='survey_close'),
    url(r'^(?P<survey_id>[0-9]+)/send$', views.SendResultSurveyView.as_view(), name='survey_send'),
    url(r'^(?P<survey_id>[0-9]+)/resend$', views.ResendSurveyView.as_view(), name='survey_resend'),
]
