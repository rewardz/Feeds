from __future__ import division, print_function, unicode_literals

from django.db import models
from django.utils.translation import ugettext as _

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

    def __unicode__(self):
        return self.nominator.email
