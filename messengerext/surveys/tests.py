from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.test.client import Client
from surveys.models import Choice, Vote, Survey
from groups.tests import create_user, create_group
from home import models
from mock import patch
import mock
import telepot
import json
import bot


class TestSurveyModel(TestCase):
    def test_survey_create(self):
        user = create_user()
        # Group
        group = models.Group.create_and_save(name="Soccer", picture="", description="", telegram_id=21)
        survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=user,
                                        created="2016-06-04 8:00+01:00", group=group, multiselect=False)

        self.assertEquals(len(Survey.objects.all()), 1)
        self.assertEquals(survey.question, "When we meet for a soccer game?")
        self.assertEquals(survey.created, "2016-06-04 8:00+01:00")
        self.assertEquals(survey.status, "open")
        self.assertEquals(survey.group, group)

    def test_string_representation(self):
        user = create_user()
        group = models.Group.create_and_save(name="Soccer", picture="", description="", telegram_id=21)
        survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=user,
                                        created="2016-06-04 8:00+01:00", group=group, multiselect=False)

        self.assertEquals(str(survey), "When we meet for a soccer game?")


class TestChoiceModel(TestCase):
    def test_choice_create(self):
        user = create_user()
        group = models.Group.create_and_save(name="Soccer", picture="", description="", telegram_id=21)
        survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=user,
                                        created="2016-06-04 8:00+01:00", group=group, multiselect=False)
        choice = Choice.create_and_save(option="6 PM", survey=survey)

        self.assertEquals(len(Choice.objects.all()), 1)
        self.assertEquals(choice.option, "6 PM")
        self.assertEquals(choice.survey, survey)

    def test_string_representation(self):
        user = create_user()
        group = models.Group.create_and_save(name="Soccer", picture="", description="", telegram_id=21)
        survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=user,
                                        created="2016-06-04 8:00+01:00", group=group, multiselect=False)
        choice = Choice.create_and_save(option="6 PM", survey=survey)

        self.assertEquals(str(choice), "6 PM")


class TestVoteModel(TestCase):
    # Bei Vote muss die choice id immer mit '-' enden also z.B '-'(remove all) oder '23-'(singlevote)
    # oder '22-23-24' (multivote)
    def test_survey_create(self):
        user = create_user()
        group = models.Group.create_and_save(name="Soccer", picture="", description="", telegram_id=22)
        survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=user,
                                        created="2016-06-04 8:00+01:00", group=group, multiselect=False)
        choice = Choice.create_and_save(option="6 PM", survey=survey)
        vote = Vote.create_and_save(user=user, choice=choice)

        self.assertEquals(len(Vote.objects.all()), 1)
        self.assertEquals(vote.user, user)
        self.assertEquals(vote.choice, choice)
        self.assertEquals(choice.survey, survey)


def send_message(arg1, arg2, arg3, **kwargs):
    return {"text": "sometext", "from": {"id": 123456789, "first_name": "Jon"},
            "date": 1473851534, "chat": {"title": "TestGroup", "id": -987654321, "type": "group"},
            "entities": [{"offset": 0, "length": 24, "type": "bot_command"}], "message_id": 894}


def editMessageReplyMarkup(arg1, arg2, reply_markup=None):
    pass


class TestASurveysView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()

    def test_not_authenticated_user_is_redirected_to_login(self):
        response = self.client.get(reverse('surveys:surveys'), follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_surveys_mapping_works(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('surveys:surveys'))
        self.assertEquals(response.status_code, 200)

    def test_surveys_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('surveys:surveys'))
        self.assertTemplateUsed(response=response, template_name='surveys/surveys.html')


