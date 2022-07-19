from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string

from ajax_select import register, LookupChannel

Organization = import_string(settings.ORGANIZATION_MODEL)


@register('CustomUser')
class CustomUserLookup(LookupChannel):
    model = get_user_model()
    min_length = 3

    def get_query(self, q, request):
        return self.model.objects.filter(email__icontains=q)

    def get_result(self, obj):
        """ result is the simple text that is the completion of what the person typed """
        return obj.email


@register('Organization')
class OrganizationLookup(LookupChannel):
    model = Organization
    min_length = 3

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)

    def get_result(self, obj):
        """ result is the simple text that is the completion of what the person typed """
        return obj.name
