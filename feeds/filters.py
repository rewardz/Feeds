import django_filters
from django.conf import settings
from django.db.models import Q
from django.utils.module_loading import import_string
from .models import Post
from .utils import get_date_range


NOMINATION_STATUS = import_string(settings.NOMINATION_STATUS)


class PostFilterBase(django_filters.FilterSet):
    post_type = django_filters.BaseInFilter(name="post_type")
    shared_with = django_filters.BaseInFilter(name="shared_with")
    organizations = django_filters.BaseInFilter(name="organizations", method="organizations_filter")
    department = django_filters.BaseInFilter(name="department", method="department_filter")
    created_on_after = django_filters.DateFilter(name="created_on__gte", method="date_range_filter")
    created_on_before = django_filters.DateFilter(name="created_on__lte", method="date_range_filter")
    created_during = django_filters.CharFilter(name="created_during", method="date_period_filter")
    nom_status = django_filters.CharFilter(name="nom_status", method="nom_status_filter")
    category = django_filters.CharFilter(name="category", method="category_filter")
    nom_status_approvals = django_filters.CharFilter(name="nom_status_approvals", method="nom_status_approvals_filter")
    job_family = django_filters.CharFilter(name="job_family", method="job_family_filter")

    class Meta:
        model = Post
        fields = ['post_type', 'organizations', 'shared_with']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user') if 'user' in kwargs.keys() else None
        super(PostFilterBase, self).__init__(*args, **kwargs)

    def organizations_filter(self, queryset, name, value):
        if self.data.get("department") or self.data.get("job_family"):
            return queryset
        try:
            value = [int(value)]
        except Exception:
            if not isinstance(value, list):
                value = value.split(",")
        return queryset.filter(
            Q(organizations__in=value) | Q(created_by__organization__in=value) | Q(user__organization__in=value)
        )

    @staticmethod
    def job_family_filter(queryset, name, value):
        value = value.split(",")
        return queryset.filter(job_families__in=value)

    def date_range_filter(self, queryset, name, value):
        return queryset.filter(**{name: value})

    def date_period_filter(self, queryset, name, value):
        try:
            days = int(value)
        except ValueError:
            return queryset
        start_date, end_date = get_date_range(days)
        return queryset.filter(created_on__gte=start_date, created_on__lte=end_date)

    def department_filter(self, queryset, name, value):
        if isinstance(value, int):
            value = [value]
        return queryset.filter(Q(created_by__departments__in=value) | Q(departments__in=value))

    def nom_status_filter(self, queryset, name, value):
        if value == "pending":
            nom_choices = [0, 1, 2]
        elif value == "approved":
            nom_choices = [3]
        elif value == "rejected":
            nom_choices = [4]
        else:
            return queryset
        return queryset.filter(nomination__nom_status__in=nom_choices)

    def category_filter(self, queryset, name, value):
        if value and value.isdigit():
            return queryset.filter(nomination__category_id=value)
        else:
            return queryset

    def nom_status_approvals_filter(self, queryset, name, value):
        if value == "pending":
            queryset = queryset.filter(
                Q(nomination__assigned_reviewer=self.user) | Q(nomination__alternate_reviewer=self.user))
        elif value == "approved":
            queryset = queryset.filter(
                nomination__histories__reviewer=self.user,
                nomination__histories__status=NOMINATION_STATUS.approved)
        elif value == "rejected":
            queryset = queryset.filter(
                nomination__histories__reviewer=self.user,
                nomination__histories__status=NOMINATION_STATUS.rejected)
        return queryset


class PostFilter(PostFilterBase):
    user_strength = django_filters.BaseInFilter(name="user_strength", method="user_strength_filter")

    @staticmethod
    def user_strength_filter(queryset, name, value):
        return queryset.filter(nomination__user_strength__in=value)
