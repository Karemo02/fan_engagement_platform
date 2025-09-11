from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Club(models.Model):
    name = models.CharField(max_length=100)
    # Club name
    primary_color = models.CharField(max_length=7, default='#000000')
    # Hex color for club branding

    def __str__(self):
        return self.name
    # String representation of club

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Link to Django User
    supported_clubs = models.ManyToManyField(Club)
    # Clubs user supports
    active_club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_for')
    # User's active club
    points = models.IntegerField(default=0)
    # User's global points
    badges = models.TextField(default='None')
    # User's badges
    predictions = models.IntegerField(default=0)
    # Total predictions made
    correct_predictions = models.IntegerField(default=0)
    # Correct predictions count

    def check_challenge_completion(self):
        # Check and award challenge points
        from django.db.models import Count, Q
        one_month_ago = timezone.now() - timezone.timedelta(days=30)
        one_week_ago = timezone.now() - timezone.timedelta(days=7)

        # Prophet of the Pitch
        recent_correct = Prediction.objects.filter(
            user_profile=self,
            is_correct=True,
            created_at__gte=one_month_ago
        ).count()
        if recent_correct >= 3 and self.correct_predictions >= 3:
            reward_points = 20
            if self.points < self.points + reward_points:
                self.points += reward_points
                self.save()
                return reward_points

        # Comment King
        total_comments = Comment.objects.filter(
            user_profile=self,
            created_at__gte=one_week_ago
        ).count()
        if total_comments >= 5:
            reward_points = 10
            if self.points < self.points + reward_points:
                self.points += reward_points
                self.save()
                return reward_points

        # Positive Vibes
        positive_comments = Comment.objects.filter(
            user_profile=self,
            sentiment='Positive'
        ).count()
        if positive_comments >= 3:
            reward_points = 15
            if self.points < self.points + reward_points:
                self.points += reward_points
                self.save()
                return reward_points

        # Loyal Supporter
        club_comments = Comment.objects.filter(
            user_profile=self,
            club=self.active_club
        ).count()
        if club_comments >= 10:
            reward_points = 15
            if self.points < self.points + reward_points:
                self.points += reward_points
                self.save()
                return reward_points

        # Match Day Commentator
        news_comments = NewsComment.objects.filter(
            user_profile=self
        ).count()
        if news_comments >= 3:
            reward_points = 10
            if self.points < self.points + reward_points:
                self.points += reward_points
                self.save()
                return reward_points

        # Engagement Booster
        likes_dislikes = NewsComment.objects.filter(
            user_profile=self
        ).aggregate(total=Count('likes') + Count('dislikes'))['total']
        if likes_dislikes >= 10:
            reward_points = 5
            if self.points < self.points + reward_points:
                self.points += reward_points
                self.save()
                return reward_points

        return 0
    # Return 0 if no points awarded

    def __str__(self):
        return f"{self.user.username}'s Profile"
    # String representation of profile

class ClubStats(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='club_stats')
    # Link to UserProfile
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    # Link to Club
    points = models.IntegerField(default=0)
    # Club-specific points
    badges = models.TextField(default='None')
    # Club-specific badges

    class Meta:
        unique_together = ('user_profile', 'club')
    # Ensure unique user-club pairs

class Topic(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='topics')
    # Link to Club
    name = models.CharField(max_length=100)
    # Topic name

    def __str__(self):
        return f"{self.name} ({self.club.name})"
    # String representation of topic

class Comment(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    # Link to UserProfile
    text = models.TextField()
    # Comment text
    sentiment = models.CharField(max_length=10, choices=[('Positive', 'Positive'), ('Neutral', 'Neutral'), ('Negative', 'Negative')])
    # Comment sentiment
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    # Link to Club
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    # Optional link to Topic
    created_at = models.DateTimeField(auto_now_add=True)
    # Comment creation time

class NewsArticle(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='news_articles')
    # Link to Club
    title = models.CharField(max_length=200)
    # Article title
    summary = models.TextField()
    # Article summary
    content = models.TextField(blank=True)
    # Full article content
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)
    # Optional article image
    published_date = models.DateTimeField(auto_now_add=True)
    # Publication date
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # Optional creator

    def __str__(self):
        return f"{self.title} ({self.club.name})"
    # String representation of article

