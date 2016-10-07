from django.test import TestCase, RequestFactory
from django.core.urlresolvers import resolve, reverse
from django.test.client import Client
from django.contrib.auth.models import User
from home import models
from bot.models import TelegramUser
from gallery.models import Album
from gallery import queries
from groups.tests import create_user, create_group, create_photo, create_album
import mock
import json


class TestAlbumsOverview(TestCase):
    user = None
    group = None
    album = None

    def create_album_and_photos(self, user):
        photo = models.Photo.create_and_save(user=self.user, group=self.group,
                                             timestamp="2016-05-25 12:59:10",
                                             file="1.jpg",
                                             thumbnail="TODO")
        photo_2 = models.Photo.create_and_save(user=self.user, group=self.group,
                                               timestamp="2016-05-25 12:59:10",
                                               file="2.jpg",
                                               thumbnail="TODO")
        self.album = Album.create_and_save(name='Best of Croatia', description='only the best', group=self.group)
        self.album.photos.add(photo)
        self.album.photos.add(photo_2)

    def create_empty_album(self, user):
        self.album = Album.create_and_save(name='Best of Croatia', description='only the best', group=self.group)

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.group = create_group(self.user, is_admin=True, users=[self.unprivileged_user])

    def test_gallery_shows_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_overview', kwargs={"group_id": self.group.id}))
        self.assertTemplateUsed(response=response, template_name='gallery/group/overview.html')

    def test_gallery_returns_album(self):
        self.create_album_and_photos(self.user)
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_album', kwargs={"group_id": self.group.id,
                                                                         "album_id": self.album.id}))
        self.assertEquals(response.context['album'], self.album)

    def test_gallery_counts_photos_in_an_album(self):
        self.create_album_and_photos(self.user)
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_overview', kwargs={"group_id": self.group.id}))
        self.assertEquals(response.context['albums'][0]['photo_count'], 2)

    def test_gallery_serves_media_url_for_title_photo(self):
        self.create_album_and_photos(self.user)
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_overview', kwargs={"group_id": self.group.id}))
        self.assertTrue(response.context['albums'][0]['photo_file'].find('/media/photo/1') != -1)

    def test_gallery_uses_placeholder_for_empty_albums(self):
        self.create_empty_album(self.user)
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_overview', kwargs={"group_id": self.group.id}))
        self.assertEquals(response.context['albums'][0]['photo_file'], '/static/img/add-pictures.jpg')

    @mock.patch("gallery.models.Album.create_and_save")
    def test_create_album_redirect(self, create_and_save):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('groups:photo_overview', kwargs={"group_id": self.group.id}),
            {'new_album': 'true', 'album_group': '1', 'album_name': 'Awesome Album',
             'album_description': 'this is a album description'},
            follow=True)
        self.assertRedirects(response, reverse('groups:photo_overview', kwargs={"group_id": self.group.id}))

    @mock.patch("gallery.models.Album.create_and_save")
    def test_create_album_unprivileged(self, create_and_save):
        self.create_album_and_photos(user=self.user)
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post(
            reverse('groups:photo_overview', kwargs={"group_id": self.group.id}),
            {'new_album': 'true', 'album_group': self.group.id, 'album_name': 'Awesome Album',
             'album_description': 'this is a album description'},
            follow=True)
        self.assertEquals(403, response.status_code)

    @mock.patch("gallery.models.Album.create_and_save")
    def test_create_album_works_with_valid_input(self, create_and_save):
        self.create_album_and_photos(user=self.user)
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('groups:photo_overview', kwargs={"group_id": self.group.id}),
            {'new_album': 'true', 'album_group': self.group.id, 'album_name': 'Awesome Album',
             'album_description': 'this is a album description'},
            follow=True)
        create_and_save.assert_called()

    @mock.patch("gallery.models.Album.create_and_save")
    def test_no_album_created_with_too_short_name(self, create_and_save):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('groups:photo_overview', kwargs={"group_id": self.group.id}),
            {'new_album': 'true', 'album_group': '1', 'album_name': 'A',
             'album_description': 'this is a album description'},
            follow=True)
        create_and_save.assert_not_called()

    @mock.patch("gallery.models.Album.create_and_save")
    def test_no_album_created_without_description(self, create_and_save):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('groups:photo_overview', kwargs={"group_id": self.group.id}),
            {'new_album': 'true', 'album_group': '1', 'album_name': 'A',
             'album_description': ''},
            follow=True)
        create_and_save.assert_not_called()

    @mock.patch("gallery.models.Album.delete", )
    def test_delete_album_unprivileged(self, delete):
        self.create_album_and_photos(user=self.user)
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post(
            reverse('groups:photo_overview', kwargs={"group_id": self.group.id}),
            {'delete_album': 'true', 'album_id': self.album.id},
            follow=True)
        self.assertEquals(403, response.status_code)

    @mock.patch("gallery.models.Album.delete", )
    def test_delete_album_works(self, delete):
        self.create_album_and_photos(user=self.user)
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('groups:photo_overview', kwargs={"group_id": self.group.id}),
            {'delete_album': 'true', 'album_id': self.album.id},
            follow=True)
        delete.assert_called()

    @mock.patch("gallery.models.Album.delete")
    def test_delete_album_is_forbidden_when_album_is_wrong(self, delete):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('groups:photo_overview', kwargs={"group_id": self.group.id}),
            {'delete_album': 'true', 'album_id': '-1'},
            follow=True)
        delete.assert_not_called()


