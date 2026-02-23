from django.apps import AppConfig


class CoraclePagesConfig(AppConfig):
    name = 'coracle_pages'
    verbose_name = "Coracle Pages"

    def ready(self):
        # Apply Django 6.0 compatibility patch for pretix signals
        # Django 6.0 changed _live_receivers to return [[sync], [async]]
        # instead of a flat list of receivers
        self._patch_pretix_signals()

    def _patch_pretix_signals(self):
        from django.conf import settings
        from pretix.base import signals as pretix_signals

        def _sorted_receivers_fixed(self, sender):
            orig_list = self._live_receivers(sender)
            # Django 6.0+ returns [[sync], [async]] - flatten it
            if orig_list and isinstance(orig_list[0], list):
                flat_list = []
                for sublist in orig_list:
                    flat_list.extend(sublist)
                orig_list = flat_list

            sorted_list = sorted(
                orig_list,
                key=lambda receiver: (
                    0 if any(receiver.__module__.startswith(m) for m in settings.CORE_MODULES) else 1,
                    receiver.__module__,
                    receiver.__name__,
                )
            )
            return sorted_list

        # Patch the PluginSignal class
        pretix_signals.PluginSignal._sorted_receivers = _sorted_receivers_fixed
