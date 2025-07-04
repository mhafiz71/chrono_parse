# core/views.py
import re
import json
from io import BytesIO
from datetime import time as dt_time, datetime

import pdfplumber
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from xhtml2pdf import pisa
from PIL import Image, ImageDraw, ImageFont
import base64

from .forms import TimetableSourceForm
from .models import TimetableSource

# Simple class to convert dictionary to object for template access


class EventObject:
    def __init__(self, event_dict):
        for key, value in event_dict.items():
            setattr(self, key, value)

# --- HELPER 1: For parsing time like "7:00a - 9:55a" ---


def parse_time_range(time_str):
    try:
        start_str, end_str = time_str.split(' - ')

        # Handle both "7:00a" and "7:00AM" formats
        # Convert single letter suffixes to full AM/PM
        if start_str.endswith('a'):
            start_str = start_str[:-1] + 'AM'
        elif start_str.endswith('p'):
            start_str = start_str[:-1] + 'PM'

        if end_str.endswith('a'):
            end_str = end_str[:-1] + 'AM'
        elif end_str.endswith('p'):
            end_str = end_str[:-1] + 'PM'

        start_time = datetime.strptime(start_str, '%I:%M%p').time()
        end_time = datetime.strptime(end_str, '%I:%M%p').time()
        return start_time, end_time
    except (ValueError, AttributeError):
        return None, None

# --- HELPER 2 (FIXED): Robust parser for course strings ---


def parse_course_string(course_str):
    """
    Finds a course code like 'ACT 404' or 'ENV324' within a larger string,
    and returns the display version, a normalized version, and the details.
    """
    # This regex finds "3-4 letters, optional space, 3 digits"
    # Made more flexible to handle various formats
    match = re.search(r'([A-Z]{3,4})\s?(\d{3})', course_str.upper())
    if match:
        dept_code = match.group(1)  # e.g., "ACT"
        course_num = match.group(2)  # e.g., "404"

        # Create both display and normalized versions
        display_code = f"{dept_code} {course_num}"  # e.g., "ACT 404"
        normalized_code = f"{dept_code} {course_num}"  # e.g., "ACT404"

        # Extract details (everything after the course code)
        details = course_str[match.end():].strip()  # e.g., "Lec 1"

        return display_code, normalized_code, details

    # Fallback if no standard code is found
    return course_str, course_str.replace(' ', ''), ''

# --- HELPER 3 (NEW): Normalize course codes consistently ---


def normalize_course_code(code_str):
    """
    Normalizes course codes to a consistent format for matching.
    Handles various input formats like 'ACT 404', 'ACT404', 'act 404', etc.
    """
    if not code_str:
        return ""

    # Clean the string
    clean_code = code_str.strip().upper()

    # Try to match the pattern
    match = re.search(r'([A-Z]{3,4})\s?(\d{3})', clean_code)
    if match:
        dept_code = match.group(1)
        course_num = match.group(2)
        return f"{dept_code} {course_num}"  # Always return without spaces

    # If no match, return the cleaned version
    return clean_code.replace(' ', '')

# --- UPDATED: The JSON parser now uses the improved helpers ---


