from django.core.management.base import BaseCommand  # Import BaseCommand
from engagement.models import Fixture, Club  # Import models
import random  # Import random for opponent selection

class Command(BaseCommand):  # Define command class
    help = 'Generates 18 fixtures for specified clubs against all opponents'  # Set help message

    def handle(self, *args, **options):  # Define command logic
        specified_clubs = ['Chelsea', 'Manchester United', 'Manchester City', 'Arsenal', 'Liverpool']  # List clubs
        clubs = Club.objects.filter(name__in=specified_clubs)  # Filter clubs
        all_opponents = ['Crystal Palace', 'West Ham United', 'Fulham', 'Brentford', 'Manchester United',
                         'Brighton & Hove Albion', 'Liverpool', 'Nottingham Forest', 'Sunderland',
                         'Tottenham Hotspur', 'Wolverhampton Wanderers', 'Burnley', 'Arsenal',
                         'Leeds United', 'Bournemouth', 'Everton', 'Newcastle United', 'Aston Villa',
                         'Manchester City', 'Chelsea']  # List opponents
        base_dates = [
            '2025-08-17', '2025-08-23', '2025-08-30', '2025-09-13', '2025-09-20',
            '2025-09-27', '2025-10-04', '2025-10-18', '2025-10-25', '2025-11-01',
            '2025-11-08', '2025-11-22', '2025-11-29', '2025-12-03', '2025-12-06',
            '2025-12-13', '2025-12-20', '2025-12-27'
        ]  # List dates
        times = ['14:00', '15:00', '12:30', '17:00']  # List times

        for club in clubs:  # Loop clubs
            used_opponents = set()  # Track opponents
            date_index = 0  # Initialize date index
            available_opponents = [opp for opp in all_opponents if opp != club.name]  # Filter opponents
            for opponent_name in available_opponents:  # Loop opponents
                if opponent_name in used_opponents:  # Check duplicates
                    continue  # Skip used opponents
                used_opponents.add(opponent_name)  # Add opponent
                date = base_dates[date_index % len(base_dates)]  # Get date
                time = times[date_index % len(times)]  # Get time
                Fixture.objects.get_or_create(  # Create fixture
                    club=club, opponent=opponent_name, date=date, time=time,
                    defaults={'is_live': False, 'final_result': ''}  # Set defaults
                )
                date_index += 1  # Increment index
                if date_index >= 18:  # Limit to 18 fixtures
                    break
        self.stdout.write(self.style.SUCCESS('Successfully generated 18 fixtures for each specified club'))  # Print success