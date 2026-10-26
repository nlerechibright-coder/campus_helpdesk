import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Idempotently creates the predefined management account securely'

    def handle(self, *args, **kwargs):
        # Read credentials from environment variables, never hardcode them
        username = os.environ.get('MANAGEMENT_USERNAME', 'helpdesk_admin')
        password = os.environ.get('MANAGEMENT_PASSWORD')

        if not password:
            self.stderr.write(self.style.ERROR('Error: MANAGEMENT_PASSWORD environment variable is not set.'))
            return

        # Idempotency check: Do not duplicate or reset if it already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists. No changes made.'))
            return

        # Create the user securely
        User.objects.create_user(
            username=username,
            password=password, # Django automatically hashes this
            role=User.ROLE_MANAGEMENT,
            is_staff=True, # Allows access to Django Admin if ever needed
            is_superuser=False # Strictly follows requirement to not depend on superuser
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created management account: {username}'))