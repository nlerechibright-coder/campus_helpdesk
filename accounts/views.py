from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .forms import StudentRegistrationForm

def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:role_redirect')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def role_redirect(request):
    """
    Traffic cop: Redirects users to the correct dashboard based on their role.
    """
    if request.user.role == 'STUDENT':
        return redirect('tickets:student_dashboard')
    elif request.user.role == 'MANAGEMENT':
        return redirect('tickets:management_dashboard')
    elif request.user.role == 'STAFF':
        return redirect('tickets:staff_dashboard')
    
    # Fallback
    return redirect('accounts:login')

class CustomLoginView(LoginView):
    """
    Custom login view that redirects already-authenticated users.
    """
    template_name = 'accounts/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already authenticated, redirect them immediately
        if request.user.is_authenticated:
            return redirect('accounts:role_redirect')
        # Otherwise, proceed with normal login
        return super().dispatch(request, *args, **kwargs)