# Coracle URL configuration
import importlib.util

from django.apps import apps
from django.urls import include, path, re_path

from pretix.multidomain.plugin_handler import plugin_event_urls
from pretix.presale.urls import (
    event_patterns, locale_patterns, organizer_patterns,
)
from pretix.urls import common_patterns

from coracle_pages import views

# Build plugin patterns (same as pretix but we control the assembly)
raw_plugin_patterns = []
for app in apps.get_app_configs():
    if hasattr(app, 'PretixPluginMeta'):
        if importlib.util.find_spec(app.name + '.urls'):
            urlmod = importlib.import_module(app.name + '.urls')
            single_plugin_patterns = []
            if hasattr(urlmod, 'urlpatterns'):
                single_plugin_patterns += urlmod.urlpatterns
            if hasattr(urlmod, 'event_patterns'):
                patterns = plugin_event_urls(urlmod.event_patterns, plugin=app.name)
                single_plugin_patterns.append(re_path(r'^(?P<organizer>[^/]+)/(?P<event>[^/]+)/',
                                                      include(patterns)))
            if hasattr(urlmod, 'organizer_patterns'):
                patterns = plugin_event_urls(urlmod.organizer_patterns, plugin=app.name)
                single_plugin_patterns.append(re_path(r'^(?P<organizer>[^/]+)/',
                                                      include(patterns)))
            raw_plugin_patterns.append(
                re_path(r'', include((single_plugin_patterns, app.label)))
            )

plugin_patterns = [
    re_path(r'', include((raw_plugin_patterns, 'plugins')))
]

# Presale patterns WITHOUT the index view (we'll provide our own)
presale_patterns_main = [
    re_path(r'', include((locale_patterns + [
        re_path(r'^(?P<organizer>[^/]+)/', include(organizer_patterns)),
        re_path(r'^(?P<organizer>[^/]+)/(?P<event>[^/]+)/', include(event_patterns)),
        # Note: No index view here - coracle provides the home page
    ], 'presale')))
]

# Coracle custom pages
coracle_patterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('survival-guide/', views.survival_guide, name='survival_guide'),
    path('10-principles/', views.principles, name='principles'),
    path('ticket-info/', views.ticket_info, name='ticket_info'),
]

# Final URL assembly: common (control panel, api, etc) + plugins + coracle + presale
# Coracle patterns come before presale since presale has a catch-all pattern
urlpatterns = common_patterns + plugin_patterns + coracle_patterns + presale_patterns_main

handler404 = 'pretix.base.views.errors.page_not_found'
handler500 = 'pretix.base.views.errors.server_error'
