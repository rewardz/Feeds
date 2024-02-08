from __future__ import division, print_function, unicode_literals

from rest_framework.permissions import IsAuthenticated


class IsOptionsOrAuthenticated(IsAuthenticated):
    """
    Allow OPTIONS from anyone, otherwise require authenticated.
    """

    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True

        return super(IsOptionsOrAuthenticated, self).has_permission(request, view)
