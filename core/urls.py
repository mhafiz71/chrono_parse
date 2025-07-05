# core/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import AdminDashboardView, StudentDashboardView, SignupView, UserProfileView, download_timetable_pdf, download_timetable_jpg, delete_timetable_source, reuse_course_registration


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('student_dashboard')
    else:
        return redirect('login')


urlpatterns = [
    path('', home_redirect, name='home'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('dashboard/admin', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('student-dashboard/', StudentDashboardView.as_view(),
         name='student_dashboard'),
    # --- ADDED: URL for the download feature ---
    path('download-timetable/', download_timetable_pdf,
         name='download_timetable_pdf'),
    path('download-timetable-jpg/', download_timetable_jpg,
         name='download_timetable_jpg'),
    # --- ADDED: URL for delete functionality ---
    path('delete-timetable/<int:source_id>/', delete_timetable_source,
         name='delete_timetable_source'),
    # --- ADDED: URL for reusing course registration ---
    path('reuse-registration/<int:history_id>/', reuse_course_registration,
         name='reuse_course_registration'),
]
