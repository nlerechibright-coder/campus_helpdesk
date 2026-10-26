from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Ticket, TicketUpdate
from .forms import TicketForm, ManagementTicketActionForm, StaffCreationForm, StaffTicketUpdateForm

def is_student(user):
    return user.is_authenticated and user.role == 'STUDENT'

@login_required
@user_passes_test(is_student, login_url='accounts:login')
def student_dashboard(request):
    recent_tickets = Ticket.objects.filter(student=request.user).order_by('-created_at')[:5]
    return render(request, 'tickets/student_dashboard.html', {'recent_tickets': recent_tickets})

@login_required
@user_passes_test(is_student, login_url='accounts:login')
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.student = request.user
            ticket.save()
            messages.success(request, f'Ticket submitted successfully! Your ticket number is {ticket.ticket_number}.')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm()
    return render(request, 'tickets/create_ticket.html', {'form': form})

@login_required
@user_passes_test(is_student, login_url='accounts:login')
def ticket_list(request):
    tickets = Ticket.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets})

@login_required
@user_passes_test(is_student, login_url='accounts:login')
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, student=request.user)
    updates = ticket.updates.exclude(update_type=TicketUpdate.TYPE_INTERNAL_NOTE)
    return render(request, 'tickets/ticket_detail.html', {'ticket': ticket, 'updates': updates})

# --- MANAGEMENT VIEWS ---

