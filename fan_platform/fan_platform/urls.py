from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls), # Map /admin/ to Django admin site
    path('engagement/', include('engagement.urls', namespace='engagement')),  # Base URL for engagement app
    path('accounts/login/', RedirectView.as_view(url='/engagement/login/', permanent=False)),  # Redirect to engagement login
    path('', RedirectView.as_view(url='/engagement/', permanent=False)),  # Redirect root to engagement
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # Serve media files during development