"""
    Django command to wait for database to be available before running the server
"""

from django.core.management.base import BaseCommand
from psycopg2 import OperationalError as Psycopg2OperationalError
from django.db.utils import OperationalError
import time


class Command(BaseCommand):
    """Django command to wait for database"""

    def handle(self, *args, **options):
        """Command entry point"""
        self.stdout.write(self.style.HTTP_INFO('Waiting for database...'))
        db_up = False

        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OperationalError, OperationalError):
                self.stdout.write(self.style.WARNING('Database not available, waiting 1 second...'))
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database is available!'))
