from .context import *


class LoginTestCase(HOSLiveServerTestCase):

    def setUp(self):
        self.browser = get_webdriver()
        self.browser.implicitly_wait(10)
        create_user()

    def tearDown(self):
        self.browser.quit()

    def test_can_login_to_site(self):
        self.browser.get(self.live_server_url + '/login')

        self.assertNotIn('Not Found', self.browser.page_source)
        self.assertIn('groupsome - Login', self.browser.title)

        login_inputbox = self.browser.find_element_by_id('id_login')
        login_inputbox.send_keys('Superuser')
        password_inputbox = self.browser.find_element_by_id('id_password')
        password_inputbox.send_keys('Password')
        password_inputbox.send_keys(Keys.RETURN)

        # The website welcomes the now logged-in User
        wait = WebDriverWait(self.browser, 10)
        wait.until_not(EC.title_contains("Login"))
        self.assertTrue(EC.title_contains("groupsome"))
