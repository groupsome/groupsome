from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from accounts.views import LoginRequiredMixin
from django.views.generic import View
from home.models import Group
from . import models
from django.http import Http404, HttpResponseRedirect, JsonResponse
from bot.bot import bot_sendMessage
from bot.models import TelegramUser
import json
from django.contrib import messages
import datetime
import telepot
from surveys.models import Choice, Vote, Survey
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.translation import ugettext as _
from .commands import show_survey_in_group, vote_for_survey, devote_for_survey, delete_all_survey_votes_of_user
from .commands import update_shown_survey_in_group


class SurveyView(LoginRequiredMixin, View):

    def _get_surveys_for_groups(self, groups):
        return models.Survey.objects.filter(group__in=groups).order_by('id').reverse()

    def _get_user_groups(self, user):
        return Group.objects.filter(users=user)

    def get(self, request, id):
        user_groups = self._get_user_groups(request.user)
        surveys = self._get_surveys_for_groups(user_groups)

        context = {
            'surveys': surveys,
            'user_groups': user_groups
        }
        return render(request, 'surveys/surveys.html', context)

    def post(self, request):
        return CreateSurveyView.post(self, request)


class DeleteSurveyView(LoginRequiredMixin, View,):
    def get(self, request, survey_id):
        user_groups = Group.objects.filter(users=request.user)
        survey = models.Survey.objects.filter(id=survey_id).filter(group__in=user_groups)
        if survey:
            survey = survey[0]
            if request.user == survey.creator or request.user in survey.group.admins.all():
                if survey.chat_id is not None and survey.msg_id is not None:
                    bot = telepot.Bot(settings.TELEGRAM_TOKEN)
                    bot.editMessageText((survey.chat_id, survey.msg_id), _("Survey was deleted."))
                for choice in survey.choices.all():
                    for vote in choice.votes.all():
                        vote.delete()
                    choice.delete()
                survey.delete()
                return JsonResponse({'message': _('Survey deleted')})
            return JsonResponse({'message': _('Only the creator or group admin can delete a survey.')})
        else:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))