class TestPhotoAlbum(TestCase):
    group = None
    group2 = None
    album = None
    album2 = None

    def create_user(self):
        user = User.objects.create_user('Superuser',
                                        'superuser@super.com',
                                        'Password')
        user.save()
        TelegramUser.create_and_save(user=user, telegram_id=1)
        return user

    def create_album_and_photos(self, user):
        self.group = models.Group.create_and_save(name="Croatia 2016",
                                                  picture="", description="abc", telegram_id=3)
        self.group.users.add(self.user)
        self.group2 = models.Group.create_and_save(name="Croatia 2016",
                                                   picture="", description="abc", telegram_id=4)
        photo = models.Photo.create_and_save(user=self.user, group=self.group,
                                             timestamp="2016-05-25 12:59:10",
                                             file="1.jpg",
                                             thumbnail="TODO")
        photo_2 = models.Photo.create_and_save(user=self.user, group=self.group,
                                               timestamp="2016-05-25 12:59:10",
                                               file="2.jpg",
                                               thumbnail="TODO")
        self.album = Album.create_and_save(name='Best of Croatia', description='only the best', group=self.group)
        self.album.photos.add(photo)
        self.album.photos.add(photo_2)
        user2 = User.objects.create_user('user2',
                                         'user2@super.com',
                                         'Password')
        user2.save()
        self.album2 = Album.create_and_save(name='Not this album', description='never', group=self.group2)

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = self.create_user()
        self.create_album_and_photos(self.user)

    def test_album_detail_uses_template(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_album', kwargs={"group_id": self.group.id,
                                                                         "album_id": self.album.id}))
        self.assertTemplateUsed(response=response, template_name='gallery/group/album.html')

    def test_album_from_other_user_is_not_accessible(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_album', kwargs={"group_id": self.group2.id,
                                                                         "album_id": self.album2.id}))
        self.assertEquals(response.status_code, 403)

    def test_view_returns_pictures(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_album', kwargs={"group_id": self.group.id,
                                                                         "album_id": self.album.id}))
        self.assertEquals(len(response.context['photos']), 2)

    def test_view_returns_only_other_albums_than_itself(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('groups:photo_album', kwargs={"group_id": self.group.id,
                                                                         "album_id": self.album.id}))
        self.assertEquals(len(response.context['albums']), 0)


class TestAddPhotoView(TestCase):
    group = None
    album = None
    photo = None
    photo_2 = None

    def create_album_and_photos(self, user):
        self.group = models.Group.create_and_save(name="Croatia 2016",
                                                  picture="", description="abc", telegram_id=3, everyone_is_admin=False)
        self.group.users.add(self.user)
        self.group.users.add(self.unprivileged_user)
        self.group.admins.add(self.user)
        group_2 = models.Group.create_and_save(name="Not allowed to add photo from here",
                                               picture="", description="abc", telegram_id=4)
        self.photo = models.Photo.create_and_save(user=self.user, group=self.group,
                                                  timestamp="2016-05-25 12:59:10",
                                                  file="1.jpg",
                                                  thumbnail="TODO")
        self.photo_2 = models.Photo.create_and_save(user=self.user, group=group_2,
                                                    timestamp="2016-05-25 12:59:10",
                                                    file="2.jpg",
                                                    thumbnail="TODO")
        self.album = Album.create_and_save(name='Best of Croatia', description='only the best', group=self.group)

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.create_album_and_photos(self.user)

    def test_add_photo_to_album_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/add/' + str(self.photo.id))
        self.assertEqual(response.status_code, 403)

    def test_add_photo_to_album(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/add/' + str(self.photo.id))
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.content,
            b'{"message": "Added image successfully"}'
        )

    def test_can_not_add_photo_to_album_from_a_group_user_is_not_in(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/add/' + str(self.photo_2.id))
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.content,
            b'{"message": "Something went wrong"}'
        )

    def test_add_photo_to_album(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/add/' + str(self.photo.id))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/add/' + str(self.photo.id))
        self.assertEquals(
            response.content,
            b'{"message": "Already in album"}'
        )


