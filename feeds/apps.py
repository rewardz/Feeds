from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class FeedsConfig(AppConfig):
    name = 'feeds'
    verbose_name = _('feeds')

    def ready(self):
        import feeds.signals

