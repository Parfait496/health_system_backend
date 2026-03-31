import uuid
from django.db import models
from Users.models import User
from patients.models import PatientProfile
from records.models import Prescription


class Medication(models.Model):
    """
    Master list of medications available in the system.
    Pharmacists manage this inventory.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    unit = models.CharField(
        max_length=50,
        help_text="e.g. tablets, capsules, ml"
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(
        default=50,
        help_text="Alert when stock falls below this"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    requires_prescription = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'medications'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.unit} in stock)"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level


class Dispensing(models.Model):
    """
    Records when a pharmacist dispenses medication
    against a prescription.
    """
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        DISPENSED  = 'dispensed',  'Dispensed'
        PARTIAL    = 'partial',    'Partially Dispensed'
        REFUSED    = 'refused',    'Refused'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    prescription = models.OneToOneField(
        Prescription,
        on_delete=models.CASCADE,
        related_name='dispensing'
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='dispensings'
    )
    dispensed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dispensings_done',
        limit_choices_to={'role': 'pharmacist'}
    )
    medication = models.ForeignKey(
        Medication,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dispensings'
    )

    quantity_dispensed = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    notes = models.TextField(blank=True)
    dispensed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dispensings'
        ordering = ['-dispensed_at']

    def __str__(self):
        return (
            f"{self.prescription.medication_name} dispensed to "
            f"{self.patient.health_id}"
        )

    def save(self, *args, **kwargs):
        # Deduct from stock when dispensed
        if self.status == self.Status.DISPENSED and self.medication:
            if self.medication.stock_quantity >= self.quantity_dispensed:
                self.medication.stock_quantity -= self.quantity_dispensed
                self.medication.save()
        super().save(*args, **kwargs)