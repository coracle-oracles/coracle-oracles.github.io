# Coracle settings - extends pretix settings

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
