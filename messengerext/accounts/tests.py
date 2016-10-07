from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.test.client import Client
from django.contrib.auth.models import User
from accounts.forms import EditUserForm, PasswordForm
from django.db import models
from . import models
from bot.models import TelegramUser


def create_user():
    user = User.objects.create_user('Superuser',
                                    'superuser@super.com',
                                    'Password')
    user.save()
    TelegramUser.create_and_save(user=user, telegram_id=1)
    return user


class TestLoginView(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_login_mapping_works(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEquals(response.status_code, 200)

    def test_login_shows_template(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertTemplateUsed(response=response,
                                template_name='accounts/login.html')

    def test_login(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'Superuser', 'password': 'Password'}, follow=True)
        self.assertRedirects(response, reverse('home:home'))

    def test_failed_login_with_wrong_password(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'Superuser', 'password': 'a'},
            follow=True)

        self.assertRedirects(response, reverse('accounts:login'))

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Wrong username or password')

    def test_failed_login_with_wrong_username(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'Super', 'password': 'Password'},
            follow=True)

        self.assertRedirects(response, reverse('accounts:login'))

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Wrong username or password')

    def test_authenticated_user_is_redirected_to_home_if_url_is_login(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/login', follow=True)
        self.assertRedirects(response, reverse('home:home'))

    def test_not_authenticated_user_is_redirected_to_login_if_url_is_not_home(self):
        response = self.client.get('/settings', follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_login_token_reuse(self):
        token = models.LoginToken.create_and_save()
        # kwargs doesn't work :/
        response = self.client.get(reverse('accounts:login')+"/"+token.token)
        self.assertTemplateUsed(response=response, template_name='accounts/login.html')
        self.assertEquals(token, response.context["login_token"])


class TestSettingsView(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_not_authenticated_user_is_redirected_to_login(self):
        response = self.client.get(reverse('accounts:settings'), follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_settings_mapping_works(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('accounts:settings'))
        self.assertEquals(response.status_code, 200)

    def test_settings_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('accounts:settings'))
        self.assertTemplateUsed(response=response,
                                template_name='accounts/settings.html')

    def test_change_password(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('accounts:settings'),
            {'current_password': 'Password', 'new_password': 'NewPassword', 'confirm_password': 'NewPassword',
             'change_password': 'true'},
            follow=True)

        self.assertRedirects(response, reverse('accounts:settings'))

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Password successfully changed!')
        self.assertEqual(self.user, authenticate(username='Superuser', password='NewPassword'))

    def test_failed_change_password_with_wrong_password(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('accounts:settings'),
            {'current_password': 'falsePass', 'new_password': 'newPassTest', 'confirm_password': 'newPassTest',
             'change_password': 'true'},
            follow=True)

        self.assertTemplateUsed(response=response,
                                template_name='accounts/settings.html')

        self.assertFormError(response, form='pw_form', field='current_password',
                             errors='This is not your current password. Please try again.')

    def test_failed_change_password_with_not_equal_passwords(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('accounts:settings'),
            {'current_password': 'Password', 'new_password': 'NewPassword', 'confirm_password': 'NewPassword2',
             'change_password': 'true'},
            follow=True)

        self.assertTemplateUsed(response=response,
                                template_name='accounts/settings.html')

        self.assertFormError(response, form='pw_form', field='confirm_password',
                             errors="Your passwords didn't match. Please try again.")

    def test_failed_change_password_with_old_password_equal_new_passwords(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('accounts:settings'),
            {'current_password': 'Password', 'new_password': 'Password', 'confirm_password': 'Password',
             'change_password': 'true'},
            follow=True)

        self.assertTemplateUsed(response=response,
                                template_name='accounts/settings.html')
        self.assertFormError(response, form='pw_form', field='confirm_password',
                             errors="Your new passwords can't be your old password. Please try again.")

    def test_failed_change_password_with_old_password_but_no_new_passwords(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('accounts:settings'),
            {'current_password': 'Password', 'new_password': None, 'confirm_password': None,
             'change_password': 'true'},
            follow=True)

        self.assertTemplateUsed(response=response,
                                template_name='accounts/settings.html')
        self.assertFormError(response, form='pw_form', field='confirm_password',
                             errors="This password is too short. It must contain at least 8 characters.")

    def test_edit_profile_change_first_name_last_name(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('accounts:settings'),
            {'first_name': 'Super', 'last_name': 'User', 'username': 'Superuser', 'timezone': 'UTC',
             'edit_profile': 'true'},
            follow=True)

        self.assertRedirects(response, reverse('accounts:settings'))
        user = User.objects.get(id=self.user.id)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Profile successfully updated!')
        self.assertEqual(user.first_name, 'Super')
        self.assertEqual(user.last_name, 'User')

    def test_edit_profile_change_username(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('accounts:settings'),
            {'first_name': 'Super', 'last_name': 'User', 'username': 'Superuser1', 'timezone': 'UTC',
             'edit_profile': 'true'},
            follow=True)

        self.assertRedirects(response, reverse('accounts:settings'))

        user = User.objects.get(id=self.user.id)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Profile successfully updated!')
        self.assertEqual(user.username, 'Superuser1')

    def test_failed_edit_profile_username_taken(self):
        user2 = User.objects.create_user('Superuser2', 'superuser@super.com', 'Password')
        TelegramUser.create_and_save(user=user2, telegram_id=20000)
        user2.save()

        username = self.user.username

        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('accounts:settings'),
            {'first_name': 'Super', 'last_name': 'User', 'username': 'Superuser2', 'edit_profile': 'true'},
            follow=True)

        self.assertTemplateUsed(response=response,
                                template_name='accounts/settings.html')

        user = User.objects.get(id=self.user.id)

        self.assertFormError(response, form='user_form', field='username',
                             errors="Username already taken!")
        self.assertEqual(user.username, username)


class TestLegal(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_legal_mapping_works(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('accounts:legal'))
        self.assertEquals(response.status_code, 200)

    def test_legal_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('accounts:legal'))
        self.assertTemplateUsed(response, 'accounts/legal.html')
        self.assertTemplateUsed(response, 'assets/legal_notice_text.html')

    def test_not_authenticated_user_is_redirected_to_legal_notice_if_url_is_legal(self):
        response = self.client.get('/legal', follow=True)
        self.assertRedirects(response, reverse('pages:legal_notice'))
