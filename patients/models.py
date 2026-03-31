import uuid
from django.db import models
from Users.models import User


class PatientProfile(models.Model):

    class BloodType(models.TextChoices):
        A_POS  = 'A+',  'A+'
        A_NEG  = 'A-',  'A-'
        B_POS  = 'B+',  'B+'
        B_NEG  = 'B-',  'B-'
        AB_POS = 'AB+', 'AB+'
        AB_NEG = 'AB-', 'AB-'
        O_POS  = 'O+',  'O+'
        O_NEG  = 'O-',  'O-'

    class InsuranceType(models.TextChoices):
        MUTUELLE   = 'mutuelle',   'Mutuelle de Santé'
        PRIVATE    = 'private',    'Private Insurance'
        MILITARY   = 'military',   'Military Insurance'
        NONE       = 'none',       'No Insurance'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # One patient user → one profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        limit_choices_to={'role': 'patient'}
    )

    # Unique health ID — generated automatically
    health_id = models.CharField(max_length=20, unique=True, editable=False)

    # Personal info
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True
    )
    address = models.TextField(blank=True)
    district = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)

    # Medical
    blood_type = models.CharField(
        max_length=3,
        choices=BloodType.choices,
        blank=True
    )
    allergies = models.TextField(blank=True, help_text='List known allergies')
    chronic_conditions = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)

    # Insurance
    insurance_type = models.CharField(
        max_length=20,
        choices=InsuranceType.choices,
        default=InsuranceType.NONE
    )
    insurance_number = models.CharField(max_length=50, blank=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patient_profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.health_id} — {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        # Auto-generate health ID on first save
        if not self.health_id:
            self.health_id = self._generate_health_id()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_health_id():
        """
        Generates a unique Rwanda health ID.
        Format: RW-YYYY-XXXXXXXX
        Example: RW-2026-A3F9B2C1
        """
        from django.utils import timezone
        year = timezone.now().year
        unique_part = uuid.uuid4().hex[:8].upper()
        health_id = f"RW-{year}-{unique_part}"
        # Ensure uniqueness
        while PatientProfile.objects.filter(health_id=health_id).exists():
            unique_part = uuid.uuid4().hex[:8].upper()
            health_id = f"RW-{year}-{unique_part}"
        return health_id


class MedicalHistory(models.Model):
    """
    Tracks significant medical events for a patient.
    Each entry is immutable — doctors can add but not edit history.
    """
    class EventType(models.TextChoices):
        DIAGNOSIS   = 'diagnosis',   'Diagnosis'
        SURGERY     = 'surgery',     'Surgery'
        ALLERGY     = 'allergy',     'Allergy'
        VACCINATION = 'vaccination', 'Vaccination'
        HOSPITALIZATION = 'hospitalization', 'Hospitalization'
        OTHER       = 'other',       'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='medical_history'
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_histories'
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medical_history'
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.patient.health_id} — {self.title}"