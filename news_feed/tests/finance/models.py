from __future__ import division, print_function, unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from annoying.fields import JSONField

from .constants import POINT_SOURCE, TRANSACTION_STATUSES


class Transaction(models.Model):
    user = models.ForeignKey("profiles.CustomUser", related_name="transactions",
                             null=True, blank=True, on_delete=models.SET_NULL)
    creator = models.ForeignKey("profiles.CustomUser", null=True, blank=True, related_name="created_transactions",
                                on_delete=models.SET_NULL)
    organization = models.ForeignKey("profiles.Organization", related_name="transactions", null=False, blank=True)
    # reason = models.ForeignKey(PointsTable)
    points = models.DecimalField(blank=True, max_digits=12, decimal_places=2)
    value = models.PositiveIntegerField(default=0, null=False, blank=True)
    context = JSONField(blank=True, null=False, default="{}")

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    is_manually_created = models.BooleanField(default=False)
    message = models.TextField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.SmallIntegerField(choices=TRANSACTION_STATUSES(), blank=False,
                                      default=TRANSACTION_STATUSES.auto_approved)
    bulk_allocation_id = models.IntegerField(null=True, blank=True)
    updated_by = models.ForeignKey("profiles.CustomUser", null=True, blank=True, related_name="updated_transactions",
                                   on_delete=models.SET_NULL)
    department = models.ForeignKey("profiles.Department", null=True, blank=True, related_name="transaction_department",
                                   on_delete=models.SET_NULL)

    class Meta:
        ordering = ("-created", "-pk")

    def __unicode__(self):
        return "{transaction.points} pt".format(transaction=self)


class PointsTable(models.Model):
    organization = models.ForeignKey("profiles.Organization", blank=True, null=True)
    point_source = models.PositiveIntegerField(choices=POINT_SOURCE(), null=False, default=POINT_SOURCE.custom)
    alias = models.CharField(max_length=100, null=False, blank=True, db_index=True,
                             help_text="If you selected 'custom' type, please name it here otherwise leave it blank")
    points = models.DecimalField(blank=True, null=True, max_digits=12, decimal_places=4)
    slug = models.SlugField(unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
