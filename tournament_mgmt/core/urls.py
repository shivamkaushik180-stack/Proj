"""
OGTRMS - Core URL Patterns
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── Public ──
    path('', views.home, name='home'),
    path('tournaments/', views.tournaments_list, name='tournaments_list'),
    path('tournaments/<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),

    # ── Auth ──
    path('auth/signup/', views.signup_view, name='signup'),
    path('auth/verify-email/', views.verify_email, name='verify_email'),
    path('auth/resend-otp/', views.resend_otp, name='resend_otp'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/forgot-password/', views.forgot_password, name='forgot_password'),
    path('auth/reset-password/', views.reset_password, name='reset_password'),

    # ── User Dashboard ──
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/registrations/', views.my_registrations, name='my_registrations'),
    path('dashboard/registrations/<int:pk>/', views.registration_detail_user, name='registration_detail_user'),
    path('dashboard/registrations/<int:pk>/receipt/', views.download_receipt, name='download_receipt'),
    path('dashboard/profile/', views.user_profile, name='user_profile'),
    path('dashboard/change-password/', views.change_password_user, name='change_password_user'),
    path('dashboard/notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),

    # ── Tournament Registration ──
    path('tournaments/<int:tournament_id>/register/', views.register_tournament, name='register_tournament'),

    # ── Admin ──
path('admin-panel/pin/', views.admin_pin_verify, name='admin_pin_verify'),
path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),

path('admin-panel/tournaments/', views.admin_tournaments, name='admin_tournaments'),
path('admin-panel/tournaments/add/', views.admin_tournament_add, name='admin_tournament_add'),
path('admin-panel/tournaments/<int:pk>/edit/', views.admin_tournament_edit, name='admin_tournament_edit'),
path('admin-panel/tournaments/<int:pk>/delete/', views.admin_tournament_delete, name='admin_tournament_delete'),
path('admin-panel/tournaments/<int:tournament_pk>/winners/', views.admin_announce_winner, name='admin_announce_winner'),

path('admin-panel/registrations/', views.admin_registrations, name='admin_registrations'),
path('admin-panel/registrations/<int:pk>/', views.admin_registration_detail, name='admin_registration_detail'),
path('admin-panel/registrations/<int:pk>/approve/', views.admin_approve_registration, name='admin_approve_registration'),
path('admin-panel/registrations/<int:pk>/reject/', views.admin_reject_registration, name='admin_reject_registration'),
path('admin-panel/registrations/<int:pk>/verify-payment/', views.admin_verify_payment, name='admin_verify_payment'),
path('admin-panel/registrations/<int:pk>/reject-payment/', views.admin_reject_payment, name='admin_reject_payment'),

path('admin-panel/users/', views.admin_users, name='admin_users'),
path('admin-panel/games/', views.admin_games, name='admin_games'),
path('admin-panel/games/add/', views.admin_game_add, name='admin_game_add'),
path('admin-panel/games/edit/<int:pk>/', views.admin_game_edit, name='admin_game_edit'),
path('admin-panel/games/delete/<int:pk>/', views.admin_game_delete, name='admin_game_delete'),

path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
path('admin-panel/reports/export-csv/', views.admin_export_csv, name='admin_export_csv'),

path('admin-panel/change-password/', views.admin_change_password, name='admin_change_password'),
    # ── API ──
    path('api/tournament/<int:pk>/slots/', views.api_tournament_slots, name='api_tournament_slots'),
    path('api/live-tournaments/', views.api_live_tournaments, name='api_live_tournaments'),
]