from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'tickets'

urlpatterns = [
    # Smart redirect: /tickets/ goes to the role-based router
    path('', RedirectView.as_view(pattern_name='accounts:role_redirect'), name='home'),
    
    # Student URLs
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    
    # Management URLs
    path('management/', views.management_dashboard, name='management_dashboard'),
    path('management/tickets/<int:pk>/', views.management_ticket_detail, name='management_ticket_detail'),
    path('management/create-staff/', views.create_staff, name='create_staff'),
    path('management/reports/', views.management_reports, name='management_reports'),
    
    # Staff URLs
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/tickets/<int:pk>/', views.staff_ticket_detail, name='staff_ticket_detail'),
]