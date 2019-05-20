"""
WSGI config for ctru_django project.
 
It exposes the WSGI callable as a module-level variable named ``application``.
 
For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
 
import os
import sys
 
 
sys.path.insert(0, "/mnt/storage/apps/software/django/1.11.5/lib/python2.7/")
sys.path.insert(0, "/mnt/storage/apps/software/django/1.11.5/lib/python2.7/site-packages/")
 
 
 
# ADD YOUR PROJECT TO THE PYTHONPATH FOR THE PYTHON INSTANCE
path = '/var/www/ga/'
if path not in sys.path:
    sys.path.insert(0, path)
 
# IMPORTANTLY GO TO THE PROJECT DIR
os.chdir(path)
 
 
from django.core.wsgi import get_wsgi_application
os.environ["DJANGO_SETTINGS_MODULE"] = "django_example.settings"
application = get_wsgi_application()
