from .context import *


class InfiniteScrollingTestcase(HOSLiveServerTestCase):
    def create_content(self):
        user = create_user()
        group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                             telegram_id=21)
        group.save()
        group.users.add(user)
        for i in range(15):
            photo = models.Photo.create_and_save(user=user, group=group,
                                                 timestamp="2016-05-25 12:59:10+01:00",
                                                 file=os.path.join(settings.MEDIA_ROOT, 'testbild.jpg'),
                                                 thumbnail=os.path.join(settings.MEDIA_ROOT, 'testbild_thumbnail.jpg'))
            photo.save()

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

    def setUp(self):
        self.browser = get_webdriver()
        self.browser.implicitly_wait(10)
        self.create_content()

    def tearDown(self):
        for method, error in self._outcome.errors:
            if error:
                test_method_name = self._testMethodName
                now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.browser.save_screenshot(
                    os.getcwd() + '/functional_tests/screenshots/' + test_method_name + "-" + now + ".png")
        self.browser.quit()

    def test_show_load_more_button(self):
        self.force_login()
        driver = self.browser
        self.assertTrue(driver.find_element_by_link_text('more'))

    def test_load_more_works(self):
        self.force_login()
        driver = self.browser
        driver.find_element_by_link_text('more').click()
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.visibility_of_element_located((By.CLASS_NAME, "endless_more")))
        wait.until_not(EC.visibility_of_element_located((By.CLASS_NAME, "endless_loading")))
        elems = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "item")))
        self.assertTrue(len(elems) == 15)  # assert that browser finds image of second delivery

        # def test_load_more_on_scrolling_works(self):
        #    driver = self.browser
        #    driver.set_window_size(500, 500)
        #    self.force_login()
        #    count_items_before = len(driver.find_elements_by_css_selector('.item'))
        #    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #    #driver.implicitly_wait(5)
        #    count_items_after = len(driver.find_elements_by_css_selector('.item'))
        #    self.assertTrue(count_items_after > count_items_before)
