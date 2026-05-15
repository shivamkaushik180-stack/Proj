"""
OGTRMS - Core Models
Online Gaming Tournament Registration & Management System
MCA Final Year Major Project
FIXED VERSION (Only Required Fixes Applied)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string


# ─────────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────────
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    total_wins = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def generate_otp(self):
        self.otp = ''.join(random.choices(string.digits, k=6))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp

    # ✅ FIXED
    def is_otp_valid(self, entered_otp):
        if self.otp_created_at and self.otp == entered_otp:
            elapsed = (timezone.now() - self.otp_created_at).seconds
            return elapsed < 300
        return False

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# ─────────────────────────────────────────────
# GAME
# ─────────────────────────────────────────────
GAME_CHOICES = [
    ('BGMI', 'BGMI - Battlegrounds Mobile India'),
    ('FREE_FIRE', 'Free Fire'),
    ('VALORANT', 'Valorant'),
    ('PUBG', 'PUBG PC'),
    ('COD', 'Call of Duty'),
    ('FIFA', 'FIFA'),
]

class Game(models.Model):
    name = models.CharField(max_length=100, choices=GAME_CHOICES)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='games/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    genre = models.CharField(max_length=50, default='Battle Royale')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name = "Game"
        verbose_name_plural = "Games"


# ─────────────────────────────────────────────
# TOURNAMENT
# ─────────────────────────────────────────────
TOURNAMENT_STATUS = [
    ('UPCOMING', 'Upcoming'),
    ('LIVE', 'Live'),
    ('COMPLETED', 'Completed'),
    ('CANCELLED', 'Cancelled'),
]

TOURNAMENT_TYPE = [
    ('SOLO', 'Solo'),
    ('DUO', 'Duo'),
    ('SQUAD', 'Squad'),
    ('TEAM', 'Team'),
]

class Tournament(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='tournaments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    tournament_type = models.CharField(max_length=10, choices=TOURNAMENT_TYPE, default='SQUAD')
    status = models.CharField(max_length=15, choices=TOURNAMENT_STATUS, default='UPCOMING')
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prize_pool = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    first_prize = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    second_prize = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    third_prize = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_slots = models.IntegerField(default=100)
    registered_slots = models.IntegerField(default=0)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()

    room_id = models.CharField(max_length=50, blank=True)
    room_password = models.CharField(max_length=50, blank=True)
    rules = models.TextField(blank=True)
    map_name = models.CharField(max_length=100, blank=True)

    is_featured = models.BooleanField(default=False)
    upi_id = models.CharField(max_length=100, default='ogtrms@upi')
    banner_image = models.ImageField(upload_to='tournament_banners/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.game.display_name}"

    # ✅ FIXED
    def save(self, *args, **kwargs):
        if self.registered_slots < 0:
            self.registered_slots = 0
        if self.registered_slots > self.total_slots:
            self.registered_slots = self.total_slots
        super().save(*args, **kwargs)

    @property
    def slots_left(self):
        return self.total_slots - self.registered_slots

    @property
    def is_free(self):
        return self.entry_fee == 0

    @property
    def registration_open(self):
        return (
            timezone.now() < self.registration_deadline and
            self.slots_left > 0 and
            self.status == 'UPCOMING'
        )

    @property
    def fill_percentage(self):
        if self.total_slots == 0:
            return 0
        return int((self.registered_slots / self.total_slots) * 100)

    class Meta:
        verbose_name = "Tournament"
        verbose_name_plural = "Tournaments"
        ordering = ['-created_at']


# ─────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────
REGISTRATION_STATUS = [
    ('PENDING', 'Pending'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
    ('WAITLISTED', 'Waitlisted'),
]

PAYMENT_STATUS = [
    ('PENDING', 'Pending'),
    ('VERIFIED', 'Verified'),
    ('REJECTED', 'Rejected'),
    ('FREE', 'Free Entry'),
]

class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='registrations')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    ingame_uid = models.CharField(max_length=100)
    ingame_name = models.CharField(max_length=100)
    team_name = models.CharField(max_length=100, blank=True)
    team_members = models.TextField(blank=True)
    payment_screenshot = models.ImageField(upload_to='payments/', blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')
    registration_status = models.CharField(max_length=15, choices=REGISTRATION_STATUS, default='PENDING')
    registration_number = models.CharField(max_length=20, unique=True, blank=True)
    admin_notes = models.TextField(blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} - {self.tournament.title}"

    def save(self, *args, **kwargs):
        if not self.registration_number:
            self.registration_number = self.generate_reg_number()

        if self.tournament.is_free:
            self.payment_status = 'FREE'

        super().save(*args, **kwargs)

    def generate_reg_number(self):
        prefix = 'OGT'
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}{suffix}"

    @property
    def team_members_list(self):
        if self.team_members:
            return [m.strip() for m in self.team_members.split(',')]
        return []

    class Meta:
        verbose_name = "Registration"
        verbose_name_plural = "Registrations"
        ordering = ['-registered_at']
        unique_together = ['user', 'tournament']


# ─────────────────────────────────────────────
# LEADERBOARD / RESULTS
# ─────────────────────────────────────────────
class TournamentResult(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='results')
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='results')
    rank = models.IntegerField()
    kills = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    prize_won = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_winner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rank {self.rank} - {self.registration.full_name}"

    class Meta:
        ordering = ['rank']


# ─────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, default='INFO')
    is_read = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ─────────────────────────────────────────────
# CONTACT
# ─────────────────────────────────────────────
class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=300)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


# ─────────────────────────────────────────────
# ANNOUNCEMENT
# ─────────────────────────────────────────────
class Announcement(models.Model):
    title = models.CharField(max_length=300)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title