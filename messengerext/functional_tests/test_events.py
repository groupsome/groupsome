from .context import *
import mock
import telepot


def send_message(arg1, arg2, arg3, **kwargs):
    return {"text": "sometext", "from": {"id": 123456789, "first_name": "Jon"},
            "date": 1473851534, "chat": {"title": "TestGroup", "id": -987654321, "type": "group"},
            "entities": [{"offset": 0, "length": 24, "type": "bot_command"}], "message_id": 894}


class EventTestCase(HOSLiveServerTestCase):
    def create_content(self):
        user = create_user()
        self.group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                                  telegram_id=21)
        self.group.users.add(user)
        return user

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

    def test_can_access_events(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        event_link = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Events")))
        event_link.send_keys(Keys.RETURN)
        wait.until(EC.title_contains("Events"))
        el = driver.find_element_by_id('eventlist')
        self.assertTrue(el.is_displayed())
        self.assertTrue(el.text.__contains__("No upcoming Events! Take your phone and start a /newevent"))

    def test_radio_button_works(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/events/')
        wait.until(EC.title_contains("Events"))
        button = driver.find_element_by_id('id_cal')
        self.assertFalse(self.browser.find_element_by_id('calendar').is_displayed())
        self.assertTrue(self.browser.find_element_by_id('eventlist').is_displayed())
        self.browser.implicitly_wait(10)
        button.click()
        self.assertTrue(self.browser.find_element_by_id('calendar').is_displayed())
        self.assertFalse(self.browser.find_element_by_id('eventlist').is_displayed())
        button = driver.find_element_by_id('id_list')
        self.browser.implicitly_wait(10)
        button.click()
        self.assertFalse(self.browser.find_element_by_id('calendar').is_displayed())
        self.assertTrue(self.browser.find_element_by_id('eventlist').is_displayed())

    def test_content_shown_in_eventlist(self):
        for i in range(-1, 2):
            add = datetime.timedelta(days=i, hours=3)
            time = datetime.datetime.now() + add
            event = Event.create_and_save(group=self.group, start=time,
                                          allday=False, name=str(i), location="Paris")
        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/events/')
        wait.until(EC.title_contains("Events"))
        elems = driver.find_elements_by_class_name('event-list')
        self.assertTrue(len(elems) == 2)
        for i in range(0, 2):
            self.assertTrue(elems[i].text.__contains__(str(i)))

    # def test_event_details_are_shown(self):
    #     add = datetime.timedelta(days=2, hours=3)
    #     time = datetime.datetime.now() + add
    #     event = Event.create_and_save(group=self.group, start=time,
    #                                   allday=False, name=0, location="Paris")
    #     event.save()
    #     event.attendees.add(self.user)
    #     driver = self.browser
    #     self.force_login()
    #     wait = WebDriverWait(driver, 10)
    #     wait.until_not(EC.title_contains('Login'))
    #     driver.get(self.live_server_url + '/events/')
    #     wait.until(EC.title_contains("Events"))
    #     driver.find_element_by_class_name("event-list-data").click()
    #     self.assertTrue(self.browser.find_element_by_class_name('event-details').is_displayed())
    #     self.assertTrue(self.browser.find_element_by_class_name('user-avatar').is_displayed())

    def test_event_deleting(self):
        add = datetime.timedelta(days=2, hours=4)
        time = datetime.datetime.now() + add
        event = Event.create_and_save(group=self.group, start=time,
                                      allday=False, name="tada", location="Paris")
        attend = Attending.create_and_save(user=self.user, status="no")
        attend.event.add(event)
        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/events/')
        wait.until(EC.title_contains("Events"))
        self.assertTrue(len(driver.find_elements_by_class_name('event-list')) == 1)
        # driver.find_element_by_class_name("event-options").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.event-options>button')))
        driver.find_element_by_css_selector(".event-options>button").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.event-delete-btn')))
        driver.find_element_by_class_name("event-delete-btn").click()
        wait.until(EC.alert_is_present())
        alert = driver.switch_to_alert()
        alert.accept()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.event-list')))
        self.assertTrue(len(driver.find_elements_by_class_name('event-list')) == 0)

    def test_attending_status_is_shown(self):
        add = datetime.timedelta(days=2, hours=3)
        start_time = datetime.datetime.now() + add
        event = Event.create_and_save(group=self.group, start=start_time,
                                      allday=False, name=0, location="Paris")
        attend = Attending.create_and_save(user=self.user, status="yes")
        attend.event.add(event)

        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/events/')
        wait.until(EC.title_contains("Events"))

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.fa-check')))
        el = driver.find_element_by_class_name("fa-check")
        el.click()

        driver.find_element_by_link_text("don't attend").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.fa-times')))
        el = driver.find_element_by_class_name("fa-times")
        el.click()

        driver.find_element_by_link_text("maybe attend").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.fa-question')))
        el = driver.find_element_by_class_name("fa-question")
        self.assertTrue(el)

    def test_attending_with_no_status_yet(self):
        add = datetime.timedelta(days=2, hours=3)
        start_time = datetime.datetime.now() + add
        event = Event.create_and_save(group=self.group, start=start_time,
                                      allday=False, name=0, location="Paris")
        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/events/')
        wait.until(EC.title_contains("Events"))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.fa-question')))
        el = driver.find_element_by_class_name("fa-question")
        el.click()
        driver.find_element_by_link_text("don't attend").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.fa-times')))
        el = driver.find_element_by_class_name("fa-times")
        el.click()
        driver.find_element_by_link_text("attend").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.fa-check')))
        el = driver.find_element_by_class_name("fa-check")
        self.assertTrue(el)

    @mock.patch.object(telepot.Bot, 'sendMessage', send_message)
    def test_event_creation(self):
        driver = self.browser
        self.force_login()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/events/')
        wait.until(EC.title_contains("Events"))
        wait.until(EC.presence_of_element_located((By.ID, 'new-Event-lg')))
        el = driver.find_element_by_id("new-Event-lg")
        el.click()
        wait.until(EC.visibility_of_element_located((By.ID, "occasion")))
        el = self.browser.find_element_by_id('occasion')
        el.send_keys('occasion')

        wait.until(EC.visibility_of_element_located((By.ID, "location")))
        loc = self.browser.find_element_by_id('location')
        loc.send_keys('location')

        wait.until(EC.visibility_of_element_located((By.ID, "date")))
        el = self.browser.find_element_by_id('date')
        el.send_keys('11.01.2020')
        loc.click()

        wait.until(EC.visibility_of_element_located((By.ID, "create_event")))
        submit = self.browser.find_element_by_id('create_event')
        submit.send_keys(Keys.ENTER)

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.event-list')))
        list = driver.find_elements_by_class_name('event-list')
        self.assertTrue(len(list) == 1)
