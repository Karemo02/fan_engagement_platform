import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
# Import NLTK for sentiment analysis
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# Import Django utilities for HTTP, rendering, and auth
import json
from django.shortcuts import redirect
# Import JSON and redirect
from .models import UserProfile, Comment, Prediction, Club, ClubStats, Topic, NewsArticle, NewsComment, Fixture, MatchComment, Poll, Vote
# Import app models
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models import Q
# Import Django messages and query utilities
import logging
from datetime import datetime, timedelta
import random
from django.utils import timezone
# Import logging and datetime utilities
from .forms import CommentForm
# Import custom comment form

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Configure debug logging

# Download VADER lexicon (runs once)
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()
# Initialize VADER for sentiment analysis

def get_or_create_user_profile(request):
    # Get or create user profile with default clubs
    if request.user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        if not user_profile.supported_clubs.exists():
            user_profile.supported_clubs.set(Club.objects.all()[:2])
            user_profile.active_club = user_profile.supported_clubs.first()
            user_profile.save()
        elif not user_profile.active_club:
            user_profile.active_club = user_profile.supported_clubs.first()
            user_profile.save()
        return user_profile
    return None

@login_required
def home(request):
    # Render home page with user stats and comments
    user_profile = get_or_create_user_profile(request)
    club_stats = user_profile.club_stats.filter(club=user_profile.active_club).first()
    club_comment_count = user_profile.comment_set.filter(club=user_profile.active_club).count() if user_profile and user_profile.active_club else 0
    club_points = club_stats.points if club_stats else 0
    club_badges = club_stats.badges if club_stats else 'None'
    badges_count = len(club_badges.split(', ') if club_badges != 'None' else []) if club_badges else 0
    topics = Topic.objects.filter(club=user_profile.active_club) if user_profile and user_profile.active_club else []
    if user_profile and user_profile.active_club and not topics.exists():
        topics = [Topic.objects.create(club=user_profile.active_club, name='Match Reviews'),
                  Topic.objects.create(club=user_profile.active_club, name='Player Discussions'),
                  Topic.objects.create(club=user_profile.active_club, name='Fan Predictions')]
    
    # Fetch recent comments
    comments = Comment.objects.filter(club=user_profile.active_club).order_by('-created_at')[:10] if user_profile and user_profile.active_club else []
    
    # Add live fixtures
    live_fixtures = Fixture.objects.filter(is_live=True)

    return render(request, 'engagement/home.html', {
        'user_profile': user_profile,
        'club_comment_count': club_comment_count,
        'club_points': club_points,
        'club_badges': club_badges,
        'badges_count': badges_count,
        'topics': topics,
        'live_fixtures': live_fixtures,
        'comments': comments
    })

@login_required
def leaderboard(request):
    # Render leaderboard with points data
    user_profile = get_or_create_user_profile(request)
    topics = Topic.objects.filter(club=user_profile.active_club) if user_profile and user_profile.active_club else []
    if user_profile and user_profile.active_club and not topics.exists():
        topics = [Topic.objects.create(club=user_profile.active_club, name='Match Reviews'),
                  Topic.objects.create(club=user_profile.active_club, name='Player Discussions'),
                  Topic.objects.create(club=user_profile.active_club, name='Fan Predictions')]
    
    club_points_data = []
    if user_profile and user_profile.active_club:
        comments = user_profile.comment_set.filter(club=user_profile.active_club, sentiment='Positive').order_by('created_at')
        total_points = 0
        for comment in comments:
            total_points += 10
            club_points_data.append({
                'date': comment.created_at.strftime('%Y-%m-%d'),
                'points': total_points,
                'topic_id': comment.topic.id if comment.topic else None
            })
    
    global_points_data = []
    if user_profile:
        comments = user_profile.comment_set.filter(sentiment='Positive').order_by('created_at')
        total_points = 0
        for comment in comments:
            total_points += 10
            global_points_data.append({
                'date': comment.created_at.strftime('%Y-%m-%d'),
                'points': total_points,
                'topic_id': comment.topic.id if comment.topic else None
            })
    
    return render(request, 'engagement/leaderboard.html', {
        'user_profile': user_profile,
        'topics': topics,
        'club_points_data': club_points_data,
        'global_points_data': global_points_data
    })

