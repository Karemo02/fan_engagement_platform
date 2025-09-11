from django.urls import path
from . import views
# Import views from the engagement app

app_name = 'engagement'
# Set namespace for the engagement app

urlpatterns = [ # Map root to various views
    path('', views.home, name='home'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('challenges/', views.challenges, name='challenges'),
    path('fixtures/', views.fixtures, name='fixtures'),
    path('switch-club/', views.switch_club, name='switch_club'),
    path('api/analyze-sentiment/', views.analyze_sentiment, name='analyze_sentiment'),
    path('api/update-stats/', views.update_stats, name='update_stats'),
    path('api/get-badges/', views.get_badges, name='get_badges'),
    path('api/get-leaderboard-data/', views.get_leaderboard_data, name='get_leaderboard_data'),
    path('reset-stats/', views.reset_stats, name='reset_stats'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('news/', views.news, name='news'),
    path('news/<int:article_id>/', views.news_detail, name='news_detail'),
    path('challenges/predict/<int:fixture_id>/', views.challenges_predict, name='challenges_predict'),
    path('update_predictions/', views.update_predictions, name='update_predictions'),
    path('live-match/', views.live_match, name='live_match'),
    path('polls/', views.polls, name='polls'),
    path('api/get-comments/', views.get_comments, name='get_comments'),
]