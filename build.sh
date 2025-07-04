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

# Create media directory if it doesn't exist
echo "Setting up media directory..."
mkdir -p media/master_timetables

# Copy sample JSON files if they don't exist (for initial deployment)
if [ ! -f "media/master_timetables/master_timetable.json" ]; then
    echo "Creating default master timetable..."
    cat > media/master_timetables/master_timetable.json << 'EOF'
[
  {
    "Day": "Monday",
    "Time": "7:00a - 9:55a",
    "Course": "ENV 633 Lec 1",
    "Venue": "C-BLOCK RM 1 (80, 56.55)",
    "Instructor(s)": "Ampofo, S"
  },
  {
    "Day": "Monday",
    "Time": "2:00p - 3:55p",
    "Course": "CAC 301 Lec 1",
    "Venue": "C-BLOCK RM 1 (80, 56.55)",
    "Instructor(s)": "Anafo, A"
  }
]
EOF
fi

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
