# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

class TimetableSource(models.Model):
    academic_year = models.CharField(max_length=10)
    semester = models.CharField(max_length=20)
    display_name = models.CharField(max_length=255)
    # --- RENAMED: from source_pdf to source_json ---
    source_json = models.FileField(upload_to='master_timetables/')
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name