class CreateSurveyView(LoginRequiredMixin, View):
    def _get_group_from_name_and_user(self, group, user):
        return Group.objects.filter(users=user, name=group)

    def get(self, request):
        user_groups = Group.objects.filter(users=request.user)
        context = {
            'user_groups': user_groups
        }

        return render(request, 'surveys/create_survey.html', context)

    def post(self, request):
        user = request.user
        group_name = request.POST.get('group')
        question = request.POST.get('question')
        creator = request.user
        created = datetime.datetime.utcnow()
        multiselect = request.POST.get('multiselect')

        group = self._get_group_from_name_and_user(group_name, user)

        if len(group) > 0:
            group = group[0]
        else:
            messages.error(request, _('No group found!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))

        if question.strip() == "":
            messages.error(request, _('Survey question can`t be empty!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))

        if multiselect is None:
            multiselect = False
        elif multiselect == 'on':
            multiselect = True

        new_survey = Survey(question=question, creator=creator, created=created, group=group, multiselect=multiselect)
        new_survey.save()

        option_counter = 1
        option = request.POST.get('option_'+str(option_counter))
        options_array = []

        while option:
            new_choice = Choice(option=option, survey=new_survey)
            new_choice.save()
            options_array.append([{'text': option, 'callback_data': str(new_survey.id) + '-' +
                                   str(new_choice.id) + '-survey'}])
            option_counter += 1
            option = request.POST.get('option_'+str(option_counter))

        inline_keyboard = {'inline_keyboard': options_array}

        bot = telepot.Bot(settings.TELEGRAM_TOKEN)

        if multiselect:
            multiselect = " " + _("(multiselect)")
        else:
            multiselect = ""

        message = bot.sendMessage(new_survey.group.telegram_id,
                                  _("{0} created a survey{2}:\n\n {1}").
                                  format(user.username, new_survey.question, multiselect),
                                  reply_markup=inline_keyboard)

        new_survey.msg_id = str(message["message_id"])
        new_survey.chat_id = str(message["chat"]["id"])
        new_survey.save()

        return HttpResponseRedirect(reverse('surveys:surveys'))


class EditSurveyView(LoginRequiredMixin, View):
    def get(self, request, survey_id):
        user_groups = Group.objects.filter(users=request.user)
        survey = models.Survey.objects.filter(id=survey_id).filter(group__in=user_groups)
        if survey:
            survey = survey[0]
        else:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))

        context = {
            'survey': survey,
        }
        if request.user == survey.creator or request.user in survey.group.admins.all():
            if request.is_ajax():
                return render(request, 'surveys/assets/edit_survey_content.html', context)

            return render(request, 'surveys/edit_survey.html', context)

        else:
            return JsonResponse({'message': _("Only the creator or group admin can edit a survey.")})

    def post(self, request, survey_id):
        user_groups = Group.objects.filter(users=request.user)
        survey = models.Survey.objects.filter(id=survey_id).filter(group__in=user_groups)
        if not survey:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))

        survey = survey[0]
        user = request.user
        if user == survey.creator or user in survey.group.admins.all():
            question = request.POST.get('question')

            if question.strip() == "":
                messages.error(request, _('Survey question can`t be empty!'))
                return HttpResponseRedirect(reverse('surveys:surveys'))

            old_question = survey.question

            survey.question = question
            survey.save()

            old_options = survey.choices.all().order_by("id")

            option_counter = 1
            option = request.POST.get('option_' + str(option_counter))
            options_array = []

            while option:
                if len(old_options) > (option_counter-1):
                    choice = old_options[option_counter - 1]
                    choice.option = option
                else:
                    choice = Choice(option=option, survey=survey)
                choice.save()
                options_array.append(option)
                option_counter += 1
                option = request.POST.get('option_' + str(option_counter))

            if len(old_options) > len(options_array):
                counter = len(options_array)

                while counter < len(old_options):
                    choice = old_options[counter]
                    for vote in choice.votes.all():
                        vote.delete()
                    choice.delete()
                    counter += 1

            bot = telepot.Bot(settings.TELEGRAM_TOKEN)

            multiselect = ""
            if survey.multiselect:
                multiselect = _("(multiselect)")

            old_question_text = ""
            if survey.question != old_question:
                old_question_text = _("{0}\n\nto:\n").format(old_question)

            message = show_survey_in_group(survey, bot, text=_("{0} changed survey{1}:\n\n{2}{3}").
                                           format(user.username, multiselect, old_question_text, survey.question))

            survey.msg_id = str(message["message_id"])
            survey.chat_id = str(message["chat"]["id"])
            survey.save()

            return HttpResponseRedirect(reverse('surveys:surveys'))
        else:
            return JsonResponse({'message': _("Only the creator or group admin can edit a survey.")})


class VoteSurveyView(LoginRequiredMixin, View):

    def get(self, request, survey_id, choice_id):
        user_groups = Group.objects.filter(users=request.user)
        survey = models.Survey.objects.filter(id=survey_id).filter(group__in=user_groups)
        if survey:
            survey = survey[0]
        else:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))

        choices = choice_id.split("-")

        while '' in choices:
            choices.remove('')
        choice_respone = ""

        if(len(choices) > 1) and not survey.multiselect:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))

        delete_all_survey_votes_of_user(survey, request.user)

        for choice_id in choices:
            choice = models.Choice.objects.filter(id=choice_id).filter(survey=survey)
            if choice:
                choice = choice[0]
            else:
                messages.error(request, _('Something went wrong!'))
                return HttpResponseRedirect(reverse('surveys:surveys'))

            vote_for_survey(survey, choice, request.user)
            choice_respone += choice.option + " - "

        if len(choices) == 0:
            choice_respone = _("Votes removed.")
        else:
            choice_respone = _('You voted for: ') + choice_respone[:-3]

        bot = telepot.Bot(settings.TELEGRAM_TOKEN)
        update_shown_survey_in_group(survey, bot)

        context = {
            'survey': survey,
        }

        html = render_to_string("surveys/surveylist.html", context, request)
        return JsonResponse({'message': choice_respone, 'html': html})


