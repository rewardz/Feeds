from django.db import models

from .constants import FEEDBACK_STATUS_OPTIONS


class Feedback(models.Model):
    status = models.PositiveSmallIntegerField(
        choices=FEEDBACK_STATUS_OPTIONS(),
        default=FEEDBACK_STATUS_OPTIONS.UNPUBLISHED,
        db_index=True
    )
    user = models.ForeignKey("profiles.CustomUser", on_delete=models.CASCADE)
    resolve_date = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey("profiles.CustomUser", on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="resolved_feedbacks")

    def __unicode__(self):
        return self.user.email
