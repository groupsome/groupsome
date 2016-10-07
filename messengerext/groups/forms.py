from django.contrib.auth.forms import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm
from home.models import Group

'''class GroupSettingsForm(ModelForm):
    class Meta:
        model = Group
        fields = ("description",)'''


class GroupSettingsForm(forms.Form):
    description = forms.CharField(widget=forms.TextInput, required=False, max_length=255, label=_('Description'))
    header = forms.ImageField(label=_("Header Image"), required=False)
    admins = forms.MultipleChoiceField(label=_("Administrators"), widget=forms.CheckboxSelectMultiple, required=False)
    everyone_is_admin = forms.BooleanField(label=_("Make everyone an administrator"), required=False)
    
    def __init__(self, group, showAdminFields, *args, **kwargs):
        super(GroupSettingsForm, self).__init__(*args, **kwargs)

        if showAdminFields:
            self.fields["admins"].choices = [(u.id, u.username) for u in group.users.all()]
        else:
            del self.fields["admins"]
            del self.fields["everyone_is_admin"]
    
    class Meta:
        model = Group
        fields = ("description", "header", "admins", "everyone_is_admin")
