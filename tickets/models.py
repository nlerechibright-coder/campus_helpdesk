from django.db import models
from django.conf import settings
import datetime

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Departments"
        ordering = ['name']

    def __str__(self):
        return self.name


class Ticket(models.Model):
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # PROTECT ensures historical tickets are not deleted if a user/department is removed
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='student_tickets'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT, 
        related_name='department_tickets'
    )
    
    # SET_NULL ensures the ticket remains if a staff member is deleted, but becomes unassigned
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tickets',
        limit_choices_to={'role': 'STAFF'} # Only staff can be assigned
    )
    
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate unique ticket number only on creation
        if not self.ticket_number:
            today = datetime.date.today().strftime('%Y%m%d')
            prefix = f"TKT-{today}-"
            
            # Find the highest number for today to prevent collisions
            last_ticket = self.__class__.objects.filter(ticket_number__startswith=prefix).order_by('-ticket_number').first()
            if last_ticket:
                last_num = int(last_ticket.ticket_number[-4:])
                new_num = f"{last_num + 1:04d}"
            else:
                new_num = "0001"
                
            self.ticket_number = f"{prefix}{new_num}"
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"


class TicketUpdate(models.Model):
    TYPE_COMMENT = 'COMMENT'
    TYPE_INTERNAL_NOTE = 'INTERNAL_NOTE'
    TYPE_STATUS_CHANGE = 'STATUS_CHANGE'
    TYPE_ASSIGNMENT_CHANGE = 'ASSIGNMENT_CHANGE'

    UPDATE_TYPE_CHOICES = [
        (TYPE_COMMENT, 'Comment'),
        (TYPE_INTERNAL_NOTE, 'Internal Note'),
        (TYPE_STATUS_CHANGE, 'Status Change'),
        (TYPE_ASSIGNMENT_CHANGE, 'Assignment Change'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPE_CHOICES)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Update on {self.ticket.ticket_number} by {self.author.username}"