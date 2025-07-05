# core/models.py
import json
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

class TimetableSource(models.Model):
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

    STATUS_CHOICES = [
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    academic_year = models.CharField(max_length=10)
    semester = models.CharField(max_length=20)
    display_name = models.CharField(max_length=255)
    # --- RENAMED: from source_pdf to source_json ---
    source_json = models.FileField(upload_to='master_timetables/')
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=PROCESSING)
    events_parsed = models.BooleanField(default=False)
    total_events = models.IntegerField(default=0)

    def __str__(self):
        return self.display_name


class TimetableEvent(models.Model):
    source = models.ForeignKey(
        TimetableSource, on_delete=models.CASCADE, related_name='events')
    day = models.CharField(max_length=10, db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    course_code = models.CharField(max_length=20, db_index=True)
    normalized_code = models.CharField(max_length=20, db_index=True)
    details = models.CharField(max_length=100, blank=True, null=True)
    lecturer = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['source', 'normalized_code']),
            models.Index(fields=['day', 'start_time']),
        ]


class CourseRegistrationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(TimetableSource, on_delete=models.CASCADE)
    course_codes = models.TextField()  # JSON string of course codes
    display_name = models.CharField(max_length=255)
    # e.g., "BSC Computer Science"
    program = models.CharField(max_length=100, blank=True, null=True)
    # e.g., "Level 200", "Year 2"
    level = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_used']

    def get_course_count(self):
        """Get the number of courses in this registration."""
        try:
            return len(json.loads(self.course_codes))
        except:
            return 0

    def __str__(self):
        return f"{self.user.username} - {self.display_name}"
