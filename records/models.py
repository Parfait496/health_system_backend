import uuid
from django.db import models
from Users.models import User
from patients.models import PatientProfile
from appointments.models import Appointment


class ClinicalNote(models.Model):
    """
    Written by a doctor during or after a consultation.
    Linked to an appointment — one appointment can have one note.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='clinical_notes'
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='clinical_notes',
        limit_choices_to={'role': 'doctor'}
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinical_note'
    )

    subjective = models.TextField(
        help_text="Patient's complaints and symptoms in their own words"
    )
    objective = models.TextField(
        help_text="Doctor's observations, vitals, exam findings"
    )
    assessment = models.TextField(
        help_text="Doctor's clinical assessment and interpretation"
    )
    plan = models.TextField(
        help_text="Treatment plan, follow-ups, referrals"
    )

    # Vitals
    temperature = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        help_text="Celsius"
    )
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    pulse_rate = models.PositiveIntegerField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        help_text="SpO2 percentage"
    )
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    height_cm = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )

    is_finalized = models.BooleanField(
        default=False,
        help_text="Finalized notes cannot be edited"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_notes'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"Note for {self.patient.health_id} "
            f"by Dr.{self.doctor.get_full_name()} "
            f"on {self.created_at.date()}"
        )

    @property
    def bmi(self):
        if self.weight_kg and self.height_cm and self.height_cm > 0:
            height_m = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (height_m ** 2), 1)
        return None


class Diagnosis(models.Model):
    """
    Formal diagnosis attached to a clinical note.
    Uses ICD-10 style coding.
    """
    class Severity(models.TextChoices):
        MILD     = 'mild',     'Mild'
        MODERATE = 'moderate', 'Moderate'
        SEVERE   = 'severe',   'Severe'
        CRITICAL = 'critical', 'Critical'

    class DiagnosisType(models.TextChoices):
        PRIMARY   = 'primary',   'Primary'
        SECONDARY = 'secondary', 'Secondary'
        CHRONIC   = 'chronic',   'Chronic'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    clinical_note = models.ForeignKey(
        ClinicalNote,
        on_delete=models.CASCADE,
        related_name='diagnoses'
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='diagnoses'
    )
    diagnosed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='diagnoses_made'
    )

    icd_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="ICD-10 code e.g. E11 for Type 2 Diabetes"
    )
    condition_name = models.CharField(max_length=200)
    diagnosis_type = models.CharField(
        max_length=20,
        choices=DiagnosisType.choices,
        default=DiagnosisType.PRIMARY
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MILD
    )
    notes = models.TextField(blank=True)
    diagnosed_date = models.DateField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnoses'
        ordering = ['-diagnosed_date']

    def __str__(self):
        return f"{self.condition_name} ({self.icd_code}) — {self.patient.health_id}"


class Prescription(models.Model):
    """
    Medication prescribed to a patient.
    Linked to both a clinical note and directly to the patient
    so pharmacy can access it without needing the full note.
    """
    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        DISPENSED = 'dispensed', 'Dispensed'
        EXPIRED   = 'expired',   'Expired'
        CANCELLED = 'cancelled', 'Cancelled'

    class Frequency(models.TextChoices):
        ONCE_DAILY    = 'once_daily',    'Once daily'
        TWICE_DAILY   = 'twice_daily',   'Twice daily'
        THREE_DAILY   = 'three_daily',   'Three times daily'
        FOUR_DAILY    = 'four_daily',    'Four times daily'
        EVERY_8_HOURS = 'every_8_hours', 'Every 8 hours'
        AS_NEEDED     = 'as_needed',     'As needed'
        WEEKLY        = 'weekly',        'Weekly'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    clinical_note = models.ForeignKey(
        ClinicalNote,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    prescribed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescriptions_written'
    )

    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, help_text="e.g. 500mg")
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.TWICE_DAILY
    )
    duration_days = models.PositiveIntegerField(help_text="Number of days")
    quantity = models.PositiveIntegerField(help_text="Total units to dispense")
    instructions = models.TextField(
        blank=True,
        help_text="Special instructions e.g. take with food"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    start_date = models.DateField()
    end_date = models.DateField()

    # Audit
    dispensed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prescriptions_dispensed'
    )
    dispensed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.medication_name} {self.dosage} "
            f"for {self.patient.health_id}"
        )