class TestCreateSurveyView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)

    def test_not_authenticated_user_is_redirected_to_login(self):
        response = self.client.get(reverse('surveys:surveys'), follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_create_survey_mapping_works(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('surveys:create_survey'))
        self.assertEquals(response.status_code, 200)

    def test_create_survey_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('surveys:create_survey'))
        self.assertTemplateUsed(response=response, template_name='surveys/create_survey.html')

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    # TODO
    def test_create_survey(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            reverse('surveys:create_survey'),
            {'question': 'Testfrage', 'group': 'Test', 'option_1': '1', 'option_2': '2'}, follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

        survey = Survey.objects.get(group=self.group)
        choices = survey.choices.all().order_by('id')

        self.assertEqual(survey.question, 'Testfrage')
        self.assertEqual(survey.group.name, 'Test')
        self.assertEqual(choices[0].option, '1')
        self.assertEqual(choices[1].option, '2')
        self.assertEqual(len(choices.all()), 2)

    def test_create_survey_empty_question_failure(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            reverse('surveys:create_survey'),
            {'question': '', 'group': 'Test', 'option_1': '1', 'option_2': '2'}, follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Survey question can`t be empty!')

    def test_create_survey_wrong_group_failure(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            reverse('surveys:create_survey'),
            {'question': 'What?', 'group': '', 'option_1': '1', 'option_2': '2'}, follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'No group found!')


class TestDeleteSurveyView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)

        self.new_survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=self.user,
                                                 created="2016-06-04 8:00+01:00", group=self.group, multiselect=False)
        self.new_survey.chat_id = "123"
        self.new_survey.msg_id = "123"

        self.new_option_1 = Choice.create_and_save("Optionstest 1", self.new_survey)
        self.new_option_2 = Choice.create_and_save("Optionstest 2", self.new_survey)

    @patch.object(telepot.Bot, 'editMessageText', send_message)
    def test_delete_survey_as_creator(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/delete', follow=True)

        self.assertEquals(len(Survey.objects.all()), 0)

    @patch.object(telepot.Bot, 'editMessageText', send_message)
    def test_delete_survey_not_as_creator(self):
        new_user = create_user(username="Sepp")
        self.group.users.add(new_user)
        self.client.force_login(user=new_user)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/delete', follow=True)

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['message'], "Only the creator or group admin can delete a survey.")


class TestEditSurveyView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)

        self.new_survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=self.user,
                                                 created="2016-06-04 8:00+01:00", group=self.group, multiselect=False)

        self.new_option_1 = Choice.create_and_save("Optionstest 1", self.new_survey)
        self.new_option_2 = Choice.create_and_save("Optionstest 2", self.new_survey)

    def test_not_authenticated_user_is_redirected_to_login(self):
        response = self.client.get('/surveys/'+str(self.new_survey.id)+'/edit_survey', follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_edit_survey_mapping_works(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/surveys/'+str(self.new_survey.id)+'/edit_survey')
        self.assertEquals(response.status_code, 200)

    def test_edit_survey_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/surveys/1/edit_survey')
        self.assertTemplateUsed(response=response, template_name='surveys/edit_survey.html')

    @patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_edit_survey_as_creator(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            '/surveys/'+str(self.new_survey.id)+'/edit_survey',
            {'question': 'When we meet for a football game?', 'group': self.group, 'option_1': '1 PM',
             'option_2': '2 PM'},
            follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

        survey = Survey.objects.get(group=self.group)

        self.assertEqual(survey.question, 'When we meet for a football game?')
        choices = survey.choices.all().order_by('id')
        self.assertEquals(choices[0].option, '1 PM')
        self.assertEquals(choices[1].option, '2 PM')

    @patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_edit_survey_not_as_creator(self):
        new_user = create_user(username="Sepp")
        self.group.users.add(new_user)
        self.client.force_login(user=new_user)

        response = self.client.post(
            '/surveys/' + str(self.new_survey.id) + '/edit_survey',
            {'question': 'When we meet for a football game?', 'group': self.group, 'option_1': '1 PM',
             'option_2': '2 PM'},
            follow=True)

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['message'], "Only the creator or group admin can edit a survey.")

    def test_edit_survey_empty_question_failure(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            '/surveys/'+str(self.new_survey.id)+'/edit_survey',
            {'question': '', 'group': 'Test', 'option_1': '1', 'option_2': '2'}, follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Survey question can`t be empty!')


class TestVoteSurveyView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)

        self.new_survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=self.user,
                                                 created="2016-06-04 8:00+01:00", group=self.group, multiselect=False)

        self.new_option_1 = Choice.create_and_save("Optionstest 1", self.new_survey)
        self.new_option_2 = Choice.create_and_save("Optionstest 2", self.new_survey)

    def test_not_authenticated_user_is_redirected_to_login(self):
        response = self.client.get(reverse('surveys:surveys'), follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

    @patch.object(telepot.Bot, 'editMessageReplyMarkup', editMessageReplyMarkup)
    def test_vote_single_select_survey(self):
        self.client.force_login(user=self.user)
        self.assertEquals(len(self.new_option_1.votes.all()), 0)
        self.assertEquals(len(self.new_option_2.votes.all()), 0)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/' + str(self.new_option_1.id) + '-/vote_survey',
            follow=True)

        self.assertEquals(len(self.new_option_1.votes.all()), 1)
        self.assertEquals(len(self.new_option_2.votes.all()), 0)

    def test_vote_multi_select_on_single_survey_failure(self):
        self.client.force_login(user=self.user)
        self.assertEquals(len(self.new_option_1.votes.all()), 0)
        self.assertEquals(len(self.new_option_2.votes.all()), 0)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/' + str(self.new_option_1.id) + '-' + str(self.new_option_2.id) +
            '-/vote_survey', follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Something went wrong!')
        self.assertEquals(len(self.new_option_1.votes.all()), 0)
        self.assertEquals(len(self.new_option_2.votes.all()), 0)

    @patch.object(telepot.Bot, 'editMessageReplyMarkup', editMessageReplyMarkup)
    def test_vote_multi_select_survey_and_delete_votes(self):
        self.client.force_login(user=self.user)
        self.new_survey.multiselect = True
        self.new_survey.save()
        self.assertEquals(len(self.new_option_1.votes.all()), 0)
        self.assertEquals(len(self.new_option_2.votes.all()), 0)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/' + str(self.new_option_1.id) + '-' + str(self.new_option_2.id) +
            '-/vote_survey', follow=True)

        self.assertEquals(len(self.new_option_1.votes.all()), 1)
        self.assertEquals(len(self.new_option_2.votes.all()), 1)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/-/vote_survey', follow=True)

        self.assertEquals(len(self.new_option_1.votes.all()), 0)
        self.assertEquals(len(self.new_option_2.votes.all()), 0)

    @patch.object(telepot.Bot, 'editMessageReplyMarkup', editMessageReplyMarkup)
    def test_change_vote(self):
        self.client.force_login(user=self.user)
        self.assertEquals(len(self.new_option_1.votes.all()), 0)
        self.assertEquals(len(self.new_option_2.votes.all()), 0)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/' + str(self.new_option_1.id) + '-/vote_survey', follow=True)

        self.assertEquals(len(self.new_option_1.votes.all()), 1)
        self.assertEquals(len(self.new_option_2.votes.all()), 0)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/' + str(self.new_option_2.id) + '-/vote_survey', follow=True)

        self.assertEquals(len(self.new_option_1.votes.all()), 0)
        self.assertEquals(len(self.new_option_2.votes.all()), 1)


