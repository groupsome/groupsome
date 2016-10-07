from django.test import TestCase, RequestFactory
from django.core.urlresolvers import resolve, reverse
from django.test.client import Client
from django.contrib.auth.models import User
from home.models import Directory, File
from gallery.models import Album
from gallery import queries
from groups.tests import create_user, create_group, create_photo, create_album
import mock
import json


def create_directory(group, parent=None):
    return Directory.create_and_save(group=group, name="Foo", parent=parent)


def create_file(user, group, telegram_id=3000, directory=None):
    return File.create_and_save(user=user, group=group, timestamp="2016-05-25 12:59:10+01:00",
                                other_file="Overview.pdf", file_name='overview', doc_type="JPEG",
                                telegram_id=telegram_id, directory=directory)


class TestDirectoryView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.directory = create_directory(self.group)
        self.file = create_file(self.user, self.group)
        self.directory_file = create_file(self.user, self.group, telegram_id=3001, directory=self.directory)
    
    def test_index(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/files")
        self.assertTemplateUsed(response, "files/group/directory.html")
        self.assertEquals(response.context["group"], self.group)
        self.assertEquals(response.context["directory"], None)
        self.assertIn(self.directory, response.context["directories"])
        self.assertIn(self.file, response.context["files"])

    def test_directory(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/files/directories/1")
        self.assertTemplateUsed(response, "files/group/directory.html")
        self.assertEquals(response.context["directory"], self.directory)
        self.assertIn(self.directory_file, response.context["files"])


class TestDeleteFileView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.group = create_group(self.user, is_admin=True, users=[self.unprivileged_user])
        self.file = create_file(self.user, self.group)

    def test_delete_file_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post("/groups/1/files/1/delete")
        self.assertEquals(response.status_code, 403)

    def test_delete_file(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/1/delete")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "File deleted")
        self.assertEquals(File.objects.filter(pk=self.file.id).count(), 0)

    def test_delete_non_existing_file(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/2/delete")
        self.assertEquals(response.status_code, 404)


class TestDeleteDirectoryView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.group = create_group(self.user, is_admin=True, users=[self.unprivileged_user])
        self.empty_directory = create_directory(self.group)
        self.file_directory = create_directory(self.group)
        self.file = create_file(self.user, self.group, directory=self.file_directory)
        self.sub_directory_parent = create_directory(self.group)
        self.sub_directory_child = create_directory(self.group, self.sub_directory_parent)
        self.sub_directory_child_file = create_file(self.user, self.group,
                                                    telegram_id=3001, directory=self.sub_directory_child)

    def test_delete_directory_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post("/groups/1/files/directories/%d/delete" % self.empty_directory.id)
        self.assertEquals(response.status_code, 403)

    def test_delete_empty_directory(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/%d/delete" % self.empty_directory.id)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Directory deleted")
        self.assertEquals(Directory.objects.filter(pk=self.empty_directory.id).count(), 0)

    def test_delete_directory_with_file(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/%d/delete" % self.file_directory.id)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Directory.objects.filter(pk=self.file_directory.id).count(), 0)
        self.assertEquals(File.objects.filter(pk=self.file.id).count(), 0)

    def test_delete_directory_with_subdirectory(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/%d/delete" % self.sub_directory_parent.id)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Directory.objects.filter(pk=self.sub_directory_parent.id).count(), 0)
        self.assertEquals(Directory.objects.filter(pk=self.sub_directory_child.id).count(), 0)
        self.assertEquals(File.objects.filter(pk=self.sub_directory_child_file.id).count(), 0)

    def test_delete_non_existing_directory(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/1000/delete")
        self.assertEquals(response.status_code, 404)


class TestFileMoveView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.group = create_group(self.user, is_admin=True, users=[self.unprivileged_user])
        self.file = create_file(self.user, self.group)
        self.directory = create_directory(self.group)
        self.other_file = create_file(self.user, self.group, telegram_id=3001, directory=self.directory)

    def test_move_file_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post("/groups/1/files/1/move", {"directory": self.directory.id})
        self.assertEquals(response.status_code, 403)

    def test_move_file_to_directory(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/1/move", {"directory": self.directory.id})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "File moved")
        self.file.refresh_from_db()
        self.assertEquals(self.file.directory, self.directory)

    def test_move_file_to_root(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/2/move", {"directory": 0})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "File moved")
        self.other_file.refresh_from_db()
        self.assertEquals(self.other_file.directory, None)

    def test_move_non_existing_file(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/1000/move", {"directory": self.directory.id})
        self.assertEquals(response.status_code, 404)


class TestDirectoryMoveView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.group = create_group(self.user, is_admin=True, users=[self.unprivileged_user])
        self.directory = create_directory(self.group)
        self.other_directory = create_directory(self.group)
        self.sub_directory = create_directory(self.group, self.directory)
    
    def test_move_directory_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post("/groups/1/files/directories/%d/move" % self.directory.id,
                                    {"directory": self.other_directory.id})
        self.assertEquals(response.status_code, 403)
    
    def test_move_directory_to_directory(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/%d/move" % self.directory.id,
                                    {"directory": self.other_directory.id})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Directory moved")
        self.directory.refresh_from_db()
        self.assertEquals(self.directory.parent, self.other_directory)

    def test_move_directory_to_root(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/%d/move" % self.sub_directory.id, {"directory": 0})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Directory moved")
        self.sub_directory.refresh_from_db()
        self.assertEquals(self.sub_directory.parent, None)

    def test_move_non_existing_directory(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/1000/move", {"directory": 0})
        self.assertEquals(response.status_code, 404)


class TestCreateDirectoryView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.group = create_group(self.user, is_admin=True, users=[self.unprivileged_user])
        self.directory = create_directory(self.group)

    def test_create_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post("/groups/1/files/directories/create", {"name": "Test", "parent": 0}, follow=True)
        self.assertEquals(response.status_code, 403)

    def test_create_within_root(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/create", {"name": "Test", "parent": 0}, follow=True)
        self.assertRedirects(response, reverse('groups:file_directory',
                                               kwargs={"group_id": self.group.id, "directory_id": 2}))
        directory = Directory.objects.get(pk=2)
        self.assertIsNotNone(directory)

    def test_create_within_directory(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/groups/1/files/directories/create", {"name": "Test", "parent": 1}, follow=True)
        self.assertRedirects(response, reverse('groups:file_directory',
                                               kwargs={"group_id": self.group.id, "directory_id": 2}))
        directory = Directory.objects.get(pk=2)
        self.assertIsNotNone(directory)
        self.assertEquals(directory.parent, self.directory)
