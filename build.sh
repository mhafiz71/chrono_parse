#!/bin/bash

# Build script for Render deployment

set -o errexit  # exit on error

echo "Starting build process..."

# Upgrade pip first
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Verify PostgreSQL adapter installation
echo "Verifying PostgreSQL adapter..."
python -c "
try:
    import psycopg2
    print('✓ psycopg2-binary installed successfully')
except ImportError as e:
    print(f'⚠ psycopg2-binary not available: {e}')
    print('Will fallback to SQLite')
"

# Install Node.js dependencies and build Tailwind CSS
echo "Installing Node.js dependencies..."
cd theme/static_src
npm install

echo "Building Tailwind CSS..."
npm run build

# Go back to project root
cd ../..

# Create media directory if it doesn't exist
echo "Setting up media directory..."
mkdir -p media/master_timetables

# Note: Master timetables will be loaded from fixtures/timetables.json
# via the seed_data command, so no need to create sample files here

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Seed database with initial data from fixtures
echo "Seeding database with initial data..."
python manage.py seed_data

# Verify database setup
echo "Verifying database setup..."
python manage.py shell -c "
from django.db import connection
from core.models import User, TimetableSource
print(f'Database engine: {connection.vendor}')
print(f'Users count: {User.objects.count()}')
print(f'Timetables count: {TimetableSource.objects.count()}')
"

echo "Build completed successfully!"