class CloseSurveyView(LoginRequiredMixin, View):

    def get(self, request, survey_id):
        user_groups = Group.objects.filter(users=request.user)
        survey = models.Survey.objects.filter(id=survey_id).filter(group__in=user_groups)
        if survey:
            survey = survey[0]
            if request.user == survey.creator or request.user in survey.group.admins.all():
                survey.status = "closed"
                survey.save()

                bot = telepot.Bot(settings.TELEGRAM_TOKEN)
                standings = ""

                choices = survey.choices.all()
                choices = sorted(choices, key=lambda x: len(x.votes.all()), reverse=True)

                for choice in choices:
                    votes = len(choice.votes.all())
                    if votes == 1:
                        standings += "\n   " + choice.option + " - " + str(votes) + " " + _("vote")
                    else:
                        standings += "\n   " + choice.option + " - " + str(votes) + " " + _("votes")

                bot.sendMessage(survey.group.telegram_id, _("{0} closed a survey.\nThe final standings of your survey"
                                                            " are:\n\n{1}").format(request.user.username,
                                                                                   survey.question) +
                                "\n " + standings)

                bot.editMessageText((survey.chat_id, survey.msg_id), _("The Survey was closed."))

                context = {
                    'survey': survey,
                }
                html = render_to_string("surveys/surveylist.html", context, request)
                return JsonResponse({'message': _('Survey closed'), 'html': html})
            else:
                return JsonResponse({'message': _("Only the creator or group admin can close a survey.")})
        else:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))


class SendResultSurveyView(LoginRequiredMixin, View):

    def post(self, request, survey_id):
        user_groups = Group.objects.filter(users=request.user)
        survey = models.Survey.objects.filter(id=survey_id).filter(group__in=user_groups)
        if survey:
            survey = survey[0]
            if request.user == survey.creator or request.user in survey.group.admins.all():

                bot = telepot.Bot(settings.TELEGRAM_TOKEN)
                standings = ""

                choices = survey.choices.all()
                choices = sorted(choices, key=lambda x: len(x.votes.all()), reverse=True)

                for choice in choices:
                    votes = len(choice.votes.all())
                    if votes == 1:
                        standings += "\n   " + choice.option + " - " + str(votes) + " " + _("vote")
                    else:
                        standings += "\n   " + choice.option + " - " + str(votes) + " " + _("votes")

                bot.sendMessage(survey.group.telegram_id, _("The final standings of your survey"
                                                            " are:\n\n{0}").format(survey.question) +
                                "\n " + standings)

                return JsonResponse({'message': _('Survey result posted')})
            else:
                return JsonResponse({'message': _("Only the creator or group admin can send results.")})
        else:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))


class ResendSurveyView(LoginRequiredMixin, View):

    def post(self, request, survey_id):
        user_groups = Group.objects.filter(users=request.user)
        survey = models.Survey.objects.filter(id=survey_id).filter(group__in=user_groups)
        if survey:
            survey = survey[0]
            if request.user == survey.creator or request.user in survey.group.admins.all():
                bot = telepot.Bot(settings.TELEGRAM_TOKEN)
                message = show_survey_in_group(survey, bot)

                survey.msg_id = str(message["message_id"])
                survey.chat_id = str(message["chat"]["id"])
                survey.save()

                return JsonResponse({'message': _('Survey resent')})
            else:
                return JsonResponse({'message': _('Only the creator or group admin can resend a survey.')})
        else:
            messages.error(request, _('Something went wrong!'))
            return HttpResponseRedirect(reverse('surveys:surveys'))
