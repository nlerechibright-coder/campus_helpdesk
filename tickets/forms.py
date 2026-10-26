from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Ticket, Department, TicketUpdate

User = get_user_model()

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['department', 'subject', 'description']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].empty_label = "Select a department..."
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary focus:border-primary outline-none transition'
            })

class ManagementTicketActionForm(forms.Form):
    status = forms.ChoiceField(
        choices=Ticket.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary focus:border-primary outline-none transition'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(role='STAFF'),
        required=False,
        empty_label="Unassigned",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary focus:border-primary outline-none transition'})
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary focus:border-primary outline-none transition',
            'placeholder': 'Add a response to the student or an internal note...'
        })
    )
    is_internal_note = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-primary border-gray-300 rounded focus:ring-primary'})
    )

class StaffCreationForm(UserCreationForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=True,
        empty_label="Select a department...",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary focus:border-primary outline-none transition'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'department', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_STAFF
        if commit:
            user.save()
        return user

# NEW: Form for Staff to update tickets
class StaffTicketUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Ticket.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary focus:border-primary outline-none transition'})
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary focus:border-primary outline-none transition',
            'placeholder': 'Add a progress update or response to the student...'
        })
    )
    is_internal_note = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-primary border-gray-300 rounded focus:ring-primary'})
    )