from django.contrib.auth.forms import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password, get_default_password_validators
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
import pytz


class PasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, required=True, label=_('Current Password'))
    new_password = forms.CharField(widget=forms.PasswordInput, required=True, label=_('New Password'))
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label=_('Confirm New Password'))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PasswordForm, self).__init__(*args, **kwargs)

    def clean_current_password(self):
        # If the user entered the current password, make sure it's right
        if self.cleaned_data['current_password'] and \
                not self.user.check_password(self.cleaned_data['current_password']):
            raise forms.ValidationError(_('This is not your current password. Please try again.'))

        return self.cleaned_data['current_password']

    def clean_confirm_password(self):
        # Make sure the new password and confirmation match
        password1 = self.cleaned_data.get('new_password')
        password2 = self.cleaned_data.get('confirm_password')
        old_password = self.cleaned_data.get('current_password')

        if password1 != password2:
            raise forms.ValidationError(_("Your passwords didn't match. Please try again."))

        if password1 == old_password:
            raise forms.ValidationError(_("Your new passwords can't be your old password. Please try again."))

        if validate_password(self.cleaned_data.get('confirm_password'), user=self.user,
                             password_validators=get_default_password_validators()) is not None:
            raise forms.ValidationError(_("Validation Error."))

        return self.cleaned_data.get('confirm_password')


class EditUserForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput, required=True, max_length=15, label=_("Username"))
    first_name = forms.CharField(widget=forms.TextInput, required=False, max_length=25, label=_('First Name'))
    last_name = forms.CharField(widget=forms.TextInput, required=False, max_length=25, label=_('Last Name'))
    tzones = [(x, x) for x in pytz.common_timezones]
    timezone = forms.ChoiceField(choices=tzones, label=_('Timezone'))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        super(EditUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'timezone')

    def clean_username(self):
        user = User.objects.get(username=self.user.username)

        if " " in self.cleaned_data['username']:
            raise forms.ValidationError(_("No whitespaces allowed in username!"))

        try:
            new_user = User.objects.get(username=self.cleaned_data['username'])
        except ObjectDoesNotExist:
            new_user = None

        if new_user is not None and new_user.id is not user.id:
            raise forms.ValidationError(_("Username already taken!"))

        return self.cleaned_data['username']
