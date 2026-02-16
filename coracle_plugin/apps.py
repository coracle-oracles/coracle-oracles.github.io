from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoraclePluginConfig(AppConfig):
    name = 'coracle_plugin'
    verbose_name = _("Coracle")

    class PretixPluginMeta:
        name = _("Coracle")
        author = "Coracle Team"
        category = 'FEATURE'
        version = "0.1.0"
        description = _("Coracle Regional Burn website pages")