def parse_master_timetable(source):
    """Parses a master timetable JSON and returns a list of event dictionaries."""
    events = []
    try:
        with open(source.source_json.path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                start_time, end_time = parse_time_range(item.get("Time"))
                display_code, normalized_code, details = parse_course_string(
                    item.get("Course", ""))

                if not all([start_time, end_time, display_code]):
                    continue

                events.append({
                    'day': item.get("Day", "").title(),
                    'start_time': start_time,
                    'end_time': end_time,
                    'location': item.get("Venue", ""),
                    # For display (e.g., "ACT 404")
                    'course_code': display_code,
                    # For matching (e.g., "ACT404")
                    'normalized_code': normalized_code,
                    'details': details,
                    'lecturer': item.get("Instructor(s)", ""),
                })
    except Exception as e:
        print(f"Error parsing master JSON {source.id}: {e}")
    return events

# get_master_schedule_data uses the cache for performance


def get_master_schedule_data(source_id):
    """Retrieves master schedule, using cache or parsing the JSON and caching it."""
    cache_key = f'master_schedule_{source_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    try:
        source = TimetableSource.objects.get(id=source_id)
        schedule_data = parse_master_timetable(source)
        if schedule_data:  # Only cache if parsing was successful
            cache.set(cache_key, schedule_data, 3600)  # Cache for 1 hour
        return schedule_data
    except TimetableSource.DoesNotExist:
        return []

# AdminDashboardView has no major changes


class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        form = TimetableSourceForm()
        timetables = TimetableSource.objects.all().order_by('-created_at')
        return render(request, 'core/admin_dashboard.html', {'form': form, 'timetables': timetables})

    def post(self, request):
        form = TimetableSourceForm(request.POST, request.FILES)
        if form.is_valid():
            timetable_source = form.save(commit=False)
            timetable_source.uploader = request.user
            timetable_source.save()
            messages.success(
                request, f"'{timetable_source.display_name}' has been uploaded successfully.")
            return redirect('admin_dashboard')

        timetables = TimetableSource.objects.all().order_by('-created_at')
        return render(request, 'core/admin_dashboard.html', {'form': form, 'timetables': timetables})


# --- FIXED: StudentDashboardView with improved course code extraction and matching ---
class StudentDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        sources = TimetableSource.objects.all().order_by('-created_at')
        return render(request, 'core/student_dashboard.html', {'sources': sources})

    def post(self, request):
        sources = TimetableSource.objects.all().order_by('-created_at')
        source_id = request.POST.get('timetable_source')
        course_reg_pdf = request.FILES.get('course_reg_pdf')

        if not source_id or not course_reg_pdf:
            messages.error(
                request, 'Please select a timetable and upload your file.')
            return render(request, 'core/student_dashboard.html', {'sources': sources})

        student_course_codes = set()
        raw_extracted_codes = []  # For debugging

        try:
            with pdfplumber.open(course_reg_pdf) as pdf:
                for page in pdf.pages:
                    # Try table extraction first
                    table = page.extract_table()
                    if table:
                        for row in table[1:]:  # Skip header
                            if row and len(row) > 1 and row[1]:
                                course_code = row[1].strip()
                                raw_extracted_codes.append(course_code)
                                normalized = normalize_course_code(course_code)
                                if normalized:
                                    student_course_codes.add(normalized)

                    # Also try text extraction as backup
                    text = page.extract_text()
                    if text:
                        # Find course codes in text using regex
                        course_matches = re.findall(
                            r'([A-Z]{3,4})\s?(\d{3})', text.upper())
                        for match in course_matches:
                            course_code = f"{match[0]} {match[1]}"
                            raw_extracted_codes.append(course_code)
                            normalized = normalize_course_code(course_code)
                            if normalized:
                                student_course_codes.add(normalized)

        except Exception as e:
            messages.error(request, f'Could not process your PDF. Error: {e}')
            return render(request, 'core/student_dashboard.html', {'sources': sources})

        if not student_course_codes:
            messages.warning(
                request, 'No course codes found in your PDF. Please check if the file contains a valid course registration.')
            return render(request, 'core/student_dashboard.html', {'sources': sources})

        master_schedule = get_master_schedule_data(source_id)

        # Filter matching events
        student_events = []
        for event in master_schedule:
            event_code = event.get('normalized_code')
            if event_code in student_course_codes:
                student_events.append(event)

        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        # Sort events by start time within each day
        schedule = {
            day: sorted([e for e in student_events if e['day']
                        == day], key=lambda x: x['start_time'])
            for day in days_of_week
        }

        return render(request, 'core/student_dashboard.html', {
            'sources': sources,
            'schedule': schedule,
            'processed_codes': list(student_course_codes),
            'raw_codes': raw_extracted_codes,  # For debugging
            'selected_source_id': int(source_id)
        })

# --- UPDATED: download_timetable_pdf with consistent normalization ---


@login_required
def download_timetable_pdf(request):
    source_id = request.GET.get('source_id')
    course_codes_str = request.GET.get('codes', '')
    template_type = request.GET.get('template', 'modern')  # Default to modern
    course_codes = [normalize_course_code(
        code) for code in course_codes_str.split(',') if code.strip()]

    if not source_id or not course_codes:
        return HttpResponse("Invalid request.", status=400)

    master_schedule = get_master_schedule_data(source_id)
    student_events = [e for e in master_schedule if e.get(
        'normalized_code') in course_codes]

    try:
        source = TimetableSource.objects.get(id=source_id)
    except TimetableSource.DoesNotExist:
        return HttpResponse("Timetable source not found.", status=404)

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Convert event dictionaries to objects for template access
    event_objects = [EventObject(e) for e in student_events]
    schedule = {day: sorted([e for e in event_objects if e.day == day],
                            key=lambda x: x.start_time) for day in days_of_week}

    # Select template based on user choice
    template_map = {
        'modern': 'core/timetable_pdf_modern.html',
        'minimal': 'core/timetable_pdf_minimal.html',
        'neon': 'core/timetable_pdf_neon.html',
        'grid': 'core/timetable_pdf_grid.html'
    }

    template_path = template_map.get(
        template_type, 'core/timetable_pdf_modern.html')
    template = get_template(template_path)
    html = template.render(
        {'schedule': schedule, 'days_of_week': days_of_week, 'source_name': source.display_name, 'template_type': template_type})

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(
            result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="my_timetable.pdf"'
        return response

    return HttpResponse("Error Generating PDF", status=500)


@login_required
def download_timetable_jpg(request):
    """Generate and download timetable as JPG image"""
    source_id = request.GET.get('source_id')
    course_codes_str = request.GET.get('codes', '')
    template_type = request.GET.get('template', 'modern')
    course_codes = [normalize_course_code(
        code) for code in course_codes_str.split(',') if code.strip()]

    if not source_id or not course_codes:
        return HttpResponse("Invalid request.", status=400)

    master_schedule = get_master_schedule_data(source_id)
    student_events = [e for e in master_schedule if e.get(
        'normalized_code') in course_codes]

    try:
        source = TimetableSource.objects.get(id=source_id)
    except TimetableSource.DoesNotExist:
        return HttpResponse("Timetable source not found.", status=404)

    # Create image using PIL
    img_width, img_height = 1200, 800
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)

    try:
        # Try to use a better font
        title_font = ImageFont.truetype("arial.ttf", 24)
        header_font = ImageFont.truetype("arial.ttf", 16)
        text_font = ImageFont.truetype("arial.ttf", 12)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # Draw title
    title = f"My Timetable - {source.display_name}"
    draw.text((50, 30), title, fill='black', font=title_font)

    # Draw table headers
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    times = ["8:00", "9:00", "10:00", "11:00", "12:00",
             "13:00", "14:00", "15:00", "16:00", "17:00"]

    cell_width = 110
    cell_height = 120
    start_x, start_y = 50, 80

    # Draw time headers
    for i, time_slot in enumerate(times):
        x = start_x + (i + 1) * cell_width
        draw.rectangle([x, start_y, x + cell_width, start_y + 40],
                       outline='black', fill='#667eea')
        draw.text((x + 10, start_y + 10), time_slot,
                  fill='white', font=header_font)

    # Draw day rows and events
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    event_objects = [EventObject(e) for e in student_events]
    schedule = {day: sorted([e for e in event_objects if e.day == day],
                            key=lambda x: x.start_time) for day in days_of_week}

    for day_idx, day in enumerate(days):
        y = start_y + 40 + day_idx * cell_height

        # Draw day header
        draw.rectangle([start_x, y, start_x + cell_width, y +
                       cell_height], outline='black', fill='#4a5568')
        draw.text((start_x + 10, y + 50), day, fill='white', font=header_font)

        # Draw time slots for this day
        day_events = schedule.get(day, [])
        for time_idx in range(len(times)):
            x = start_x + (time_idx + 1) * cell_width
            draw.rectangle([x, y, x + cell_width, y + cell_height],
                           outline='black', fill='#fafafa')

            # Find events for this time slot
            hour = time_idx + 8
            for event in day_events:
                if event.start_time.hour == hour:
                    # Draw event
                    draw.rectangle([x + 5, y + 5, x + cell_width - 5, y + cell_height - 5],
                                   outline='#667eea', fill='#667eea')

                    # Draw event text
                    course_text = event.course_code
                    time_text = f"{event.start_time.hour}:{event.start_time.minute:02d}-{event.end_time.hour}:{event.end_time.minute:02d}"
                    location_text = event.location[:15] if len(
                        event.location) > 15 else event.location

                    draw.text((x + 10, y + 15), course_text,
                              fill='white', font=text_font)
                    draw.text((x + 10, y + 35), time_text,
                              fill='white', font=text_font)
                    draw.text((x + 10, y + 55), location_text,
                              fill='white', font=text_font)

    # Save image to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG', quality=95)
    img_buffer.seek(0)

    response = HttpResponse(img_buffer.getvalue(), content_type='image/jpeg')
    response['Content-Disposition'] = 'attachment; filename="my_timetable.jpg"'
    return response
