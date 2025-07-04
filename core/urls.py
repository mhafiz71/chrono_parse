# core/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import AdminDashboardView, StudentDashboardView, download_timetable_pdf, download_timetable_jpg


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('student_dashboard')
    else:
        return redirect('login')


urlpatterns = [
    path('', home_redirect, name='home'),
    path('dashboard/admin', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('student-dashboard/', StudentDashboardView.as_view(),
         name='student_dashboard'),
    # --- ADDED: URL for the download feature ---
    path('download-timetable/', download_timetable_pdf,
         name='download_timetable_pdf'),
    path('download-timetable-jpg/', download_timetable_jpg,
         name='download_timetable_jpg'),
]
