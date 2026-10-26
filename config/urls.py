from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('tickets/', include('tickets.urls')),
    # Redirect root URL to the login page
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False), name='home'),
]