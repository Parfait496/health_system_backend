from rest_framework.permissions import BasePermission
from Users.models import User


class IsPatientOwner(BasePermission):
    """Patient can only access their own profile."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CanViewPatient(BasePermission):
    """Doctors, admins can view any patient. Patient sees only their own."""
    def has_object_permission(self, request, view, obj):
        if request.user.role in [User.Role.ADMIN, User.Role.DOCTOR]:
            return True
        return obj.user == request.user