from django.core.management.base import BaseCommand, CommandError
from serve_media.cleanup import cleanup_media


class Command(BaseCommand):
    help = 'Delete media files which dont exist in the database anymore'

    def handle(self, *args, **options):
        cleanup_media()
