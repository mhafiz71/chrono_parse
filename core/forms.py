# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import TimetableSource

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'login-input block w-full px-3 py-2.5 rounded-lg text-sm',
            'placeholder': 'username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'login-input block w-full px-3 py-2.5 rounded-lg text-sm',
            'placeholder': '••••••••'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'login-input block w-full px-3 py-2.5 rounded-lg text-sm',
            'placeholder': '••••••••'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input-modern block w-full px-4 py-3 rounded-lg',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input-modern block w-full px-4 py-3 rounded-lg',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-modern block w-full px-4 py-3 rounded-lg',
                'placeholder': 'your.email@example.com'
            }),
            'role': forms.Select(attrs={
                'class': 'input-modern block w-full px-4 py-3 rounded-lg',
            }),
        }


class TimetableSourceForm(forms.ModelForm):
    class Meta:
        model = TimetableSource
        fields = ['academic_year', 'semester', 'display_name', 'source_json']
        widgets = {
            'academic_year': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'}),
            'semester': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'}),
            'display_name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'}),
            'source_json': forms.FileInput(attrs={'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100', 'accept': '.json'}),
        }
