from .context import *
from home import models


class GroupSelectionTestCase(HOSLiveServerTestCase):

    def setUp(self):
        self.browser = get_webdriver()
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

    def test_checkboxes_are_shown_for_groups(self):
        for i in range(1, 7):
            group = models.Group.create_and_save(name='k' + str(i), picture='', description='k' + str(i),
                                                 telegram_id=230 + i)
            group.users.add(self.user)
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        elems = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".feed-select>label")))
        for i in range(1, 7):
            self.assertTrue(elems[i - 1].text.__contains__(str(i)))

    # NOT USED

    # def test_cookie_works(self):
    #     ids = []
    #     for i in range(1, 4):
    #         group = models.Group.create_and_save(name='l'+str(i), picture='', description='l'+str(i),
    #                 telegram_id=220+i)
    #         group.users.add(self.user)
    #         photo = models.Photo.create_and_save(user=self.user, group=group,
    #                                              timestamp="2016-05-25 12:59:10",
    #                                              file='/media/testbild.jpg',
    #                                              thumbnail='/media/testbild_thumbnail.jpg')
    #         ids.append(group.id)
    #     self.force_login()
    #     driver = self.browser
    #     id2 = list(ids)
    #     id3 = list(ids)
    #     for i in range(1, 4):
    #         self.assertTrue(driver.find_element_by_id('checkbox'+ str(ids.pop())).is_selected())
    #     for i in range(1, 2):
    #         driver.find_element_by_id('checkbox'+ str(id2.pop())).click
    #     driver.get(self.live_server_url + '/home')
    #     #driver.implicitly_wait(10)
    #     for i in range(1, 2):
    #         self.assertFalse(driver.find_element_by_id('checkbox'+ str(id3.pop())).is_selected())
    #     for i in range(1, 2):
    #         self.assertTrue(driver.find_element_by_id('checkbox'+ str(id3.pop())).is_selected())
    #
    #
    #
    # def test_no_group_selected(self):
    #       ids = []
    #       for i in range(1, 4):
    #           group = models.Group.create_and_save(name='f'+str(i), picture='', description='f'+str(i),
    #                   telegram_id=220+i)
    #           group.users.add(self.user)
    #           photo = models.Photo.create_and_save(user=self.user, group=group,
    #                                                timestamp="2016-05-25 12:59:10",
    #                                                file='/media/testbild.jpg',
    #                                                thumbnail='/media/testbild_thumbnail.jpg')
    #           ids.append(group.id)
    #       self.force_login()
    #       driver = self.browser
    #       for i in range(1, 4):
    #           driver.find_element_by_id('checkbox'+ str(ids.pop())).click
    #       #driver.implicitly_wait(10)
    #       self.assertNotIn('posted', driver.find_element_by_id('feed').text)
    #
    # def test_dropdown_for_small_resolution(self):
    #   driver.manage().window().setSize(new Dimension(1024, 768)) FIXME
    #   self.force_login()
    #   el self.browser.find_element_by_id('groups')
    #   self.assertTrue(el)
    #
    # def test_ajax_loading_works(self):
    #     ids = []
    #     for i in range(1, 4):
    #         group = models.Group.create_and_save(name='o' + str(i), picture='', description='o' + str(i),
    #                                              telegram_id=210 + i)
    #         group.users.add(self.user)
    #         photo = models.Photo.create_and_save(user=self.user, group=group,
    #                                              timestamp="2016-05-25 12:59:10+01:00",
    #                                              file=os.path.join(settings.MEDIA_ROOT, 'testbild.jpg'),
    #                                              thumbnail=os.path.join(settings.MEDIA_ROOT,
    #                                              'testbild_thumbnail.jpg'))
    #         ids.append(group.id)
    #     self.force_login()
    #     driver = self.browser
    #     wait = WebDriverWait(driver, 10)
    #     for i in range(4, 1):
    #         for j in range(1, i):
    #             wait.until(EC.visibility_of_any_elements_located((By.CLASS_NAME, 'item')))
    #             el = driver.find_element_by_xpath("//div[@id='feed']/div[" + str(j) + "]/a/img")
    #             self.assertTrue(el)
    #         driver.find_element_by_id('checkbox' + str(ids.pop())).click()
