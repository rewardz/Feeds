from django.db import models


class RepeatedEvent(models.Model):

    user = models.ForeignKey("profiles.CustomUser", blank=False, on_delete=models.CASCADE)
    organization = models.ForeignKey("profiles.Organization", related_name="repeated_events", editable=False)

    month = models.PositiveSmallIntegerField(blank=True, default=0, db_index=True)
    day = models.PositiveSmallIntegerField(db_index=True)
    year = models.PositiveIntegerField(db_index=True, null=True, blank=True)

    class Meta:
        ordering = ("-month", "-day", "id")
