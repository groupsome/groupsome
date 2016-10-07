from django.test import TestCase, RequestFactory
from django.core.urlresolvers import resolve, reverse
from django.http import HttpRequest
from django.test.client import Client
from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from . import models
from . import views
from groups.tests import create_user


class TestLandingPage(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_landing_mapping_works(self):
        response = self.client.get(reverse('pages:landing'))
        self.assertEquals(response.status_code, 200)

    def test_landing_shows_template(self):
        response = self.client.get(reverse('pages:landing'))
        self.assertTemplateUsed(response=response,
                                template_name='pages/landing.html')

    def test_authenticated_user_is_redirectet_to_home_if_url_is_landing(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/landing', follow=True)
        self.assertRedirects(response, reverse('home:home'))


class TestLegalNotice(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_legal_notice_mapping_works(self):
        response = self.client.get(reverse('pages:legal_notice'))
        self.assertEquals(response.status_code, 200)

    def test_legal_notice_shows_template(self):
        response = self.client.get(reverse('pages:legal_notice'))
        self.assertTemplateUsed(response, 'pages/legal_notice.html')
        self.assertTemplateUsed(response, 'assets/legal_notice_text.html')

    def test_authenticated_user_is_redirected_to_legal_if_url_is_legal_notice(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/legal_notice', follow=True)
        self.assertRedirects(response, reverse('accounts:legal'))
