from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
import os


class Command(BaseCommand):
    help = 'Seed database with initial data from fixtures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force loading data even if tables are not empty',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting database seeding...')
        
        # Check if we're in production (DATABASE_URL is set)
        is_production = bool(os.environ.get('DATABASE_URL'))
        
        if is_production:
            self.stdout.write(self.style.WARNING('Running in PRODUCTION mode'))
        else:
            self.stdout.write('Running in DEVELOPMENT mode')

        try:
            with transaction.atomic():
                # Load fixtures in order (users first, then related data)
                fixtures = [
                    'fixtures/users.json',
                    'fixtures/timetables.json', 
                    'fixtures/course_history.json'
                ]
                
                for fixture in fixtures:
                    if os.path.exists(fixture):
                        self.stdout.write(f'Loading {fixture}...')
                        call_command('loaddata', fixture, verbosity=0)
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Successfully loaded {fixture}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Fixture {fixture} not found, skipping...')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS('✓ Database seeded successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error seeding database: {str(e)}')
            )
            raise
