# PostgreSQL Deployment Guide for Chronopars Timetable System

## Overview
This guide explains how to deploy the Django timetable system to Render with PostgreSQL database for persistent data storage, solving the data synchronization issue between development and production.

## What This Solves
- **Data Persistence**: PostgreSQL database persists across deployments
- **No Data Loss**: Your timetables and user data won't be lost on redeploy
- **Synchronized Data**: Development fixtures are automatically loaded to production
- **Consistent Environment**: Same data structure in both development and production

## Prerequisites
- Render account
- Git repository with your code
- Current development data exported as fixtures (✓ Already done)

## Step 1: Set Up PostgreSQL Database on Render

1. **Create PostgreSQL Database:**
   - Go to Render Dashboard
   - Click "New" → "PostgreSQL"
   - Name: `chronopars-db`
   - Plan: Free
   - Region: Oregon (or your preferred region)
   - Click "Create Database"

2. **Get Database URL:**
   - Once created, copy the "External Database URL"
   - Format: `postgresql://user:password@host:port/database`

## Step 2: Deploy Web Service

### Option A: Using render.yaml (Recommended)
1. Commit all changes to your repository:
   ```bash
   git add .
   git commit -m "Add PostgreSQL support and data fixtures"
   git push
   ```

2. In Render Dashboard:
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository with `render.yaml`
   - Click "Apply"

### Option B: Manual Setup
1. **Create Web Service:**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - Name: `chronopars-web`
     - Environment: Python 3
     - Build Command: 
       ```bash
       pip install -r requirements.txt && python manage.py migrate && python manage.py seed_data && python manage.py collectstatic --noinput
       ```
     - Start Command: `gunicorn chronopars.wsgi:application`

2. **Set Environment Variables:**
   - `DATABASE_URL`: Paste the PostgreSQL External Database URL
   - `DJANGO_SETTINGS_MODULE`: `chronopars.settings`

## Step 3: Verify Deployment

1. **Check Build Logs:**
   - Ensure migrations run successfully
   - Verify fixtures are loaded with `seed_data` command
   - Look for "✓ Database seeded successfully!" message

2. **Test Application:**
   - Visit your Render app URL
   - Test login with existing users from development
   - Verify admin panel works with existing admin accounts
   - Check that master timetables are present

## Step 4: Future Data Management

### Adding New Data
When you add new timetables or make changes:

1. **In Development:**
   ```bash
   # Make your changes (add timetables, users, etc.)
   
   # Export updated data
   python manage.py dumpdata core.TimetableSource --indent 2 --output fixtures/timetables.json
   python manage.py dumpdata core.User --indent 2 --output fixtures/users.json
   python manage.py dumpdata core.CourseRegistrationHistory --indent 2 --output fixtures/course_history.json
   ```

2. **Deploy to Production:**
   ```bash
   git add fixtures/
   git commit -m "Update production data fixtures"
   git push
   ```

3. **Render automatically:**
   - Redeploys your app
   - Runs migrations
   - Loads updated fixtures
   - Preserves existing data in PostgreSQL

### Database Persistence Benefits
- ✅ PostgreSQL database persists across deployments
- ✅ Data is NOT lost when you redeploy your application
- ✅ Only new migrations and fixture updates are applied
- ✅ User accounts and course history remain intact
- ✅ Master timetables are preserved and updated

## Files Created for This Solution

### 1. Updated requirements.txt
```
psycopg2-binary==2.9.7  # PostgreSQL adapter
dj-database-url==2.1.0  # Database URL parsing
```

### 2. Updated chronopars/settings.py
```python
# Automatic database switching
if os.environ.get('DATABASE_URL'):
    # Production: PostgreSQL
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    # Development: SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

### 3. Data Fixtures (✓ Already created)
- `fixtures/users.json` - Your user accounts
- `fixtures/timetables.json` - Master timetables
- `fixtures/course_history.json` - Course registration history

### 4. Management Command
- `core/management/commands/seed_data.py` - Loads fixtures automatically

### 5. Deployment Configuration
- `render.yaml` - Automated deployment configuration

## Next Steps

1. **Deploy Now:**
   - Follow Step 1 & 2 above to set up PostgreSQL and deploy
   - Your current development data will be automatically loaded

2. **Test Everything:**
   - Login with your existing accounts
   - Verify all timetables are present
   - Test admin functionality

3. **Future Updates:**
   - Make changes in development
   - Export fixtures
   - Commit and push
   - Render handles the rest automatically

## Benefits of This Approach

✅ **No More Data Loss**: PostgreSQL persists across deployments
✅ **Synchronized Data**: Development fixtures automatically load to production  
✅ **Easy Updates**: Simple git push updates production data
✅ **Rollback Safety**: Database changes are versioned with your code
✅ **Cost Effective**: Uses Render's free PostgreSQL tier
✅ **Automatic**: No manual database management needed
