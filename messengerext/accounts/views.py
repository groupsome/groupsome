import telepot
import datetime
import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import get_default_password_validators, password_validators_help_text_html
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.generic import View, TemplateView
from accounts.forms import EditUserForm, PasswordForm
from bot.bot import update_user_avatar
from . import models
from bot.models import TelegramUser


class AnnonymusRequiredMixin():
    authenticated_redirect_url = 'home:home'

    def check_user(self, user):
        if user.is_authenticated():
            return True
        else:
            return False

    def dispatch(self, request, *args, **kwargs):
        if self.check_user(request.user):
            return redirect(self.authenticated_redirect_url)
        return super(AnnonymusRequiredMixin, self).dispatch(
            request,
            *args,
            **kwargs)


class LoginRequiredMixin():
    not_authenticated_redirect_url = 'accounts:login'

    def check_user(self, user):
        if user.is_authenticated():
            return True
        else:
            return False

    def dispatch(self, request, *args, **kwargs):
        if not self.check_user(request.user):
            messages.error(
                request=request,
                message=_("Not logged in."))
            return redirect(self.not_authenticated_redirect_url)
        return super(LoginRequiredMixin, self).dispatch(
            request,
            *args,
            **kwargs)


class LoginView(AnnonymusRequiredMixin, View):

    def get(self, request, token_string):
        token = None

        if token_string:
            try:
                token = models.LoginToken.objects.get(token=token_string)
            except models.LoginToken.DoesNotExist:
                token = None

        if token is None:
            if "HTTP_HOST" in request.META:
                host = request.scheme+"://"+request.META["HTTP_HOST"]
            else:
                host = None

            token = models.LoginToken.create_and_save(host=host)

        return render(request, 'accounts/login.html', {
            "login_token": token, "TELEGRAM_BOT_USERNAME": settings.TELEGRAM_BOT_USERNAME,
        })

    def post(self, request, token_string):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home:home')
        else:
            messages.error(request, extra_tags='loginError', message=_('Wrong username or password'))
            return redirect('accounts:login')


class TokenView(AnnonymusRequiredMixin, View):
    def post(self, request, token):
        token = get_object_or_404(models.LoginToken, token=token)
        if token.user is not None:
            token.user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, token.user)
            token.delete()
            return JsonResponse({"redirect": True})
        else:
            token.latestPoll = timezone.now()
            token.save()
            return JsonResponse({"redirect": False})


class SettingsView(LoginRequiredMixin, TemplateView):

    template_name = 'accounts/settings.html'

    def get(self, request):
        user = request.user
        telegram_user = TelegramUser.objects.get(user=user)
        pw_form = PasswordForm(user=user)
        data = {'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'timezone': telegram_user.timezone_setting}

        user_form = EditUserForm(user=user, initial=data)
        pw_help_text = password_validators_help_text_html(password_validators=get_default_password_validators())

        return self.render_to_response({'user_form': user_form, 'pw_form': pw_form, 'pw_help_text': _(pw_help_text)})

    def post(self, request):

        if 'edit_profile' in request.POST:
            old_username = request.user.username
            user = User.objects.get(username=old_username)
            telegram_user = TelegramUser.objects.get(user=user)
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            username = request.POST.get('username')
            timezone = request.POST.get('timezone')

            data = {'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'timezone': timezone}
            user_form = EditUserForm(request.POST, user=user, initial=data)

            if (first_name == user.first_name and last_name == user.last_name and
               username == user.username and telegram_user.timezone_setting == timezone):
                messages.info(request, _('No changes detected!'))
                return HttpResponseRedirect(reverse('accounts:settings'))

            elif user_form.is_valid():
                user = User.objects.get(username=old_username)
                user.username = user_form.cleaned_data['username']
                user.first_name = user_form.cleaned_data['first_name']
                user.last_name = user_form.cleaned_data['last_name']
                telegram_user.timezone_setting = user_form.cleaned_data['timezone']
                if timezone == 'Auto':
                    telegram_user.timezone_offset = 0
                else:
                    tz = pytz.timezone(telegram_user.timezone_setting)
                    telegram_user.timezone_offset = tz.utcoffset(datetime.datetime.now()).total_seconds()/60
                user.save()
                telegram_user.save()
                messages.success(request, _('Profile successfully updated!'))
                return HttpResponseRedirect(reverse('accounts:settings'))

            pw_form = PasswordForm(user=user)
            pw_help_text = password_validators_help_text_html(password_validators=get_default_password_validators())

            return self.render_to_response({'user_form': user_form, 'pw_form': pw_form,
                                            'pw_help_text': _(pw_help_text)})

        elif 'change_password' in request.POST:
            pw_form = PasswordForm(user=request.user, data=request.POST)
            if pw_form.is_valid():

                username = request.user.username
                user = request.user
                new_password = pw_form.cleaned_data['new_password']
                user.set_password(new_password)
                user.save()
                user = authenticate(username=username, password=new_password)
                if user is not None:
                    login(request, user)
                    messages.success(request, _('Password successfully changed!'))
                    return HttpResponseRedirect(reverse('accounts:settings'))
                else:
                    messages.error(request, _('Password change failed!'))

            data = {'username': request.user.username,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name}

            user_form = EditUserForm(user=request.user, initial=data)
            pw_help_text = password_validators_help_text_html(password_validators=get_default_password_validators())
            return self.render_to_response({'user_form': user_form, 'pw_form': pw_form,
                                            'pw_help_text': _(pw_help_text)})


class SettingsUpdateAvatarView(LoginRequiredMixin, View):
    def post(self, request):
        bot = telepot.Bot(settings.TELEGRAM_TOKEN)
        update_user_avatar(request.user.telegramuser, bot)
        return HttpResponseRedirect(reverse('accounts:settings'))


class SettingsUpdateTimeZoneView(LoginRequiredMixin, View):
    def post(self, request):
        user = TelegramUser.objects.filter(user=request.user)[0]
        if user.timezone_setting != 'UTC':
            tz = pytz.timezone(user.timezone_setting)
            user.timezone_offset = tz.utcoffset(datetime.datetime.now()).total_seconds()/60
            user.save()
            return HttpResponse(status=200)
        offset = -(int(request.POST.get('off')))
        timezone = request.POST.get('tz')
        user.timezone_offset = offset
        user.timezone_setting = timezone
        user.save()
        return HttpResponse(status=200)


class LegalView(LoginRequiredMixin, View):
    not_authenticated_redirect_url = 'pages:legal_notice'

    def get(self, request):
        return render(request, 'accounts/legal.html')