@login_required
def news(request):
    # Render news articles for active club
    user_profile = get_or_create_user_profile(request)
    news_articles = NewsArticle.objects.filter(club=user_profile.active_club).order_by('-published_date')
    
    return render(request, 'engagement/news.html', {
        'user_profile': user_profile,
        'news_articles': news_articles
    })

@login_required
def news_detail(request, article_id):
    # Render news article details with comments
    user_profile = get_or_create_user_profile(request)
    article = get_object_or_404(NewsArticle, id=article_id, club=user_profile.active_club)
    
    if request.method == 'POST':
        if 'comment' in request.POST:
            text = request.POST.get('comment')
            if text:
                scores = sia.polarity_scores(text)
                sentiment = 'Neutral'
                if scores['compound'] >= 0.05:
                    sentiment = 'Positive'
                elif scores['compound'] <= -0.05:
                    sentiment = 'Negative'
                    messages.warning(request, 'Your comment was detected as negative. Let’s keep it positive!')
                
                NewsComment.objects.create(
                    user_profile=user_profile,
                    news_article=article,
                    text=text,
                    sentiment=sentiment
                )
                return JsonResponse({'status': 'success', 'message': 'Comment added!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Comment cannot be empty.'}, status=400)
        elif 'action' in request.POST and 'comment_id' in request.POST:
            action = request.POST.get('action')
            comment_id = request.POST.get('comment_id')
            comment = get_object_or_404(NewsComment, id=comment_id, news_article=article)
            if action in ['like', 'dislike']:
                current_likes = comment.likes
                current_dislikes = comment.dislikes
                if action == 'like' and comment.dislikes > 0:
                    comment.dislikes -= 1
                elif action == 'dislike' and comment.likes > 0:
                    comment.likes -= 1
                if action == 'like':
                    comment.likes += 1
                elif action == 'dislike':
                    comment.dislikes += 1
                comment.save()
                return JsonResponse({'likes': comment.likes, 'dislikes': comment.dislikes})
            return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

    comments = article.comments.all().order_by('-created_at')
    return render(request, 'engagement/news_detail.html', {
        'user_profile': user_profile,
        'article': article,
        'comments': comments
    })

