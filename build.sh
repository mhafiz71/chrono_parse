#!/bin/bash

# Build script for Render deployment

set -o errexit  # exit on error

echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies and build Tailwind CSS
echo "Installing Node.js dependencies..."
cd theme/static_src
npm install

echo "Building Tailwind CSS..."
npm run build

# Go back to project root
cd ../..

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist (optional)
# python manage.py shell -c "
# from django.contrib.auth import get_user_model
# User = get_user_model()
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
# "

echo "Build completed successfully!"
