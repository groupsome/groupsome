from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from home.models import Group
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class Survey(models.Model):
    question = models.TextField(_("Question"))
    status = models.CharField(_("Status"), max_length=6, default="open")
    creator = models.ForeignKey(User)
    created = models.DateTimeField(_("Created"))
    group = models.ForeignKey(Group)
    multiselect = models.BooleanField(_("Multiselect"), default=False)
    msg_id = models.TextField(_("Message_ID"), default=None, null=True)
    chat_id = models.TextField(_("Chat_ID"), default=None, null=True)

    @classmethod
    def create_and_save(cls, question, creator, created, group, multiselect):
        survey = cls.objects.create(question=question, creator=creator, created=created, group=group,
                                    multiselect=multiselect)
        survey.save()
        return survey

    @python_2_unicode_compatible
    def __str__(self):
        return self.question

    class Meta:
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")


class Choice(models.Model):
    option = models.TextField(_("Option"))
    survey = models.ForeignKey(Survey, related_name="choices")

    @classmethod
    def create_and_save(cls, option, survey):
        choice = cls.objects.create(option=option, survey=survey)
        choice.save()
        return choice

    @python_2_unicode_compatible
    def __str__(self):
        return self.option

    class Meta:
        verbose_name = _("Choice")
        verbose_name_plural = _("Choices")


class Vote(models.Model):
    user = models.ForeignKey(User)
    choice = models.ForeignKey(Choice, related_name="votes")

    @classmethod
    def create_and_save(cls, user, choice):
        vote = cls.objects.create(user=user, choice=choice)
        vote.save()
        return vote

    class Meta:
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")