@login_required
def challenges(request):
    # Render challenges with user progress
    user_profile = get_or_create_user_profile(request)
    club_stats = user_profile.club_stats.filter(club=user_profile.active_club).first() if user_profile else None
    total_comments = user_profile.comment_set.count() if user_profile else 0
    club_comments = user_profile.comment_set.filter(club=user_profile.active_club).count() if user_profile and user_profile.active_club else 0
    positive_comments = user_profile.comment_set.filter(sentiment='Positive').count() if user_profile else 0
    news_comments = user_profile.newscomment_set.count() if user_profile else 0
    # Sum likes and dislikes for engagement
    likes_dislikes = (user_profile.newscomment_set.aggregate(total_likes=Sum('likes'), total_dislikes=Sum('dislikes'))['total_likes'] or 0) + \
                     (user_profile.newscomment_set.aggregate(total_likes=Sum('likes'), total_dislikes=Sum('dislikes'))['total_dislikes'] or 0) if user_profile else 0
    predictions = user_profile.prediction_set.filter(created_at__gte=datetime.now() - timedelta(days=30)).count() if user_profile else 0
    correct_predictions = user_profile.prediction_set.filter(is_correct=True).count() if user_profile else 0

    logger.debug(f"User: {user_profile.user.username}, Predictions: {predictions}, Correct Predictions: {correct_predictions}, Likes/Dislikes: {likes_dislikes}")

    challenges = [
        {
            'name': 'Comment King',
            'description': 'Post 5 comments.',
            'target': 5,
            'progress': total_comments,
            'points': 10,
            'badge': 'Comment King',
            'completed': total_comments >= 5
        },
        {
            'name': 'Positive Vibes',
            'description': 'Post 3 positive comments.',
            'target': 3,
            'progress': positive_comments,
            'points': 15,
            'badge': 'Positive Fan',
            'completed': positive_comments >= 3
        },
        {
            'name': 'Loyal Supporter',
            'description': 'Comment 10 times on your active club’s content.',
            'target': 10,
            'progress': club_comments,
            'points': 15,
            'badge': 'Loyal Supporters',
            'completed': club_comments >= 10
        },
        {
            'name': 'Prophet of the Pitch',
            'description': 'Submit 3 correct predictions.',
            'target': 3,
            'progress': correct_predictions,
            'points': 20,
            'badge': 'Seer',
            'completed': correct_predictions >= 3
        },
        {
            'name': 'Match Day Commentator',
            'description': 'Comment on 3 different match-related news articles.',
            'target': 3,
            'progress': news_comments,
            'points': 10,
            'badge': 'Commentator',
            'completed': news_comments >= 3
        },
        {
            'name': 'Engagement Booster',
            'description': 'Like or dislike 10 comments from other users.',
            'target': 10,
            'progress': likes_dislikes,
            'points': 5,
            'badge': 'Engaged Fan',
            'completed': likes_dislikes >= 10
        }
    ]

    if club_stats:
        for challenge in challenges:
            if challenge['completed'] and challenge['badge'] not in club_stats.badges.split(', ') and club_stats.badges != 'None':
                club_stats.points += challenge['points']
                badges = club_stats.badges.split(', ') if club_stats.badges != 'None' else []
                badges.append(challenge['badge'])
                club_stats.badges = ', '.join(badges) if badges else 'None'
                club_stats.save()
        # Award global points
        points_awarded = user_profile.check_challenge_completion()
        if points_awarded > 0:
            logger.debug(f"Awarded {points_awarded} points to {user_profile.user.username}")

    return render(request, 'engagement/challenges.html', {
        'user_profile': user_profile,
        'challenges': challenges,
        'club_stats': club_stats
    })

@login_required
def challenges_predict(request, fixture_id=None):
    # Handle score predictions
    user_profile = get_or_create_user_profile(request)

    # Fetch specific fixture
    fixture = None
    is_live_match = False
    if fixture_id:
        try:
            fixture = Fixture.objects.get(id=fixture_id)
            is_live_match = fixture.is_live
        except Fixture.DoesNotExist:
            pass

    # Lock predictions for live matches
    if is_live_match:
        return JsonResponse({'status': 'error', 'message': 'Predictions are locked during live matches.'}, status=400)

    # Handle invalid fixture
    if fixture_id and not fixture:
        return JsonResponse({'status': 'error', 'message': 'Fixture not found.'}, status=404)

    # Adjust fixture for active club
    adjusted_fixture = fixture
    if fixture and fixture.club != user_profile.active_club:
        adjusted_fixture = Fixture(
            id=fixture.id,
            club=user_profile.active_club,
            opponent=fixture.opponent,
            date=fixture.date,
            time=fixture.time,
            is_live=fixture.is_live,
            final_result=fixture.final_result
        )

    # Get or create prediction
    existing_prediction, created = Prediction.objects.get_or_create(
        user_profile=user_profile,
        fixture_id=fixture.id if fixture else 0,
        defaults={'text': '', 'club': user_profile.active_club, 'created_at': timezone.now(), 'submission_count': 0}
    )
    submission_count = existing_prediction.submission_count

    if request.method == 'POST':
        logger.debug(f"Request body: {request.body.decode('utf-8')}")
        logger.debug(f"Content-Type: {request.content_type}")
        logger.debug(f"POST data: {dict(request.POST)}")
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                prediction_text = data.get('prediction')
            else:
                prediction_text = request.POST.get('prediction')
            logger.debug(f"Parsed prediction_text: {prediction_text}")
            if prediction_text:
                if submission_count >= 2:
                    return JsonResponse({'status': 'error', 'message': 'Prediction finalized—no further changes allowed.'}, status=400)
                existing_prediction.text = prediction_text
                existing_prediction.created_at = timezone.now()
                existing_prediction.submission_count = submission_count + 1
                existing_prediction.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Prediction updated!' if submission_count > 0 else 'Prediction submitted!',
                    'prediction_text': prediction_text,
                    'created_at': existing_prediction.created_at.isoformat(),
                    'submission_count': existing_prediction.submission_count
                })
            return JsonResponse({'status': 'error', 'message': 'Prediction cannot be empty.'}, status=400)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Parse error: {e}, Body: {request.body.decode('utf-8')}, POST: {dict(request.POST)}")
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

    return render(request, 'engagement/challenges_predict.html', {
        'user_profile': user_profile,
        'fixture': adjusted_fixture,
        'existing_prediction': existing_prediction,
        'submission_count': submission_count
    })