@login_required
@user_passes_test(lambda u: u.role == 'MANAGEMENT', login_url='accounts:login')
def management_dashboard(request):
    total_tickets = Ticket.objects.count()
    submitted_tickets = Ticket.objects.filter(status=Ticket.STATUS_SUBMITTED).count()
    in_progress_tickets = Ticket.objects.filter(status__in=[
        Ticket.STATUS_UNDER_REVIEW, Ticket.STATUS_ASSIGNED, Ticket.STATUS_IN_PROGRESS
    ]).count()
    resolved_tickets = Ticket.objects.filter(status__in=[
        Ticket.STATUS_RESOLVED, Ticket.STATUS_CLOSED
    ]).count()
    
    tickets = Ticket.objects.select_related('student', 'department', 'assigned_to').order_by('-created_at')
    
    search_query = request.GET.get('search', '')
    if search_query:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(student__username__icontains=search_query)
        )
    
    context = {
        'total_tickets': total_tickets,
        'submitted_tickets': submitted_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
        'tickets': tickets,
        'search_query': search_query,
    }
    return render(request, 'tickets/management_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'MANAGEMENT', login_url='accounts:login')
def management_ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    updates = ticket.updates.all()
    
    if request.method == 'POST':
        form = ManagementTicketActionForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            new_assigned_to = form.cleaned_data['assigned_to']
            message = form.cleaned_data['message']
            is_internal = form.cleaned_data['is_internal_note']
            
            status_changed = ticket.status != new_status
            assignment_changed = ticket.assigned_to != new_assigned_to
            
            ticket.status = new_status
            ticket.assigned_to = new_assigned_to
            ticket.save()
            
            if status_changed:
                TicketUpdate.objects.create(
                    ticket=ticket, author=request.user, update_type=TicketUpdate.TYPE_STATUS_CHANGE,
                    message=f"Status changed to {dict(Ticket.STATUS_CHOICES).get(new_status)}"
                )
            if assignment_changed:
                assignee_name = new_assigned_to.username if new_assigned_to else "Unassigned"
                TicketUpdate.objects.create(
                    ticket=ticket, author=request.user, update_type=TicketUpdate.TYPE_ASSIGNMENT_CHANGE,
                    message=f"Ticket assigned to: {assignee_name}"
                )
            if message:
                update_type = TicketUpdate.TYPE_INTERNAL_NOTE if is_internal else TicketUpdate.TYPE_COMMENT
                TicketUpdate.objects.create(
                    ticket=ticket, author=request.user, update_type=update_type, message=message
                )
            messages.success(request, 'Ticket updated successfully.')
            return redirect('tickets:management_ticket_detail', pk=ticket.pk)
    else:
        initial_data = {'status': ticket.status, 'assigned_to': ticket.assigned_to}
        form = ManagementTicketActionForm(initial=initial_data)
    
    return render(request, 'tickets/management_ticket_detail.html', {'ticket': ticket, 'updates': updates, 'form': form})

@login_required
@user_passes_test(lambda u: u.role == 'MANAGEMENT', login_url='accounts:login')
def create_staff(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Staff account "{user.username}" created successfully and assigned to {user.department.name}.')
            return redirect('tickets:management_dashboard')
    else:
        form = StaffCreationForm()
    return render(request, 'tickets/create_staff.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.role == 'MANAGEMENT', login_url='accounts:login')
def management_reports(request):
    # 1. Handle Date Range Filtering
    date_filter = request.GET.get('date_filter', 'all')
    now = timezone.now()
    
    if date_filter == '7days':
        start_date = now - timedelta(days=7)
    elif date_filter == '30days':
        start_date = now - timedelta(days=30)
    else:
        start_date = None

    base_queryset = Ticket.objects.all()
    if start_date:
        base_queryset = base_queryset.filter(created_at__gte=start_date)

    # 2. Calculate Core Metrics
    total_tickets = base_queryset.count()
    
    # Status breakdown
    status_counts = base_queryset.values('status').annotate(count=Count('id')).order_by('-count')
    
    # Department breakdown
    dept_counts = base_queryset.values('department__name').annotate(count=Count('id')).order_by('-count')
    
    # Average lifecycle time for resolved/closed tickets (in hours)
    resolved_tickets = base_queryset.filter(status__in=[Ticket.STATUS_RESOLVED, Ticket.STATUS_CLOSED])
    
    total_hours = 0
    count_with_time = 0
    for t in resolved_tickets:
        if t.updated_at and t.created_at:
            delta = t.updated_at - t.created_at
            total_hours += delta.total_seconds() / 3600
            count_with_time += 1
    
    avg_resolution_hours = (total_hours / count_with_time) if count_with_time > 0 else 0

    context = {
        'total_tickets': total_tickets,
        'status_counts': status_counts,
        'dept_counts': dept_counts,
        'avg_resolution_hours': round(avg_resolution_hours, 1),
        'resolved_count': count_with_time,
        'date_filter': date_filter,
    }
    return render(request, 'tickets/management_reports.html', context)

# --- STAFF VIEWS (PHASE 6) ---

@login_required
@user_passes_test(lambda u: u.role == 'STAFF', login_url='accounts:login')
def staff_dashboard(request):
    tickets = Ticket.objects.filter(
        Q(assigned_to=request.user) | Q(department=request.user.department)
    ).select_related('student', 'department', 'assigned_to').order_by('-updated_at')
    
    search_query = request.GET.get('search', '')
    if search_query:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(student__username__icontains=search_query)
        )
    
    my_tickets = tickets.count()
    pending_tickets = tickets.filter(status__in=[Ticket.STATUS_SUBMITTED, Ticket.STATUS_UNDER_REVIEW, Ticket.STATUS_ASSIGNED]).count()
    resolved_tickets = tickets.filter(status__in=[Ticket.STATUS_RESOLVED, Ticket.STATUS_CLOSED]).count()

    context = {
        'tickets': tickets,
        'search_query': search_query,
        'my_tickets': my_tickets,
        'pending_tickets': pending_tickets,
        'resolved_tickets': resolved_tickets,
    }
    return render(request, 'tickets/staff_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'STAFF', login_url='accounts:login')
def staff_ticket_detail(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.filter(
            Q(assigned_to=request.user) | Q(department=request.user.department)
        ),
        pk=pk
    )
    updates = ticket.updates.all()

    if request.method == 'POST':
        form = StaffTicketUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            message = form.cleaned_data['message']
            is_internal = form.cleaned_data['is_internal_note']

            if ticket.status != new_status:
                ticket.status = new_status
                ticket.save()
                TicketUpdate.objects.create(
                    ticket=ticket, author=request.user, update_type=TicketUpdate.TYPE_STATUS_CHANGE,
                    message=f"Status changed to {dict(Ticket.STATUS_CHOICES).get(new_status)}"
                )
            
            if message:
                update_type = TicketUpdate.TYPE_INTERNAL_NOTE if is_internal else TicketUpdate.TYPE_COMMENT
                TicketUpdate.objects.create(
                    ticket=ticket, author=request.user, update_type=update_type, message=message
                )
            
            messages.success(request, 'Ticket updated successfully.')
            return redirect('tickets:staff_ticket_detail', pk=ticket.pk)
    else:
        form = StaffTicketUpdateForm(initial={'status': ticket.status})

    return render(request, 'tickets/staff_ticket_detail.html', {'ticket': ticket, 'updates': updates, 'form': form})