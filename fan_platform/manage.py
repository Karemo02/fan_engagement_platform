#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""  # Describe purpose
import os 
import sys 

def main():  # Define main function
    """Run administrative tasks."""  # Describe function
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fan_platform.settings')  # Set settings module
    try:  # Start try block
        from django.core.management import execute_from_command_line  # Import command executor
    except ImportError as exc:  # Catch import error
        raise ImportError(  # Raise custom error
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc  # Include original error
    execute_from_command_line(sys.argv)  # Run commands

if __name__ == '__main__':  # Check if main script
    main()  # Call main