@login_required
def fixtures(request):
    # Render fixtures for active club
    user_profile = get_or_create_user_profile(request)
    # Fetch fixtures involving active club
    fixtures = Fixture.objects.filter(
        Q(club=user_profile.active_club) | Q(opponent=user_profile.active_club.name)
    ).exclude(club=user_profile.active_club, opponent=user_profile.active_club.name)

    adjusted_fixtures = []
    for fixture in fixtures:
        if fixture.club == user_profile.active_club:
            adjusted_fixture = {
                'id': fixture.id,
                'date': fixture.date,
                'opponent': fixture.opponent,
                'time': fixture.time,
                'club': fixture.club,
                'venue': 'Home',
                'is_live': fixture.is_live,
                'final_result': fixture.final_result if fixture.final_result else None
            }
        else:
            adjusted_fixture = {
                'id': fixture.id,
                'date': fixture.date,
                'opponent': fixture.opponent,
                'time': fixture.time,
                'club': user_profile.active_club,
                'venue': 'Away',
                'is_live': fixture.is_live,
                'final_result': fixture.final_result if fixture.final_result else None
            }
        if adjusted_fixture['club'].name == adjusted_fixture['opponent']:
            continue
        adjusted_fixtures.append(adjusted_fixture)

    return render(request, 'engagement/fixtures.html', {
        'user_profile': user_profile,
        'fixtures': adjusted_fixtures
    })

@login_required
def get_leaderboard_data(request):
    # Fetch leaderboard data
    user_profile = get_or_create_user_profile(request)
    data = {}
    
    try:
        data['global'] = list(UserProfile.objects.annotate(
            total_points=Sum('club_stats__points', default=0)
        ).values('user__username', 'total_points').order_by('-total_points')[:10])
        logger.debug(f"Global leaderboard data: {data['global']}")

        if user_profile and user_profile.active_club:
            data['club'] = list(UserProfile.objects.annotate(
                club_points=Sum('club_stats__points', filter=Q(club_stats__club=user_profile.active_club), default=0)
            ).values('user__username', 'club_points').order_by('-club_points')[:10])
        else:
            data['club'] = []
        logger.debug(f"Club-specific leaderboard data: {data['club']}")

        topic_id = request.GET.get('topic_id')
        if user_profile and user_profile.active_club and topic_id:
            try:
                topic = get_object_or_404(Topic, id=topic_id, club=user_profile.active_club)
                data['topic'] = list(UserProfile.objects.annotate(
                    topic_points=Count('comment', filter=Q(comment__club=user_profile.active_club, comment__topic=topic), distinct=True) * 10
                ).values('user__username', 'topic_points').order_by('-topic_points')[:10])
                logger.debug(f"Topic-specific leaderboard data for topic {topic_id}: {data['topic']}")
            except Topic.DoesNotExist:
                data['topic'] = []
        else:
            data['topic'] = []
        logger.debug(f"Final leaderboard data: {data}")

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in get_leaderboard_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def reset_stats(request):
    # Reset user stats
    user_profile = get_or_create_user_profile(request)
    if user_profile:
        Comment.objects.filter(user_profile=user_profile).delete()
        for club in user_profile.supported_clubs.all():
            club_stats, created = ClubStats.objects.get_or_create(user_profile=user_profile, club=club)
            club_stats.points = 0
            club_stats.badges = 'None'
            club_stats.save()
        messages.success(request, 'Stats have been reset successfully.')
    return redirect('engagement:home')

