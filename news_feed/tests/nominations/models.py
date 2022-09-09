from __future__ import division, print_function, unicode_literals

from django.db import models
from django.utils.translation import ugettext as _
from django.utils import timezone

from .constants import NOMINATION_STATUS, REVIEWER_LEVEL


class NominationCategory(models.Model):
    name = models.CharField(max_length=250, blank=False, verbose_name="Category Name")
    img = models.ImageField(upload_to="nominations/icon")
    slug = models.SlugField(blank=True, unique=True, null=True)
    organization = models.ManyToManyField("profiles.Organization", related_name="nominations_categories_organization")
    department = models.ManyToManyField("profiles.Department", related_name="nominations_categories_department")
    end_date = models.DateField()
    nom_cat_order = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("Nomination category will be displayed based on the order")
    )
    limit = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("Limit of users that can be nominated in the same category")
    )
    reviewer_levels = models.SmallIntegerField(choices=REVIEWER_LEVEL(), default=0)
    badge = models.OneToOneField("profiles.TrophyBadge", blank=True, null=True, on_delete=models.CASCADE)
    auto_action_time = models.PositiveIntegerField(blank=True, null=True, help_text="Auto Action Time in Hours")

    def __unicode__(self):
        return self.name


class Nominations(models.Model):
    category = models.ForeignKey(NominationCategory, related_name="categories")
    nominator = models.ForeignKey("profiles.CustomUser", related_name="current_user")
    assigned_reviewer = models.ManyToManyField("profiles.CustomUser", related_name="reviewer")
    nominated_team_member = models.ForeignKey("profiles.CustomUser", related_name="nominated_user",
                                              verbose_name="Nominated Team Member"
                                              )
    nom_status = models.SmallIntegerField(choices=NOMINATION_STATUS(), default=0)
    comment = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    user_strength = models.ForeignKey("profiles.UserStrength", blank=True, null=True, on_delete=models.CASCADE)
    message_to_reviewer = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.nominator.email

    @property
    def time_left_for_auto_action(self):
        if not self.category.auto_action_time:
            return None
        time_lapsed = timezone.now() - self.created
        time_left = self.category.auto_action_time - (time_lapsed.total_seconds() / 3600)
        if time_left > 0:
            return time_left
        return None