class TestDeletePhotoFromAlbumView(TestCase):
    group = None
    album = None
    album_2 = None
    photo = None
    photo_2 = None

    def create_album_and_photos(self, user):
        self.group = models.Group.create_and_save(name="Croatia 2016",
                                                  picture="", description="abc", telegram_id=3, everyone_is_admin=False)
        self.group.users.add(self.user)
        self.group.users.add(self.unprivileged_user)
        self.group.admins.add(self.user)
        group_2 = models.Group.create_and_save(name="Not allowed to add photo from here",
                                               picture="", description="abc", telegram_id=4)
        self.photo = models.Photo.create_and_save(user=self.user, group=self.group,
                                                  timestamp="2016-05-25 12:59:10",
                                                  file="1.jpg",
                                                  thumbnail="TODO")
        self.photo_2 = models.Photo.create_and_save(user=self.user, group=self.group,
                                                    timestamp="2016-05-25 12:59:11",
                                                    file="2.jpg",
                                                    thumbnail="TODO")
        self.album = Album.create_and_save(name='Best of Croatia', description='only the best', group=self.group)
        self.album.photos.add(self.photo)
        self.album.photos.add(self.photo_2)
        self.album_2 = Album.create_and_save(name='Another album',
                                             description='no photo removed from here',
                                             group=group_2)
        self.album_2.photos.add(self.photo_2)

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.create_album_and_photos(self.user)

    def test_delete_photo_from_album_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/delete_from_album/' + str(self.photo.id))
        self.assertEqual(response.status_code, 403)

    def test_delete_photo_to_album(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/delete_from_album/' + str(self.photo.id))
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.content,
            b'{"message": "Successfully removed from album"}'
        )

    def test_can_not_delete_photo_from_album_of_a_group_the_user_is_not_in(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album_2.id) + '/delete_from_album/' + str(
                self.photo_2.id))
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.content,
            b'{"message": "Something went wrong"}'
        )

    def test_photo_is_removed_from_album(self):
        self.client.force_login(user=self.user)
        album_content_count_before = self.album.photos.count()
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/delete_from_album/' + str(self.photo.id))
        album_content_count_after = self.album.photos.count()
        self.assertEqual(album_content_count_after, album_content_count_before - 1)

    def test_photo_is_removed_from_only_one_album(self):
        self.client.force_login(user=self.user)
        album_content_count_before = self.album_2.photos.count()
        response = self.client.post(
            '/gallery/' + str(self.group.id) + '/' + str(self.album.id) + '/delete_from_album/' + str(self.photo.id))
        album_content_count_after = self.album_2.photos.count()
        self.assertEqual(album_content_count_after, album_content_count_before)


