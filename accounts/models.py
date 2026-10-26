from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_STUDENT = 'STUDENT'
    ROLE_STAFF = 'STAFF'
    ROLE_MANAGEMENT = 'MANAGEMENT'
    
    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_STAFF, 'Support Staff'),
        (ROLE_MANAGEMENT, 'Management'),
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default=ROLE_STUDENT
    )
    
    # Using string reference to avoid circular import with tickets.Department
    department = models.ForeignKey(
        'tickets.Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='staff_members'
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"