from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        help_text='Required. Enter a valid university email address.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Security: Force the role to STUDENT. 
        # This prevents any HTML manipulation from granting higher privileges.
        user.role = User.ROLE_STUDENT
        if commit:
            user.save()
        return user