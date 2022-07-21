import django_filters

from .models import Post


class PostFilter(django_filters.FilterSet):
    post_type = django_filters.BaseInFilter(name="post_type")
    shared_with = django_filters.BaseInFilter(name="shared_with")
    organization = django_filters.BaseInFilter(name="organization")
    user_strength = django_filters.BaseInFilter(name="user_strength", method="user_strength_filter")
    created_on_after = django_filters.DateFilter(name="created_on__gte", method="date_range_filter")
    created_on_before = django_filters.DateFilter(name="created_on__lte", method="date_range_filter")
    nom_status = django_filters.CharFilter(name="nom_status", method="nom_status_filter")

    class Meta:
        model = Post
        fields = ['post_type', 'organization', 'shared_with']

    def user_strength_filter(self, queryset, name, value):
        return queryset.filter(nomination__user_strength__in=value)

    def date_range_filter(self, queryset, name, value):
        return queryset.filter(**{name: value})

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