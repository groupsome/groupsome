from .context import *


class GalleryTestcase(HOSLiveServerTestCase):
    def create_content(self):
        user = create_user()
        self.group = models.Group.create_and_save(name='Croatia 2016', picture='', description='summer vacation',
                                                  telegram_id=21)
        self.group.users.add(user)
        self.album = Album.create_and_save(name='Best of Croatia', description='only the best', group=self.group)

        photo = models.Photo.create_and_save(user=user, group=self.group,
                                             timestamp="2016-05-25 12:59:10+01:00",
                                             file=os.path.join(settings.MEDIA_ROOT, 'testbild.jpg'),
                                             thumbnail=os.path.join(settings.MEDIA_ROOT, 'testbild_thumbnail.jpg'))
        self.album.photos.add(photo)

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

    def test_can_access_gallery(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        groups_link = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Groups")))
        groups_link.send_keys(Keys.RETURN)
        group_link = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.group-preview')))
        group_link.send_keys(Keys.RETURN)
        gallery_link = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Photos")))
        gallery_link.send_keys(Keys.RETURN)
        wait.until(EC.title_contains("Photos"))

    def test_create_album(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/groups/' + str(self.group.id) + '/photos')
        wait.until(EC.title_contains("Photos"))
        count_albums_before = len(driver.find_elements_by_css_selector('.item.album'))
        driver.find_element_by_id('input-new-album-name').send_keys('My new album')
        driver.find_element_by_id('input-new-album-description') \
            .send_keys('My new album')
        driver.find_element_by_css_selector('#create-album > form > label.btn').click()
        wait.until(self.CountAlbums(count_albums_before + 1))

    def test_delete_album(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        driver.get(self.live_server_url + '/groups/' + str(self.group.id) + '/photos')
        wait.until(EC.title_contains("Photos"))
        count_albums_before = len(driver.find_elements_by_css_selector('.item.album'))
        driver.find_element_by_css_selector(
            'div.album:nth-child(1) > div:nth-child(3) > a:nth-child(1) > i:nth-child(1)').click()
        alert = driver.switch_to.alert
        alert.accept()
        wait.until(self.CountAlbums(count_albums_before - 1))

    def test_remove_image_from_album(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        id = self.album.id
        driver.get(self.live_server_url + '/groups/' + str(self.group.id) + '/photos/albums/' + str(self.album.id))
        wait.until(EC.title_contains("Photos"))
        element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.photo-options')))
        element.click()
        element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.remove-from-album-btn')))
        element.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.item')))

    def test_toast_notification(self):
        self.force_login()
        driver = self.browser
        wait = WebDriverWait(driver, 10)
        wait.until_not(EC.title_contains('Login'))
        id = self.album.id
        driver.get(self.live_server_url + '/groups/' + str(self.group.id) + '/photos/albums/' + str(self.album.id))
        wait.until(EC.title_contains("Photos"))
        element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.photo-options')))
        element.click()
        element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.photo-delete-btn')))
        element.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.toast')))

    class CountAlbums:
        def __init__(self, target):
            self.target = target

        def __call__(self, driver):
            return len(driver.find_elements_by_css_selector('.item.album')) == self.target
