#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from django.core.management import execute_from_command_line
from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ga_core.settings')

    load_dotenv()
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
