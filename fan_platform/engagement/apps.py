from django.apps import AppConfig

class EngagementConfig(AppConfig): # Configuration for the engagement app
    default_auto_field = 'django.db.models.BigAutoField'  # Use BigAutoField for primary keys
    name = 'engagement' # App name