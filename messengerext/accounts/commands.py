from bot.commands import Command
import telepot
import re
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from accounts.models import LoginToken


def create_user_login(user):
    password = User.objects.make_random_password()
    user.user.set_password(password)
    user.user.save()
    return password


class RegisterCommand(Command):
    def handle(self):
        password = create_user_login(self.user)
        self.reply(_("Username: {0}\nPassword:").format(self.user.user.username), private=True)
        self.reply(str(password), private=True)
        self.reply(_("Remember to change your password after you login on www.groupso.me"), private=True)


class NewPasswordCommand(Command):
    def handle(self):
        password = create_user_login(self.user)
        self.reply(_("Your new password:"), private=True)
        self.reply(str(password), private=True)
        self.reply(_("Remember to change your password after you login"), private=True)


class LoginCommand(Command):
    hide_in_keyboard = True
    
    def validate(self):
        return self.text.startswith("/start login-")
    
    def handle(self):
        pattern = re.compile(r"^/start login-(?P<token>[a-zA-Z0-9]+)(?P<scan>-scan)?\s*$")
        match = pattern.search(self.text)
        try:
            token = LoginToken.objects.get(token=match.group("token"))
        except LoginToken.DoesNotExist:
            token = None

        if token and token.user is None:
            token.user = self.user.user
            token.save()
            self.reply(_("You're logged in now."), private=True)

            if token.host is not None and not match.group("scan"):
                self.reply("back to " + token.host + "/login/" + token.token, private=True)
