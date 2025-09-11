from engagement.models import UserProfile, Prediction  # Import models
from django.db.models import Max  # Import Max for aggregation

user = UserProfile.objects.get(user__username='logan')  # Get user profile for logan
predictions = Prediction.objects.filter(user_profile=user)  # Get all predictions
for p in predictions:  # Loop predictions
    print(f"Fixture {p.fixture_id}: {p.text} (Created: {p.created_at})")  # Print prediction details
unique_fixtures = predictions.values('fixture_id').annotate(latest_id=Max('id'))  # Get latest prediction per fixture
for fixture in unique_fixtures:  # Loop unique fixtures
    latest = Prediction.objects.get(id=fixture['latest_id'])  # Get latest prediction
    predictions.exclude(id=latest.id).delete()  # Delete older predictions
print("Reset complete. Remaining predictions:")  # Print completion message
for p in Prediction.objects.filter(user_profile=user):  # Loop remaining predictions
    print(f"Fixture {p.fixture_id}: {p.text} (Created: {p.created_at})")  # Print remaining details