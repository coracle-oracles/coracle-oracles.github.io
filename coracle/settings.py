# Coracle settings - extends pretix settings

# Monkey-patch for Django 4.0+ compatibility: js_catalog_template was removed
# This must happen before importing pretix which uses it in widget.py
import django.views.i18n
if not hasattr(django.views.i18n, 'js_catalog_template'):
    django.views.i18n.js_catalog_template = r"""
{% autoescape off %}
'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  {% if plural %}
  django.pluralidx = function(n) {
    const v = {{ plural }};
    if (typeof v === 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  {% else %}
  django.pluralidx = function(count) { return (count == 1) ? 0 : 1; };
  {% endif %}

  /* gettext library */

  django.catalog = django.catalog || {};
  {% if catalog_str %}
  const newcatalog = {{ catalog_str }};
  for (const key in newcatalog) {
    django.catalog[key] = newcatalog[key];
  }
  {% endif %}

  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      const value = django.catalog[msgid];
      if (typeof value === 'undefined') {
        return msgid;
      } else {
        return (typeof value === 'string') ? value : value[0];
      }
    };

    django.ngettext = function(singular, plural, count) {
      const value = django.catalog[singular];
      if (typeof value === 'undefined') {
        return (count == 1) ? singular : plural;
      } else {
        return value.constructor === Array ? value[django.pluralidx(count)] : value;
      }
    };

    django.gettext_noop = function(msgid) { return msgid; };

    django.pgettext = function(context, msgid) {
      let value = django.gettext(context + '\x04' + msgid);
      if (value.includes('\x04')) {
        value = msgid;
      }
      return value;
    };

    django.npgettext = function(context, singular, plural, count) {
      let value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
      if (value.includes('\x04')) {
        value = django.ngettext(singular, plural, count);
      }
      return value;
    };

    django.interpolate = function(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
      }
    };


    /* formatting library */

    django.formats = {{ formats_str }};

    django.get_format = function(format_type) {
      const value = django.formats[format_type];
      if (typeof value === 'undefined') {
        return format_type;
      } else {
        return value;
      }
    };

    /* add to global namespace */
    globals.pluralidx = django.pluralidx;
    globals.gettext = django.gettext;
    globals.ngettext = django.ngettext;
    globals.gettext_noop = django.gettext_noop;
    globals.pgettext = django.pgettext;
    globals.npgettext = django.npgettext;
    globals.interpolate = django.interpolate;
    globals.get_format = django.get_format;

    django.jsi18n_initialized = true;
  }
};
{% endautoescape %}
"""

from pretix.settings import *  # noqa: F401, F403

# Add coracle_pages as a regular Django app (not a pretix plugin)
# Note: coracle_pages.apps.CoraclePagesConfig.ready() applies Django 6.0 compatibility patches
INSTALLED_APPS = INSTALLED_APPS + ['coracle_pages']  # noqa: F405

# Use our custom URL config
ROOT_URLCONF = 'coracle.urls'

# Insert our middleware right after MultiDomainMiddleware (position 2)
# to override the urlconf it sets
MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
multi_domain_idx = MIDDLEWARE.index('pretix.multidomain.middlewares.MultiDomainMiddleware')
MIDDLEWARE.insert(multi_domain_idx + 1, 'coracle.middleware.CoracleUrlconfMiddleware')
MIDDLEWARE = tuple(MIDDLEWARE)

# Development settings - disable offline compression
import os
if os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes'):
    DEBUG = True
    COMPRESS_OFFLINE = False
    COMPRESS_ENABLED = False
