from django.contrib import admin
from .models import (
    UserProfile, Game, Tournament, Registration,
    TournamentResult, Notification, ContactMessage, Announcement
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'mobile', 'is_verified', 'total_wins', 'total_points']
    list_filter = ['is_verified']
    search_fields = ['user__username', 'user__email']

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'genre', 'is_active']
    list_filter = ['is_active']

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['title', 'game', 'status', 'entry_fee', 'prize_pool', 'total_slots', 'registered_slots', 'start_date']
    list_filter = ['status', 'game', 'is_featured']
    search_fields = ['title']

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'full_name', 'tournament', 'payment_status', 'registration_status', 'registered_at']
    list_filter = ['registration_status', 'payment_status']
    search_fields = ['registration_number', 'full_name', 'email']

@admin.register(TournamentResult)
class TournamentResultAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'registration', 'rank', 'kills', 'points', 'prize_won']
    list_filter = ['tournament', 'is_winner']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'is_global', 'created_at']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_resolved', 'created_at']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']