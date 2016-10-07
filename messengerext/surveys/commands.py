from bot.commands import Command, StatefulCommand
import telepot
import re
import datetime
import dateparser
import pytz
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from accounts.models import LoginToken
from .models import Survey, Choice, Vote


def show_survey_in_group(survey, bot, text=None):
    user = survey.creator
    choices = survey.choices.all().order_by('id')
    options_array = []
    multiselect = ""

    if survey.multiselect:
        multiselect = " " + _("(multiselect)")

    for choice in choices:
        options_array.append([{'text': choice.option + " - " + str(len(choice.votes.all())),
                               'callback_data': str(survey.id) + '-' +
                              str(choice.id) + '-survey'}])

    inline_keyboard = {'inline_keyboard': options_array}

    if survey.chat_id is not None and survey.msg_id is not None:
        bot.editMessageText((survey.chat_id, survey.msg_id), _("Survey posted below."))

    if text is None:
        text = _("Survey{2} from {0}:\n\n {1}").format(user.username, survey.question, multiselect)

    message = bot.sendMessage(survey.group.telegram_id, text, reply_markup=inline_keyboard)

    return message


def vote_for_survey(survey, choice, user):
    all_choices = Choice.objects.filter(survey=survey)
    vote = Vote.objects.filter(choice__in=all_choices).filter(user=user)
    if vote and not survey.multiselect:
        vote[0].choice = choice
        vote[0].save()
    else:
        vote = Vote.create_and_save(user=user, choice=choice)
        vote.save()


def devote_for_survey(survey, choice_id, user):
    choice = Choice.objects.filter(survey=survey).filter(id=choice_id)
    if choice:
        choice = choice[0]
        vote = Vote.objects.filter(choice=choice).filter(user=user)
        if vote and survey.multiselect:
            vote[0].delete()
            return True
    return False


def delete_all_survey_votes_of_user(survey, user):
    all_choices = Choice.objects.filter(survey=survey)
    votes = Vote.objects.filter(choice__in=all_choices).filter(user=user)
    for vote in votes:
        vote.delete()


def update_shown_survey_in_group(survey, bot):
    choices = survey.choices.all().order_by('id')
    options_array = []

    for choice in choices:
        options_array.append([{'text': choice.option + " - " + str(len(choice.votes.all())),
                               'callback_data': str(survey.id) + '-' +
                              str(choice.id) + '-survey'}])

    inline_keyboard = {'inline_keyboard': options_array}

    bot.editMessageReplyMarkup((survey.chat_id, survey.msg_id), reply_markup=inline_keyboard)


def handle_survey_callback(query_id, index, status, user, user_groups, bot):
    survey = Survey.objects.filter(id=index).filter(group__in=user_groups)
    if not survey:
        return bot.answerCallbackQuery(query_id, _("Survey not found."))
    
    survey = survey[0]
    if survey.status != "open":
        return bot.answerCallbackQuery(query_id, _("The survey is already closed."))
    
    choice = Choice.objects.filter(id=status)
    if not choice:
        return bot.answerCallbackQuery(query_id, _("Option not found."))
    
    choice = choice[0]
    callback_answer = ""
    if devote_for_survey(survey, status, user.user):
        callback_answer += _("Vote removed for: ") + choice.option
    else:
        vote_for_survey(survey, choice, user.user)
        callback_answer += _("You voted for: ") + choice.option

    bot.answerCallbackQuery(query_id, callback_answer)

    if survey.msg_id is not None and survey.chat_id is not None:
        update_shown_survey_in_group(survey, bot)


class ShowSurveyCommand(Command):
    def handle(self):
        survey = Survey.objects.filter(group=self.group).filter(status='open').order_by('-id')
        if survey:
            survey = survey[0]
            message = show_survey_in_group(survey, self.bot)

            survey.msg_id = str(message["message_id"])
            survey.chat_id = str(message["chat"]["id"])
            survey.save()
        else:
            self.reply(_("No Survey found in this group.\nYou can create a new survey with /newsurvey."))


class ShowResultsCommand(Command):
    def handle(self):
        survey = Survey.objects.filter(group=self.group).order_by('-id')[0]
        standings = ""

        choices = survey.choices.all()
        choices = sorted(choices, key=lambda x: len(x.votes.all()), reverse=True)

        for choice in choices:
            votes = len(choice.votes.all())
            if votes == 1:
                standings += "\n   " + choice.option + " - " + str(votes) + " " + _("vote")
            else:
                standings += "\n   " + choice.option + " - " + str(votes) + " " + _("votes")

        self.reply(_("The standings of your latest survey are:\n\n") + survey.question + "\n " + standings)