class TestCloseSurveyView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)

        self.new_survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=self.user,
                                                 created="2016-06-04 8:00+01:00", group=self.group, multiselect=False)

        self.new_option_1 = Choice.create_and_save("Optionstest 1", self.new_survey)
        self.new_option_2 = Choice.create_and_save("Optionstest 2", self.new_survey)

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    @mock.patch.object(telepot.Bot, 'editMessageText', send_message)
    def test_close_survey_as_creator(self):
        self.client.force_login(user=self.user)
        self.assertEquals(self.new_survey.status, "open")

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/close', follow=True)

        self.assertEquals(Survey.objects.get(id=self.new_survey.id).status, "closed")

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['message'], "Survey closed")

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    @mock.patch.object(telepot.Bot, 'editMessageText', send_message)
    def test_close_survey_not_as_creator(self):
        new_user = create_user(username="Sepp")
        self.group.users.add(new_user)
        self.client.force_login(user=new_user)
        self.assertEquals(self.new_survey.status, "open")

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/close', follow=True)

        self.assertEquals(Survey.objects.get(id=self.new_survey.id).status, "open")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['message'], "Only the creator or group admin can close a survey.")

    def test_close_survey_user_not_in_group(self):
        new_user = create_user(username="Sepp")
        self.client.force_login(user=new_user)

        response = self.client.get(
            '/surveys/' + str(self.new_survey.id) + '/close', follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Something went wrong!')


class TestSendResultSurveyView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)

        self.new_survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=self.user,
                                                 created="2016-06-04 8:00+01:00", group=self.group, multiselect=False)
        self.new_survey.status = "closed"
        self.new_option_1 = Choice.create_and_save("Optionstest 1", self.new_survey)
        self.new_option_2 = Choice.create_and_save("Optionstest 2", self.new_survey)

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_send_result_survey_as_creator(self):
        self.client.force_login(user=self.user)
        self.assertEquals(self.new_survey.status, "closed")

        response = self.client.post(
            '/surveys/' + str(self.new_survey.id) + '/send', follow=True)

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['message'], "Survey result posted")

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_send_result_survey_not_as_creator(self):
        new_user = create_user(username="Sepp")
        self.group.users.add(new_user)
        self.client.force_login(user=new_user)
        self.assertEquals(self.new_survey.status, "closed")

        response = self.client.post(
            '/surveys/' + str(self.new_survey.id) + '/send', follow=True)

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['message'], "Only the creator or group admin can send results.")

    def test_send_result_survey_user_not_in_group(self):
        new_user = create_user(username="Sepp")
        self.client.force_login(user=new_user)

        response = self.client.post(
            '/surveys/' + str(self.new_survey.id) + '/send', follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Something went wrong!')


class TestResendSurveyView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)

        self.new_survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=self.user,
                                                 created="2016-06-04 8:00+01:00", group=self.group, multiselect=False)
        self.new_survey.status = "closed"
        self.new_option_1 = Choice.create_and_save("Optionstest 1", self.new_survey)
        self.new_option_2 = Choice.create_and_save("Optionstest 2", self.new_survey)

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_resend_survey_as_creator(self):
        self.client.force_login(user=self.user)
        self.assertEquals(self.new_survey.status, "closed")

        response = self.client.post(
            '/surveys/' + str(self.new_survey.id) + '/resend', follow=True)

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['message'], "Survey resent")

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_resend_survey_not_as_creator(self):
        new_user = create_user(username="Sepp")
        self.group.users.add(new_user)
        self.client.force_login(user=new_user)
        self.assertEquals(self.new_survey.status, "closed")

        response = self.client.post(
            '/surveys/' + str(self.new_survey.id) + '/resend', follow=True)

        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['message'], "Only the creator or group admin can resend a survey.")

    def test_resend_survey_user_not_in_group(self):
        new_user = create_user(username="Sepp")
        self.client.force_login(user=new_user)

        response = self.client.post(
            '/surveys/' + str(self.new_survey.id) + '/resend', follow=True)

        self.assertRedirects(response, reverse('surveys:surveys'))

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Something went wrong!')