def switch_club(request):
    # Switch active club
    if request.method == 'POST' and request.user.is_authenticated:
        user_profile = get_or_create_user_profile(request)
        logger.debug(f"Request body: {request.body.decode('utf-8')}")
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = {'club_id': request.POST.get('club_id')}
            club_id = data.get('club_id')
            logger.debug(f"Parsed data: {data}, club_id: {club_id}")
            if club_id and Club.objects.filter(id=club_id).exists() and user_profile.supported_clubs.filter(id=club_id).exists():
                user_profile.active_club = Club.objects.get(id=club_id)
                user_profile.save()
                return JsonResponse({'status': 'success', 'club_color': user_profile.active_club.primary_color})
            return JsonResponse({'status': 'error', 'message': 'Invalid club selection'}, status=400)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Parse error: {e}, Body: {request.body.decode('utf-8')}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def analyze_sentiment(request):
    # Analyze comment sentiment
    if request.method == 'POST':
        user_profile = get_or_create_user_profile(request)
        if not user_profile:
            return JsonResponse({'error': 'Please log in to submit comments.'}, status=401)
        data = json.loads(request.body)
        comment = data.get('comment', '')
        topic_id = data.get('topic_id')
        topic = Topic.objects.get(id=topic_id) if topic_id else None
        scores = sia.polarity_scores(comment)
        sentiment = 'Neutral'
        if scores['compound'] >= 0.05:
            sentiment = 'Positive'
        elif scores['compound'] <= -0.05:
            sentiment = 'Negative'
        
        club = user_profile.active_club
        comment_obj = Comment.objects.create(
            user_profile=user_profile,
            text=comment,
            sentiment=sentiment,
            club=club,
            topic=topic
        )
        club_stats, created = ClubStats.objects.get_or_create(user_profile=user_profile, club=club)
        if sentiment == 'Positive':
            club_stats.points += 10
            badges = club_stats.badges.split(', ') if club_stats.badges != 'None' else []
            if 'Positive Fan' not in badges:
                badges.append('Positive Fan')
                club_stats.badges = ', '.join(badges) if badges else 'None'
            comment_count = user_profile.comment_set.filter(club=club).count()
            if comment_count >= 10 and 'Dedicated Fan' not in badges:
                badges.append('Dedicated Fan')
                club_stats.badges = ', '.join(badges) if badges else 'None'
            if comment_count >= 20 and 'Loyal Supporters' not in badges:
                badges.append('Loyal Supporters')
                club_stats.badges = ', '.join(badges) if badges else 'None'
            if topic and user_profile.comment_set.filter(club=club, topic=topic).count() >= 10 and 'Topic Expert' not in badges:
                badges.append('Topic Expert')
                club_stats.badges = ', '.join(badges) if badges else 'None'
            club_stats.save()
        return JsonResponse({'sentiment': sentiment})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def update_stats(request):
    # Update user stats via AJAX
    if request.user.is_authenticated:
        user_profile = get_or_create_user_profile(request)
        if user_profile and user_profile.active_club:
            club_stats = user_profile.club_stats.filter(club=user_profile.active_club).first()
            comment_count = user_profile.comment_set.filter(club=user_profile.active_club).count()
            points = club_stats.points if club_stats else 0
            badges = club_stats.badges.split(', ') if club_stats and club_stats.badges != 'None' else []
            badges_count = len(badges)
        else:
            comment_count = 0
            points = 0
            badges_count = 0
        return JsonResponse({
            'comment_count': comment_count,
            'points': points,
            'badges_count': badges_count
        })
    return JsonResponse({'error': 'Please log in.'}, status=401)

