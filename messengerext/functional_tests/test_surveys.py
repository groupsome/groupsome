from .context import *
from home import models
from surveys.models import Survey, Choice
import mock
import telepot
from mock import patch


def send_message(arg1, arg2, arg3, **kwargs):
    return {"text": "sometext", "from": {"id": 123456789, "first_name": "Jon"},
            "date": 1473851534, "chat": {"title": "TestGroup", "id": -987654321, "type": "group"},
            "entities": [{"offset": 0, "length": 24, "type": "bot_command"}], "message_id": 894}


def editMessageReplyMarkup(arg1, arg2, reply_markup=None):
    pass


class SurveyTestCase(HOSLiveServerTestCase):
    def create_content(self):
        user = create_user()
        self.group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                                  telegram_id=25)
        self.group.users.add(user)
        return user

    def create_survey(self):
        time = datetime.datetime.now()
        new_survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=self.user,
                                            created=time, group=self.group, multiselect=False)

        new_option_1 = Choice.create_and_save("Optionstest 1", new_survey)
        new_option_2 = Choice.create_and_save("Optionstest 2", new_survey)

    def create_survey_multiselect(self):
        time = datetime.datetime.now()
        new_survey = Survey.create_and_save(question="When we meet for a soccer game?", creator=self.user,
                                            created=time, group=self.group, multiselect=True)

        new_option_1 = Choice.create_and_save("Optionstest 1", new_survey)
        new_option_2 = Choice.create_and_save("Optionstest 2", new_survey)
        new_option_3 = Choice.create_and_save("Optionstest 3", new_survey)

    def setUp(self):
        self.browser = get_webdriver()
        self.browser.implicitly_wait(10)
        self.user = self.create_content()

    def tearDown(self):
        for method, error in self._outcome.errors:
            if error:
                test_method_name = self._testMethodName
                now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.browser.save_screenshot(
                    os.getcwd() + '/functional_tests/screenshots/' + test_method_name + "-" + now + ".png")
        self.browser.quit()

    def force_login(self):
        self.browser.get(self.live_server_url + '/login')
        wait = WebDriverWait(self.browser, 10)
        wait.until(EC.visibility_of_element_located((By.ID, "id_login")))
        login_inputbox = self.browser.find_element_by_id('id_login')
        login_inputbox.send_keys('Superuser')
        wait.until(EC.visibility_of_element_located((By.ID, "id_password")))
        password_inputbox = self.browser.find_element_by_id('id_password')
        password_inputbox.send_keys('Password')
        password_inputbox.send_keys(Keys.ENTER)

    def test_can_access_surveys(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        survey_link = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Surveys")))
        survey_link.send_keys(Keys.RETURN)
        # wait.until(EC.title_contains("Surveys"))
        el = driver.find_element_by_id('surveylist')
        self.assertTrue(el.is_displayed())
        self.assertTrue(el.text.__contains__("No surveys in your groups! Take your phone and create a /newsurvey"))

    def test_radio_button_works(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        button = driver.find_element_by_id('id_closed')
        self.assertTrue(self.browser.find_element_by_id('surveylist').is_displayed())
        self.browser.implicitly_wait(10)
        button.click()
        self.assertTrue(self.browser.find_element_by_id('surveylist').is_displayed())
        button = driver.find_element_by_id('id_open')
        self.browser.implicitly_wait(10)
        button.click()
        self.assertTrue(self.browser.find_element_by_id('surveylist').is_displayed())

    def test_content_shown_in_surveylist(self):
        for i in range(0, 2):
            time = datetime.datetime.now()
            new_survey = Survey.create_and_save(question=str(i), creator=self.user, created=time,
                                                group=self.group, multiselect=False)

            new_option_1 = Choice.create_and_save("Optiontest 1", new_survey)
            new_option_2 = Choice.create_and_save("Optiontest 2", new_survey)

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        elems = driver.find_elements_by_class_name('open-survey')
        self.assertTrue(len(elems) == 2)
        for i in range(0, 2):
            self.assertTrue(elems[i].text.__contains__(str(i)))

    def test_survey_deleting(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        self.assertTrue(len(driver.find_elements_by_class_name('survey-list')) == 1)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-options>button')))
        driver.find_element_by_css_selector(".survey-options>button").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-delete-btn')))
        driver.find_element_by_class_name("survey-delete-btn").click()
        wait.until(EC.alert_is_present())
        alert = driver.switch_to_alert()
        alert.accept()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.survey-list')))
        self.assertTrue(len(driver.find_elements_by_class_name('survey-list')) == 0)

    def test_choices_are_shown(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        self.assertTrue(len(driver.find_elements_by_class_name('choice')) == 2)

    @patch.object(telepot.Bot, 'editMessageReplyMarkup', editMessageReplyMarkup)
    def test_survey_vote(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        # vote
        choice_buttons = driver.find_elements_by_class_name("tasks-list-mark")
        choice_buttons[0].click()
        driver.find_element_by_class_name("survey-vote-btn").click()
        # change button and results shown
        self.assertTrue(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        self.assertTrue(len(driver.find_elements_by_class_name('show-voted-users')) == 2)

    @patch.object(telepot.Bot, 'editMessageReplyMarkup', editMessageReplyMarkup)
    def test_survey_vote_multiselect(self):
        self.create_survey_multiselect()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        # first vote
        choice_buttons = driver.find_elements_by_class_name("tasks-list-mark")
        choice_buttons[0].click()
        choice_buttons[2].click()
        driver.find_element_by_class_name("survey-vote-btn").click()
        # change button click
        self.assertTrue(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        driver.find_element_by_class_name("survey-change-vote-btn").click()
        # choices shown
        self.assertTrue(len(driver.find_elements_by_class_name('choice')) == 3)
        # no change button, vote and cancel button
        self.assertFalse(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        self.assertTrue(len(driver.find_elements_by_class_name('survey-vote-btn')) == 1)
        self.assertTrue(len(driver.find_elements_by_class_name('survey-cancel-vote-btn')) == 1)
        # # cancel klick
        driver.find_element_by_class_name("survey-cancel-vote-btn").click()
        # no vote cancel button, change button and results
        self.assertFalse(self.browser.find_element_by_class_name('survey-vote-btn').is_displayed())
        self.assertFalse(self.browser.find_element_by_class_name('survey-cancel-vote-btn').is_displayed())
        self.assertTrue(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        self.assertTrue(len(driver.find_elements_by_class_name('show-voted-users')) == 3)

    @patch.object(telepot.Bot, 'editMessageReplyMarkup', editMessageReplyMarkup)
    def test_survey_change_vote_save(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        # first vote
        choice_buttons = driver.find_elements_by_class_name("tasks-list-mark")
        choice_buttons[0].click()
        driver.find_element_by_class_name("survey-vote-btn").click()
        # change button click
        self.assertTrue(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        driver.find_element_by_class_name("survey-change-vote-btn").click()
        # choices shown
        self.assertTrue(len(driver.find_elements_by_class_name('choice')) == 2)
        # no change button, vote and cancel button
        self.assertFalse(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        self.assertTrue(len(driver.find_elements_by_class_name('survey-vote-btn')) == 1)
        self.assertTrue(len(driver.find_elements_by_class_name('survey-cancel-vote-btn')) == 1)
        # other choice, vote button click
        choice_buttons = driver.find_elements_by_class_name("tasks-list-mark")
        choice_buttons[1].click()
        driver.find_element_by_class_name("survey-vote-btn").click()
        # results shown
        self.assertTrue(len(driver.find_elements_by_class_name('show-voted-users')) == 2)

    @patch.object(telepot.Bot, 'editMessageReplyMarkup', editMessageReplyMarkup)
    def test_survey_change_vote_cancel(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        # first vote
        choice_buttons = driver.find_elements_by_class_name("tasks-list-mark")
        choice_buttons[0].click()
        driver.find_element_by_class_name("survey-vote-btn").click()
        # change button click
        self.assertTrue(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        driver.find_element_by_class_name("survey-change-vote-btn").click()
        # choices shown
        self.assertTrue(len(driver.find_elements_by_class_name('choice')) == 2)
        # no change button, vote and cancel button
        self.assertFalse(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        self.assertTrue(len(driver.find_elements_by_class_name('survey-vote-btn')) == 1)
        self.assertTrue(len(driver.find_elements_by_class_name('survey-cancel-vote-btn')) == 1)
        # other choice, cancel button click
        choice_buttons = driver.find_elements_by_class_name("tasks-list-mark")
        choice_buttons[1].click()
        driver.find_element_by_class_name("survey-cancel-vote-btn").click()
        # no vote cancel button, change button and results
        self.assertFalse(self.browser.find_element_by_class_name('survey-vote-btn').is_displayed())
        self.assertFalse(self.browser.find_element_by_class_name('survey-cancel-vote-btn').is_displayed())
        self.assertTrue(self.browser.find_element_by_class_name('survey-change-vote-btn').is_displayed())
        self.assertTrue(len(driver.find_elements_by_class_name('show-voted-users')) == 2)

    @patch.object(telepot.Bot, 'editMessageReplyMarkup', editMessageReplyMarkup)
    def test_show_voted_users(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        # vote
        driver.find_element_by_class_name("tasks-list-mark").click()
        driver.find_element_by_class_name("survey-vote-btn").click()
        # voted users shown
        driver.find_element_by_class_name("has-votes").click()
        self.assertTrue(self.browser.find_element_by_class_name('user-pics').is_displayed())

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    @mock.patch.object(telepot.Bot, 'editMessageText', send_message)
    def test_survey_close(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        # options -> close
        self.assertTrue(len(driver.find_elements_by_class_name('open-survey')) == 1)
        self.assertTrue(len(driver.find_elements_by_class_name('closed-survey')) == 0)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-options>button')))
        driver.find_element_by_css_selector(".survey-options>button").click()
        driver.find_element_by_class_name("survey-close-btn").click()
        wait.until(EC.alert_is_present())
        alert = driver.switch_to_alert()
        alert.accept()
        # closed, results
        self.assertTrue(len(driver.find_elements_by_class_name('closed-survey')) == 1)
        self.assertTrue(len(driver.find_elements_by_class_name('open-survey')) == 0)

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_survey_create(self):
        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        wait.until(EC.presence_of_element_located((By.ID, 'new-Survey-lg')))
        self.assertTrue(len(driver.find_elements_by_class_name('survey-list')) == 0)
        driver.find_element_by_id("new-Survey-lg").click()
        wait.until(EC.visibility_of_element_located((By.ID, "question")))
        el = self.browser.find_element_by_id('question')
        el.send_keys('question')

        wait.until(EC.visibility_of_element_located((By.ID, "option_1")))
        loc = self.browser.find_element_by_id('option_1')
        loc.send_keys('option_1')

        wait.until(EC.visibility_of_element_located((By.ID, "option_2")))
        loc = self.browser.find_element_by_id('option_2')
        loc.send_keys('option_2')

        wait.until(EC.visibility_of_element_located((By.ID, "create_survey")))
        submit = self.browser.find_element_by_id('create_survey')
        submit.send_keys(Keys.ENTER)

        self.assertTrue(len(driver.find_elements_by_class_name('survey-list')) == 1)

    # @patch.object(telepot.Bot, 'sendMessage', send_message)
    # def test_survey_edit(self):
    #     self.create_survey()
    #
    #     driver = self.browser
    #     self.force_login()
    #     wait = WebDriverWait(driver, 10)
    #     wait.until_not(EC.title_contains('Login'))
    #     driver.get(self.live_server_url + '/surveys/')
    #     # wait.until(EC.title_contains("Surveys"))
    #     self.assertTrue(len(driver.find_elements_by_class_name('open-survey')) == 1)
    #     wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-options>button')))
    #     driver.find_element_by_css_selector(".survey-options>button").click()
    #     wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-edit-btn')))
    #     driver.find_element_by_class_name("survey-edit-btn").click()
    #     wait.until(EC.visibility_of_element_located((By.ID, "question_edit")))
    #     el = self.browser.find_element_by_id('question_edit')
    #     el.send_keys('question_edit')
    #
    #     wait.until(EC.visibility_of_element_located((By.ID, "option_1_edit")))
    #     loc = self.browser.find_element_by_id('option_1_edit')
    #     loc.send_keys('option_1_edit')
    #
    #     wait.until(EC.visibility_of_element_located((By.ID, "option_2_edit")))
    #     loc = self.browser.find_element_by_id('option_2_edit')
    #     loc.send_keys('option_2_edit')
    #
    #     wait.until(EC.visibility_of_element_located((By.ID, "survey-edit-save")))
    #     submit = self.browser.find_element_by_id('survey-edit-save')
    #     submit.send_keys(Keys.ENTER)
    #
    #     self.assertTrue(len(driver.find_elements_by_class_name('survey-list')) == 1)

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_survey_resend(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        self.assertTrue(len(driver.find_elements_by_class_name('open-survey')) == 1)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-options>button')))
        driver.find_element_by_css_selector(".survey-options>button").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-resend-btn')))
        driver.find_element_by_class_name("survey-resend-btn").click()
        self.assertTrue(len(driver.find_elements_by_class_name('survey-list')) == 1)

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    @mock.patch.object(telepot.Bot, 'editMessageText', send_message)
    def test_survey_send(self):
        self.create_survey()

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/surveys/')
        # wait.until(EC.title_contains("Surveys"))
        # options -> close
        self.assertTrue(len(driver.find_elements_by_class_name('open-survey')) == 1)
        self.assertTrue(len(driver.find_elements_by_class_name('closed-survey')) == 0)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-options>button')))
        driver.find_element_by_css_selector(".survey-options>button").click()
        driver.find_element_by_class_name("survey-close-btn").click()
        wait.until(EC.alert_is_present())
        alert = driver.switch_to_alert()
        alert.accept()
        # closed, results
        self.assertTrue(len(driver.find_elements_by_class_name('closed-survey')) == 1)
        self.assertTrue(len(driver.find_elements_by_class_name('open-survey')) == 0)
        # send button click
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-options>button')))
        driver.find_element_by_css_selector(".survey-options>button").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.survey-send-result-btn')))
        driver.find_element_by_class_name("survey-send-result-btn").click()
        self.assertTrue(len(driver.find_elements_by_class_name('survey-list')) == 1)
