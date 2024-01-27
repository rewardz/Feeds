from __future__ import division, print_function, unicode_literals

from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS


class IsOptionsOrAuthenticated(IsAuthenticated):
    """
    Allow OPTIONS from anyone, otherwise require authenticated.
    """

    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True

        return super(IsOptionsOrAuthenticated, self).has_permission(request, view)


class IsStaffOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return user.is_authenticated()
        elif user.is_authenticated() and user.is_employer():
            return True
        elif user.is_authenticated() and user.is_supervisor:
            return True
        elif user.is_authenticated() and user.is_marketing_staff:
            return True
        return False


class IsOptionsOrStaffOrReadOnly(IsStaffOrReadOnly):
    def has_permission(self, request, view):
        if request.method == 'OPTIONS' or request.method == 'options':
            return True

        return super(IsOptionsOrStaffOrReadOnly, self).has_permission(request, view)


class IsOptionsOrEcardEnabled(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'OPTIONS' or request.method == 'options':
            return True

        user = request.user
        if not user.is_authenticated():
            return False

        return user.organization.enable_ecards


class CommentPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        """The obj has to be a CustomUser instance"""
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_employer(obj.created_by.organization):
            return True

        return obj.created_by == request.user

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return False