def get_badges(request):
    # Fetch user badges via AJAX
    if request.user.is_authenticated:
        user_profile = get_or_create_user_profile(request)
        if user_profile and user_profile.active_club:
            club_stats = user_profile.club_stats.filter(club=user_profile.active_club).first()
            badges = club_stats.badges if club_stats and club_stats.badges != 'None' else ''
        else:
            badges = ''
        return JsonResponse({'badges': badges})
    return JsonResponse({'error': 'Please log in.'}, status=401)

def get_comments(request):
    # Fetch recent comments via AJAX
    if request.user.is_authenticated:
        user_profile = get_or_create_user_profile(request)
        if user_profile and user_profile.active_club:
            topic_id = request.GET.get('topic_id')
            if topic_id:
                comments = Comment.objects.filter(club=user_profile.active_club, topic_id=topic_id).order_by('-created_at')[:10]
            else:
                comments = Comment.objects.filter(club=user_profile.active_club).order_by('-created_at')[:10]
            comment_data = [{
                'user': comment.user_profile.user.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime("%H:%M %d %b")
            } for comment in comments]
            return JsonResponse({'comments': comment_data})
        return JsonResponse({'comments': []})
    return JsonResponse({'error': 'Please log in.'}, status=401)

def register(request):
    # Handle user registration
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        club_ids = request.POST.getlist('clubs')
        if len(club_ids) > 2:
            messages.error(request, 'You can select a maximum of 2 clubs.')
            return render(request, 'engagement/register.html', {'clubs': Club.objects.all()})
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'engagement/register.html', {'clubs': Club.objects.all()})
        user = User.objects.create_user(username=username, password=password)
        user_profile = UserProfile.objects.create(user=user)
        user_profile.supported_clubs.set(Club.objects.filter(id__in=club_ids))
        user_profile.active_club = user_profile.supported_clubs.first()
        user_profile.save()
        for club in user_profile.supported_clubs.all():
            ClubStats.objects.get_or_create(user_profile=user_profile, club=club)
        login(request, user)
        return redirect('engagement:home')
    return render(request, 'engagement/register.html', {'clubs': Club.objects.all()})

