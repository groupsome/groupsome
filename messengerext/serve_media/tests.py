from django.test import TestCase
import serve_media
import mock
from groups.tests import create_user, create_group, create_photo
from home.models import Sticker


class CleanupMediaTestCase(TestCase):
    def setUp(self):
        self.user = create_user()
        self.group = create_group(self.user)
        self.photo = create_photo(self.user, self.group)
        
        self.sticker = Sticker.create_and_save(self.user, self.group, "2016-05-25 12:59:10+01:00",
                                               "sticker.webp", 1)
    
    @mock.patch("serve_media.cleanup.get_media_files_except")
    @mock.patch("serve_media.cleanup.delete_files")
    def test_cleanup(self, delete_files, get_media_files_except):
        def side_effect(media_type, filenames):
            if media_type == "photo":
                self.assertIn("1.jpg", filenames)
                return ["2.jpg", "3.jpg"]
            elif media_type == "sticker":
                self.assertIn("sticker.webp", filenames)
                self.assertIn("sticker.png", filenames)
                return ["sticker.webp", "sticker.png"]
            return []
        get_media_files_except.side_effect = side_effect
        
        serve_media.cleanup.cleanup_media()
        
        delete_files.assert_any_call("photo", ["2.jpg", "3.jpg"])
        delete_files.assert_any_call("sticker", ["sticker.webp", "sticker.png"])