class TestGroupView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.photo = create_photo(self.user, self.group)
        self.album = create_album(self.group, self.photo)

    def test_overview(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/photos")
        self.assertTemplateUsed(response, "gallery/group/overview.html")
        self.assertIn(self.photo, response.context["photos"])
        self.assertEquals(self.album.id, response.context["albums"][0]["id"])


class TestGroupAlbumDetailView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.photo = create_photo(self.user, self.group)
        self.album = create_album(self.group, self.photo)
        self.other_group = create_group(telegram_id=2)
        self.other_album = create_album(self.other_group)
        self.uncategorized_photo = create_photo(self.user, self.group)

    def test_other_album(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/photos/albums/2")
        self.assertEquals(response.status_code, 404)

    def test_album(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/photos/albums/1")
        self.assertTemplateUsed(response, "gallery/group/album.html")
        self.assertEquals(self.album, response.context["album"])
        self.assertNotIn(self.album, response.context["albums"])
        self.assertEquals(self.photo.media_url, response.context["cover"])
        self.assertIn(self.photo, response.context["photos"])
        self.assertNotIn(self.uncategorized_photo, response.context["photos"])


class TestSetCoverView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.group = create_group(self.user, is_admin=True, users=[self.unprivileged_user])
        self.photo = create_photo(self.user, self.group)
        self.album = create_album(self.group, self.photo)
        self.other_photo = create_photo(self.user, self.group)
        self.album.photos.add(self.other_photo)

    def test_set_cover_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post("/gallery/1/1/cover", follow=True)
        self.assertEquals(403, response.status_code)

    def test_set_cover(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/gallery/1/1/cover", follow=True)
        self.assertRedirects(response, reverse('groups:photo_album', kwargs={"group_id": self.group.id,
                                                                             "album_id": self.album.id}))
        self.album.refresh_from_db()
        self.assertEquals(self.album.cover, self.photo)

    def test_default_cover(self):
        cover = queries.get_album_cover(self.album, self.album.photos)
        self.assertEquals(cover, self.photo.media_url)

    def test_explicit_cover(self):
        self.album.cover = self.other_photo
        cover = queries.get_album_cover(self.album, self.album.photos)
        self.assertEquals(cover, self.other_photo.media_url)


class TestDeletePhotoView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.unprivileged_user = create_user("Unprivileged", "unpriv@test.test")
        self.group = create_group(self.user, is_admin=True, users=[self.unprivileged_user])
        self.photo = create_photo(self.user, self.group)

    def test_delete_photo_unprivileged(self):
        self.client.force_login(user=self.unprivileged_user)
        response = self.client.post("/gallery/photos/1/delete")
        self.assertEquals(response.status_code, 403)

    def test_delete_photo(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/gallery/photos/1/delete")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Photo deleted")
        self.assertEquals(models.Photo.objects.filter(pk=self.photo.id).count(), 0)

    def test_delete_non_existingphoto(self):
        self.client.force_login(user=self.user)
        response = self.client.post("/gallery/photos/2/delete")
        self.assertEquals(response.status_code, 404)


class TestPhotoDetailView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.photo = create_photo(self.user, self.group)

    def test_view(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/photos/1")
        self.assertTemplateUsed(response, "gallery/group/photo.html")
        self.assertEquals(self.photo, response.context["photo"])


class TestAlbumPhotoDetailView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user)
        self.photo = create_photo(self.user, self.group)
        self.album = create_album(self.group, self.photo)
        self.photo2 = create_photo(self.user, self.group)
        self.photo3 = create_photo(self.user, self.group)
        self.album.photos.add(self.photo2)
        self.album.photos.add(self.photo3)

    def test_view(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/photos/albums/1/1")
        self.assertTemplateUsed(response, "gallery/group/album_photo.html")
        self.assertEquals(self.photo, response.context["photo"])
        self.assertEquals(self.album, response.context["album"])

    def test_pager(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/groups/1/photos/albums/1/2")
        self.assertTemplateUsed(response, "gallery/group/album_photo.html")
        self.assertEquals(self.photo, response.context["prev"])
        self.assertEquals(self.photo3, response.context["next"])


class TestRotatePhotoLeftView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user, is_admin=True)
        self.photo = create_photo(self.user, self.group)

    @mock.patch("django_rq.enqueue")
    def test_rotate_photo(self, enqueue):
        self.client.force_login(user=self.user)
        response = self.client.post("/gallery/photos/1/rotate/left")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Photo rotated")
        enqueue.assert_called()

    @mock.patch("django_rq.enqueue")
    def test_rotate_non_existing_photo(self, enqueue):
        self.client.force_login(user=self.user)
        response = self.client.post("/gallery/photos/2/rotate/left")
        self.assertEquals(response.status_code, 404)
        enqueue.assert_not_called()


class TestRotatePhotoRightView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = create_user()
        self.group = create_group(self.user, is_admin=True)
        self.photo = create_photo(self.user, self.group)

    @mock.patch("django_rq.enqueue")
    def test_rotate_photo(self, enqueue):
        self.client.force_login(user=self.user)
        response = self.client.post("/gallery/photos/1/rotate/right")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get("Content-Type"), "application/json")
        data = json.loads(response.content.decode("utf-8"))
        self.assertEquals(data["message"], "Photo rotated")
        enqueue.assert_called()

    @mock.patch("django_rq.enqueue")
    def test_rotate_non_existing_photo(self, enqueue):
        self.client.force_login(user=self.user)
        response = self.client.post("/gallery/photos/2/rotate/right")
        self.assertEquals(response.status_code, 404)
        enqueue.assert_not_called()
