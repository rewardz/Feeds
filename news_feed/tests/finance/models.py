from __future__ import division, print_function, unicode_literals

from django.db import models
from annoying.fields import JSONField

from .constants import TRANSACTION_STATUSES


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