def login_view(request):
    # Handle user login
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('engagement:home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'engagement/login.html')

def logout_view(request):
    # Handle user logout
    logout(request)
    return redirect('engagement:login')

@login_required
def update_predictions(request):
    # Update predictions for admins
    if request.method == 'POST' and request.user.is_superuser:
        fixture_id = request.POST.get('fixture_id')
        result = request.POST.get('result')
        if fixture_id and result:
            FixtureResult.objects.update_or_create(fixture_id=fixture_id, defaults={'result': result})
            predictions = Prediction.objects.filter(fixture_id=fixture_id)
            for pred in predictions:
                pred.is_correct = (pred.text == result)
                pred.save()
            return JsonResponse({'status': 'success', 'message': 'Predictions updated!'})
        return JsonResponse({'status': 'error', 'message': 'Invalid input.'}, status=400)
    return render(request, 'engagement/update_predictions.html')

@login_required
def live_match(request):
    # Render live match with comments
    user_profile = get_or_create_user_profile(request)
    try:
        live_fixture = Fixture.objects.filter(is_live=True).latest('date')
    except Fixture.DoesNotExist:
        live_fixture = None

    if not live_fixture:
        return render(request, 'engagement/live_match.html', {
            'error': 'No live match is currently simulated.'
        })

    existing_prediction = Prediction.objects.filter(
        user_profile=user_profile,
        fixture_id=live_fixture.id
    ).first()

    match_data = {
        'home_team': live_fixture.club.name,
        'away_team': live_fixture.opponent,
        'home_score': getattr(live_fixture, 'home_score', 0),
        'away_score': getattr(live_fixture, 'away_score', 0),
        'minute': getattr(live_fixture, 'minute', 0),
        'final_result': live_fixture.final_result if live_fixture.final_result else None,
        'prediction_correct': False if existing_prediction else None,
    }

    comment_form = CommentForm()

    # Handle AJAX comment submission
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logger.info(f"AJAX POST received: {request.POST}")
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment_text = comment_form.cleaned_data['content'].strip()
            comment = MatchComment.objects.create(
                user_profile=user_profile,
                fixture=live_fixture,
                text=comment_text,
                created_at=timezone.now()
            )
            return JsonResponse({
                'status': 'success',
                'message': '✅ Comment added!',
                'username': comment.user_profile.user.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime("%H:%M %d %b")
            })
        return JsonResponse({'status': 'error', 'message': '❌ Invalid comment'})

    # Handle regular POST
    elif request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment_text = comment_form.cleaned_data['content'].strip()
            MatchComment.objects.create(
                user_profile=user_profile,
                fixture=live_fixture,
                text=comment_text
            )
            messages.success(request, "✅ Comment added!")
        else:
            messages.error(request, "⚠️ Comment cannot be empty.")
        return redirect('engagement:live_match')

    # Update prediction after simulation
    if live_fixture.final_result and existing_prediction and not existing_prediction.is_correct:
        try:
            home_score, away_score = map(int, existing_prediction.text.split('-'))
            predicted_score = f"{home_score}-{away_score}"
            is_correct = predicted_score == live_fixture.final_result
            if is_correct != existing_prediction.is_correct:
                existing_prediction.is_correct = is_correct
                existing_prediction.verified_at = timezone.now()
                existing_prediction.save()
                if is_correct:
                    user_profile.correct_predictions += 1
                    points_awarded = user_profile.check_challenge_completion()
                    if points_awarded > 0:
                        messages.success(request, f"Awarded {points_awarded} points for a correct prediction!")
                user_profile.save()
                match_data['prediction_correct'] = is_correct
        except ValueError:
            pass

    # Stop simulation
    if 'simulation_ended' in request.GET:
        live_fixture.is_live = False
        MatchComment.objects.filter(fixture=live_fixture).delete()
        live_fixture.save()
        messages.info(request, "🏁 Simulation has ended.")
        return redirect('engagement:live_match')

    # Fetch comments
    comments = MatchComment.objects.filter(fixture=live_fixture).order_by('-created_at')

    return render(request, 'engagement/live_match.html', {
        'fixture': live_fixture,
        'match_data': match_data,
        'existing_prediction': existing_prediction,
        'comments': comments,
        'comment_form': comment_form,
        'user_profile': user_profile,
    })

@login_required
def polls(request):
    # Handle polls and voting
    user_profile = get_or_create_user_profile(request)
    if request.method == 'POST':
        poll_id = request.POST.get('poll_id')
        option = request.POST.get('vote')
        try:
            poll = Poll.objects.get(id=poll_id)
            if not Vote.objects.filter(user_profile=user_profile, poll=poll).exists():
                if option == poll.option1:
                    poll.votes_option1 += 1
                elif option == poll.option2:
                    poll.votes_option2 += 1
                elif option == poll.option3 and poll.option3:
                    poll.votes_option3 += 1
                poll.save()
                Vote.objects.create(user_profile=user_profile, poll=poll, option=option)
                messages.success(request, "✅ Your vote has been recorded!")
            else:
                messages.error(request, "❌ You have already voted in this poll.")
        except Poll.DoesNotExist:
            messages.error(request, "❌ Poll not found.")
        return redirect('engagement:polls')

    # Initialize polls if needed
    if not Poll.objects.exists() or Poll.objects.filter(option1="Player A").exists():
        Poll.objects.all().delete()
        Poll.objects.create(
            question="Best Performers in the Last Game",
            option1="Erling Haaland (Manchester City)",
            option2="Mohamed Salah (Liverpool)",
            option3="Bukayo Saka (Arsenal)",
            end_date=timezone.now() + timezone.timedelta(days=7)
        )
        Poll.objects.create(
            question="Favorite Moment from the Last Game",
            option1="The Winning Goal",
            option2="A Spectacular Save",
            option3="A Key Assist",
            end_date=timezone.now() + timezone.timedelta(days=7)
        )

    polls = Poll.objects.all()
    voted_poll_ids = [vote.poll_id for vote in Vote.objects.filter(user_profile=user_profile)]
    return render(request, 'engagement/polls.html', {'polls': polls, 'voted_poll_ids': voted_poll_ids})