import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN       = 'admin',      'Admin'
        DOCTOR      = 'doctor',     'Doctor'
        PATIENT     = 'patient',    'Patient'
        PHARMACIST  = 'pharmacist', 'Pharmacist'
        LAB_TECH    = 'lab_tech',   'Lab Technician'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT
    )
    phone_number = models.CharField(max_length=20, blank=True)
    national_id = models.CharField(max_length=20, blank=True, unique=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'role']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_pharmacist(self):
        return self.role == self.Role.PHARMACIST

    @property
    def is_lab_tech(self):
        return self.role == self.Role.LAB_TECH