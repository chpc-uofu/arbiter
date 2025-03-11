import logging

from django.core.management.base import BaseCommand

from arbiter3.arbiter.conf import ARBITER_USER_LOOKUP


class Command(BaseCommand):
    help = "looks up a user given the username"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        print(ARBITER_USER_LOOKUP(options['username']))