class NewsComment(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    # Link to UserProfile
    news_article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='comments')
    # Link to NewsArticle
    text = models.TextField()
    # Comment text
    sentiment = models.CharField(max_length=10, choices=[('Positive', 'Positive'), ('Neutral', 'Neutral'), ('Negative', 'Negative')])
    # Comment sentiment
    created_at = models.DateTimeField(auto_now_add=True)
    # Comment creation time
    likes = models.IntegerField(default=0)
    # Like count
    dislikes = models.IntegerField(default=0)
    # Dislike count

    def __str__(self):
        return f"Comment by {self.user_profile.user.username} on {self.news_article.title}"
    # String representation of comment

class Fixture(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    # Home club
    opponent = models.CharField(max_length=100)
    # Opponent team name
    date = models.DateTimeField(default=timezone.now)
    # Match date
    time = models.TimeField(default='14:00')
    # Match time
    is_live = models.BooleanField(default=False)
    # Live match status
    final_result = models.CharField(max_length=10, blank=True)
    # Final score (e.g., "2-1")

    def __str__(self):
        return f"{self.club.name} vs {self.opponent} on {self.date}"
    # String representation of fixture

class Prediction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    # Link to UserProfile
    fixture_id = models.IntegerField()
    # Fixture ID
    text = models.CharField(max_length=10)
    # Predicted score (e.g., "2-1")
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    # Predicted club
    is_correct = models.BooleanField(default=False)
    # Prediction correctness
    created_at = models.DateTimeField(default=timezone.now)
    # Creation time
    submission_count = models.IntegerField(default=0)
    # Number of submissions
    verified_at = models.DateTimeField(null=True, blank=True)
    # Verification time

    def check_correctness(self):
        # Check if prediction matches fixture result
        from .models import Fixture
        try:
            fixture = Fixture.objects.get(id=self.fixture_id)
            if fixture.final_result:
                return self.text == fixture.final_result
        except Fixture.DoesNotExist:
            pass
        return False

    def save(self, *args, **kwargs):
        # Update correctness and points on save
        if self.check_correctness():
            self.is_correct = True
            if not self.verified_at:
                self.verified_at = timezone.now()
                self.user_profile.correct_predictions += 1
                self.user_profile.check_challenge_completion()
                self.user_profile.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.text} (Fixture {self.fixture_id})"
    # String representation of prediction

class MatchComment(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    # Link to UserProfile
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='comments')
    # Link to Fixture
    text = models.TextField()
    # Comment text
    sentiment = models.CharField(max_length=10, choices=[('Positive', 'Positive'), ('Neutral', 'Neutral'), ('Negative', 'Negative')], default='Neutral')
    # Comment sentiment
    created_at = models.DateTimeField(auto_now_add=True)
    # Comment creation time

    def __str__(self):
        return f"Comment by {self.user_profile.user.username} on {self.fixture}"
    # String representation of comment

class Poll(models.Model):
    question = models.CharField(max_length=200)
    # Poll question
    option1 = models.CharField(max_length=100)
    # First option
    option2 = models.CharField(max_length=100)
    # Second option
    option3 = models.CharField(max_length=100, blank=True, null=True)
    # Optional third option
    votes_option1 = models.IntegerField(default=0)
    # Votes for option1
    votes_option2 = models.IntegerField(default=0)
    # Votes for option2
    votes_option3 = models.IntegerField(default=0, blank=True, null=True)
    # Votes for option3
    end_date = models.DateTimeField(blank=True, null=True)
    # Poll end date
    created_at = models.DateTimeField(auto_now_add=True)
    # Creation time

    def __str__(self):
        return self.question
    # String representation of poll

class Vote(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    # Link to UserProfile
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    # Link to Poll
    option = models.CharField(max_length=100)
    # Selected option
    voted_at = models.DateTimeField(auto_now_add=True)
    # Vote time

    class Meta:
        unique_together = ('user_profile', 'poll')
    # One vote per user per poll