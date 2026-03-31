import uuid
from django.db import models
from Users.models import User
from patients.models import PatientProfile
from records.models import Prescription


class LabTest(models.Model):

    class Status(models.TextChoices):
        REQUESTED  = 'requested',  'Requested'
        COLLECTED  = 'collected',  'Sample Collected'
        PROCESSING = 'processing', 'Processing'
        COMPLETED  = 'completed',  'Completed'
        CANCELLED  = 'cancelled',  'Cancelled'

    class Priority(models.TextChoices):
        ROUTINE   = 'routine',   'Routine'
        URGENT    = 'urgent',    'Urgent'
        EMERGENCY = 'emergency', 'Emergency'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='lab_tests'
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lab_tests_requested',
        limit_choices_to={'role': 'doctor'}
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='lab_tests_assigned',
        limit_choices_to={'role': 'lab_tech'}
    )

    test_name = models.CharField(max_length=200)
    test_code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.ROUTINE
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED
    )

    # Clinical context
    clinical_notes = models.TextField(
        blank=True,
        help_text="Doctor's notes for the lab technician"
    )
    fasting_required = models.BooleanField(default=False)

    requested_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'lab_tests'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.test_name} for {self.patient.health_id} [{self.priority}]"


class LabResult(models.Model):
    """
    Uploaded by a lab technician when test is complete.
    Linked one-to-one with a LabTest.
    """
    class ResultStatus(models.TextChoices):
        NORMAL   = 'normal',   'Normal'
        ABNORMAL = 'abnormal', 'Abnormal'
        CRITICAL = 'critical', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    lab_test = models.OneToOneField(
        LabTest,
        on_delete=models.CASCADE,
        related_name='result'
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lab_results_performed'
    )

    result_value = models.TextField(
        help_text="The actual result — numeric value or descriptive text"
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. mmol/L, mg/dL, %"
    )
    reference_range = models.CharField(
        max_length=100,
        blank=True,
        help_text="Normal range e.g. 4.0-6.0"
    )
    result_status = models.CharField(
        max_length=20,
        choices=ResultStatus.choices,
        default=ResultStatus.NORMAL
    )
    interpretation = models.TextField(
        blank=True,
        help_text="Lab technician's interpretation"
    )
    report_file = models.FileField(
        upload_to='lab_reports/',
        null=True,
        blank=True
    )

    # Notification tracking
    patient_notified = models.BooleanField(default=False)
    doctor_notified = models.BooleanField(default=False)

    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lab_results'
        ordering = ['-performed_at']

    def __str__(self):
        return (
            f"Result for {self.lab_test.test_name} — "
            f"{self.lab_test.patient.health_id}"
        )