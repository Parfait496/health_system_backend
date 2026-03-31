from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_doctor


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_patient


class IsPharmacist(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_pharmacist


class IsLabTech(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_lab_tech


class IsAdminOrDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_doctor
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level: only the owner or an admin can access."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_admin or obj == request.user