"""
WSGI config for fan_platform project.  # Configures WSGI for deployment
It exposes the WSGI callable as a module-level variable named ``application``.  # Defines app entry point
For more information on this file, see  # Django docs reference
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os  # Import os for env settings
from django.core.wsgi import get_wsgi_application  # Import WSGI app creator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fan_platform.settings')  # Set settings module

application = get_wsgi_application()  # Create WSGI application