class CloseSurveyCommand(Command):
    def handle(self):
        survey = Survey.objects.filter(group=self.group).order_by('-id')[0]
        if self.user.user != survey.creator:
            return self.reply(_("Only the creator or group admin can close a survey."))

        if not survey:
            return self.reply(_("No Survey found in this group.\nYou can create a new survey with /newsurvey."))

        survey.status = "closed"
        survey.save()
        standings = ""

        choices = survey.choices.all()
        choices = sorted(choices, key=lambda x: len(x.votes.all()), reverse=True)

        for choice in choices:
            votes = len(choice.votes.all())
            if votes == 1:
                standings += "\n   " + choice.option + " - " + str(votes) + " " + _("vote")
            else:
                standings += "\n   " + choice.option + " - " + str(votes) + " " + _("votes")

        if survey.chat_id is not None and survey.msg_id is not None:
            self.bot.editMessageText((survey.chat_id, survey.msg_id), _("The Survey was closed."))

        self.reply(_("The survey was closed.\nThe final standings of your survey are:\n\n") +
                   survey.question + "\n" + standings)


class NewSurveyCommand(StatefulCommand, Command):
    key = "_state_survey"

    def handle_initial_state(self):
        self.cache.set(str(self.user.telegram_id) + "_survey", Survey(group=self.group, creator=self.user.user))
        self.cache.set(str(self.user.telegram_id) + "_survey_options", [])
        self.reply(_("Ok, let's create a survey.\nWhat question do you want to ask?"
                   "\n\nYou can type /cancel to cancel"), private=True)
        self.set_state(1)

    def handle_state(self, state):
        text = self.text
        new_survey = self.cache.get(str(self.user.telegram_id) + "_survey")
        state = self.cache.get(str(self.user.telegram_id) + "_state_survey")
        options = self.cache.get(str(self.user.telegram_id) + "_survey_options")

        if state is None or new_survey is None or options is None:
            self.cache.delete(str(self.user.telegram_id) + "_state_survey")
            self.cache.delete(str(self.user.telegram_id) + "_survey")
            self.cache.delete(str(self.user.telegram_id) + "_survey_options")
            return

        if state == 1:
            if len(text) >= 100:
                self.reply(_("The question is too long, please keep it short. (100 letters max)"
                             "\nPlease send the question again."), private=True)
                return

            new_survey.question = text
            self.reply(_("Ok good, now send me the first option please. "
                       "\n\nYou can type /cancel to cancel"), private=True)
            self.cache.set(str(self.user.telegram_id) + "_survey", new_survey)
            self.set_state(2)
        elif state == 2 and text != _("/done"):
            if len(text) >= 30:
                self.reply(_("The option is too long, please keep it short. "
                           "(30 letters max)\nPlease send the option again."), private=True)
                return

            options.append(text)
            if len(options) == 1:
                self.cache.set(str(self.user.telegram_id) + "_survey", new_survey)
                self.cache.set(str(self.user.telegram_id) + "_survey_options", options)
                self.reply(_("Ok good, now send me the second option please. "
                           "\n\nYou can type /cancel to cancel"), private=True)
                return
            else:
                self.reply(_("Ok good, if you want to add another option, send it to me."
                             "\n\nIf you have enough options send /done to finish the "
                             "survey"), private=True)
            self.cache.set(str(self.user.telegram_id) + "_survey", new_survey)
            self.cache.set(str(self.user.telegram_id) + "_survey_options", options)
        elif state == 2 and text == _("/done"):
            if len(options) < 2:
                self.reply(_("You need at least two options. "
                             "\nPlease send another option."), private=True)
                return

            self.reply(_("Alright. Do you want to be able to select multiple options "
                         "(multiselect)?"
                         "\n\nPlease send /yes or /no."), private=True)
            self.cache.set(str(self.user.telegram_id) + "_survey", new_survey)
            self.cache.set(str(self.user.telegram_id) + "_survey_options", options)
            self.set_state(3)
        elif state == 3:
            if text == _("/yes") or text == "/yes":
                new_survey.multiselect = True
            elif text == _("/no") or text == "/no":
                new_survey.multiselect = False
            else:
                return self.reply(_("Please send /yes or /no."), private=True)

            new_survey.created = datetime.datetime.now().replace(tzinfo=pytz.utc)
            new_survey.save()
            options_array = []

            for option in options:
                new_option = Choice(option=option, survey=new_survey)
                new_option.save()
                options_array.append([{'text': option + " - " + str(len(new_option.votes.all())),
                                       'callback_data': str(new_survey.id) + '-' +
                                                        str(new_option.id) + '-survey'}])

            multiselect = ""
            if new_survey.multiselect:
                multiselect = " " + _("(multiselect)")

            inline_keyboard = {'inline_keyboard': options_array, 'resize_keyboard': True, 'one_time_keyboard': True}
            message = self.bot.sendMessage(new_survey.group.telegram_id,
                                           _("{0} created a survey{2}:\n\n {1}").
                                           format(self.user.user.username, new_survey.question, multiselect),
                                           reply_markup=inline_keyboard)

            self.reply(_("Alright, I created a new survey at your group."), private=True)

            self.cache.delete(str(self.user.telegram_id) + "_survey")
            self.cache.delete(str(self.user.telegram_id) + "_survey_options")
            self.reset_state()

            new_survey.msg_id = str(message["message_id"])
            new_survey.chat_id = str(message["chat"]["id"])
            new_survey.save()
