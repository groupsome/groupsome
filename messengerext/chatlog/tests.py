from django.test import TestCase, RequestFactory
from django.http import HttpRequest
from django.test.client import Client
from groups.tests import create_user, create_group, create_photo, create_album


class TestChatlogView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.photo1 = create_photo(self.user, self.group)
        self.photo2 = create_photo(self.user, self.group)
        self.photo3 = create_photo(self.user, self.group)
        self.other_group = create_group(telegram_id=2)
        self.other_user = create_user("Test2", "test2@test.test")
        self.other_photo = create_photo(self.other_user, self.other_group)
    
    def test_foreign_group(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/chatlog/photo/4")
        self.assertEquals(403, response.status_code)

    def test_selection(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/chatlog/photo/2")
        self.assertTemplateUsed(response, "chatlog/chatlog.html")
        self.assertIn(self.photo1, response.context["feed"])
        self.assertIn(self.photo2, response.context["feed"])
        self.assertIn(self.photo3, response.context["feed"])
    
    def test_foreign_group_pager(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/chatlog/photo/4/older")
        self.assertEquals(403, response.status_code)
    
    def test_pager_older(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/chatlog/photo/3/older")
        self.assertTemplateUsed(response, "chatlog/chatlog_items.html")
        self.assertIn(self.photo1, response.context["feed"])
        self.assertIn(self.photo2, response.context["feed"])
        self.assertNotIn(self.photo3, response.context["feed"])
    
    def test_pager_newer(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/chatlog/photo/1/newer")
        self.assertTemplateUsed(response, "chatlog/chatlog_items.html")
        self.assertNotIn(self.photo1, response.context["feed"])
        self.assertIn(self.photo2, response.context["feed"])
        self.assertIn(self.photo3, response.context["feed"])
