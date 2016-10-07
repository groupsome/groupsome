from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.staticfiles import finders
from django.contrib.auth.models import User
from django.conf import settings
from selenium import webdriver
from home import models
from events.models import Event, Attending
from gallery.models import Album
from surveys.models import Choice, Vote, Survey
from bot.models import TelegramUser
import time
import os
import datetime
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.support.expected_conditions as EC


def create_user():
    user = User.objects.create_user('Superuser',
                                    'superuser@super.com',
                                    'Password')
    user.save()
    TelegramUser.create_and_save(user=user, telegram_id=1)
    return user


def get_webdriver(locale='en-us'):
    firefox_capabilities = DesiredCapabilities.FIREFOX
    firefox_capabilities['marionette'] = True
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("intl.accept_languages", locale)
    firefox_profile.update_preferences()
    firefox_capabilities["firefox_profile"] = firefox_profile.encoded
    driver = webdriver.Firefox(capabilities=firefox_capabilities)
    return driver


class HOSLiveServerTestCase(StaticLiveServerTestCase):

    """
    HOSLiveServerTestCase tries to provide a fix for selenium race conditions
    (wait_for) and overrides all assert methods from unittest.TestCase
    """

    DEFAULT_WAIT = 10

    def wait_for(self, function_with_assertion, timeout=DEFAULT_WAIT):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return function_with_assertion()
            except (AssertionError, WebDriverException):
                time.sleep(0.1)
        return function_with_assertion()

    def assertEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertEqual(a, b, msg))

    def assertNotEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertNotEqual(a, b, msg))

    def assertTrue(self, x, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertTrue(x, msg))

    def assertFalse(self, x, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertFalse(x, msg))

    def assertIs(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertIs(a, b, msg))

    def assertIsNot(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertIsNot(a, b, msg))

    def assertIsNone(self, x, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertIsNone(x, msg))

    def assertIsNotNone(self, x, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertIsNone(x, msg))

    def assertIn(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertIn(a, b, msg))

    def assertNotIn(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertNotIn(a, b, msg))

    def assertIsInstance(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertIsInstance(a, b, msg))

    def assertIsNotInstance(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertIsNotInstance(a, b, msg))

    def assertRaises(self, exc, fun, *args, **kwargs):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertRaises(exc, fun, *args, **kwargs))

    def assertRaises(self, exc, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertRaises(exc, msg))

    def assertRaisesRegex(self, exc, r, fun, *args, **kwargs):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertRaisesRegex(exc, r, fun, *args, **kwargs))

    def assertRaisesRegex(self, exc, r, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertRaisesRegex(exc, r, msg))

    def assertWarns(self, warn, fun, *args, **kwargs):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertWarns(warn, fun, *args, **kwargs))

    def assertWarns(self, warn, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertWarns(warn, msg))

    def assertWarnsRegex(self, warn, r, fun, *args, **kwargs):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertWarnsRegex(warn, r, fun, *args, **kwargs))

    def assertWarnsRegex(self, r, warn, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertWarnsRegex(warn, r, msg))

    def assertLogs(self, logger=None, level=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertLogs(logger, level))

    def assertAlmostEqual(self, a, b, places=7, msg=None, delta=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertAlmostEqual(a, b, places, msg, delta))

    def assertNotAlmostEqual(self, a, b, places=7, msg=None, delta=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertNotAlmostEqual(a, b, places, msg, delta))

    def assertGreater(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertGreater(a, b, msg))

    def assertGreaterEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertGreaterEqual(a, b, msg))

    def assertLess(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertLessEqual(a, b, msg))

    def assertLessEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertLessEqual(a, b, msg))

    def assertRegex(self, text, r, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertRegex(text, r, msg))

    def assertNotRegex(self, text, r, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertNotRegex(text, r, msg))

    def assertCountEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertCountEqual(a, b, msg))

    def assertMultilineEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertMultilineEqual(a, b, msg))

    def assertSequenceEqual(self, a, b, msg=None, seq_type=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertSequenceEqual(a, b, msg, set_type))

    def assertListEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertListEqual(a, b, msg))

    def assertTupleEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertTupleEqual(a, b, msg))

    def assertSetEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertSetEqual(a, b, msg))

    def assertDictEqual(self, a, b, msg=None):
        self.wait_for(lambda: super(HOSLiveServerTestCase, self).assertDictEqual(a, b, msg))
