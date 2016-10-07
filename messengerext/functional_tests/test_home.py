from .context import *


class HomeTestCase(HOSLiveServerTestCase):

    def setUp(self):
        self.browser = get_webdriver()
        self.browser.implicitly_wait(10)
        self.user = create_user()

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

    def test_shows_content_for_user(self):
        group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                             telegram_id=18)
        group.save()
        group.users.add(self.user)
        photo = models.Photo.create_and_save(user=self.user, group=group,
                                             timestamp="2016-05-25 12:59:10+01:00",
                                             file=os.path.join(settings.MEDIA_ROOT, 'testbild.jpg'),
                                             thumbnail=os.path.join(settings.MEDIA_ROOT, 'testbild_thumbnail.jpg'))

        photo.save()
        self.browser.get(self.live_server_url + '/login')
        login_inputbox = self.browser.find_element_by_id('id_login')
        login_inputbox.send_keys('Superuser')
        password_inputbox = self.browser.find_element_by_id('id_password')
        password_inputbox.send_keys('Password')
        self.browser.find_element_by_id('submit').click()
        self.assertTrue(self.browser.find_element_by_class_name('item').is_displayed())

    def test_user_can_log_out(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        menu = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "dropdown-toggle")))
        menu.send_keys(Keys.RETURN)
        logout_button = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "logout-button")))
        logout_button.send_keys(Keys.RETURN)
        wait.until(EC.presence_of_element_located((By.ID, "login-link")))
        self.assertTrue(driver.current_url.__contains__('landing'))
        # can not access home anymore
        driver.get(self.live_server_url + '/home')
        wait.until(EC.presence_of_element_located((By.ID, "login-link")))
        self.assertTrue(driver.current_url.__contains__('landing'))

    def test_tile_shows_right_content_picture(self):
        group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                             telegram_id=20)
        group.save()
        group.users.add(self.user)
        photo = models.Photo.create_and_save(user=self.user, group=group,
                                             timestamp="2016-05-25 12:59:10+01:00",
                                             file=os.path.join(settings.MEDIA_ROOT, 'testbild.jpg'),
                                             thumbnail=os.path.join(settings.MEDIA_ROOT, 'testbild_thumbnail.jpg'))
        photo.save()
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.item>a>img')))
        self.assertTrue(el.get_attribute('src').__contains__('/media/photo/thumbnail/' + str(photo.id)))
        self.assertTrue(driver.find_element_by_css_selector('.item-info').text.__contains__('posted'))

    def test_tile_shows_right_content_link(self):
        group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                             telegram_id=2132)
        group.save()
        group.users.add(self.user)
        link_obj = models.Link.create_and_save(user=self.user, group=group,
                                               timestamp="2016-05-30 00:00:00+01:00", title='www.google.de',
                                               url='http://www.google.de', file='197.png',
                                               description='testdescription')
        link_obj.save()
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        link = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.item>a')))
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.item>a>img')))
        self.assertTrue(
            driver.find_element_by_css_selector('.item>p:nth-child(3)').text.__contains__('testdescription'))
        self.assertTrue(driver.find_element_by_css_selector('.item>a>h4').text.__contains__('www.google.de'))
        self.assertTrue(el.get_attribute('src').__contains__('/media/link/preview/'))
        link.send_keys(Keys.RETURN)

        driver.switch_to_window(driver.window_handles[-1])
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#hplogo')))
        self.assertTrue(driver.current_url.__contains__('google'))

    def test_audio_source_is_correct(self):
        group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                             telegram_id=2132)
        group.save()
        group.users.add(self.user)
        audio = models.Audio.create_and_save(user=self.user, group=group,
                                             timestamp='2016-05-15 00:00:00+01:00', file='/media/test.ogg',
                                             duration_sec=23, title='', interpret='', telegram_id='2001')
        audio.save()
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'audio')))
        self.assertTrue(el.get_attribute('src').__contains__('/media/audio/' + str(audio.id)))

    def test_audio_tile_shows_up(self):
        group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                             telegram_id=2132)
        group.save()
        group.users.add(self.user)
        audio = models.Audio.create_and_save(user=self.user, group=group,
                                             timestamp='2016-05-15 00:00:00+01:00', file='1.mp3',
                                             duration_sec=23, title='crawl', interpret='breaking benjamin',
                                             telegram_id='2002')
        audio.save()
        self.force_login()
        driver = self.browser
        self.assertTrue(driver.find_element_by_css_selector('audio'))
        self.assertTrue(driver.find_element_by_css_selector('.audiocontrols'))
        self.assertTrue(driver.find_element_by_css_selector('progress'))
        self.assertTrue(driver.find_element_by_css_selector('p.item-description').text.__contains__(
            'crawl - breaking benjamin'))
