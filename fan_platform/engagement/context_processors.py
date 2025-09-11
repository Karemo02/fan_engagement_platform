from .models import Fixture

def live_match_context(request):
    # Add live fixtures to template context
    live_fixtures = Fixture.objects.filter(is_live=True)
    return {'live_fixtures': live_fixtures}
    # Return live fixtures for all templates