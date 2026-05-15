"""
OGTRMS - Views
Online Gaming Tournament Registration & Management System
MCA Final Year Major Project
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .utils import admin_pin_required, load_admin_pin, save_admin_pin
import json
import io
import os
from datetime import timedelta

from .models import (
    UserProfile, Game, Tournament, Registration,
    TournamentResult, Notification, ContactMessage, Announcement
)
from .forms import (
    SignupForm, LoginForm, OTPVerificationForm, ForgotPasswordForm,
    ChangePasswordForm, UserProfileForm, RegistrationForm,
    TournamentForm, GameForm, ContactForm
)


# ─── Helper ───
def is_admin(user):
    return user.is_authenticated and user.is_staff

def get_user_notifications(user):
    if user.is_authenticated:
        return Notification.objects.filter(
            Q(user=user) | Q(is_global=True), is_read=False
        ).count()
    return 0


# ═══════════════════════════════════════════════════════════
# PUBLIC VIEWS
# ═══════════════════════════════════════════════════════════

def home(request):
    featured = Tournament.objects.filter(is_featured=True, status__in=['UPCOMING', 'LIVE'])[:6]
    upcoming = Tournament.objects.filter(status='UPCOMING').order_by('start_date')[:8]
    live = Tournament.objects.filter(status='LIVE')[:4]
    games = Game.objects.filter(is_active=True)
    announcements = Announcement.objects.filter(is_active=True)[:3]
    total_tournaments = Tournament.objects.count()
    total_users = User.objects.count()
    total_prize = Tournament.objects.aggregate(total=Sum('prize_pool'))['total'] or 0

    context = {
        'featured': featured,
        'upcoming': upcoming,
        'live': live,
        'games': games,
        'announcements': announcements,
        'total_tournaments': total_tournaments,
        'total_users': total_users,
        'total_prize': total_prize,
    }
    return render(request, 'core/home.html', context)


def tournaments_list(request):
    q = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    fee_filter = request.GET.get('fee', '')
    game_filter = request.GET.get('game', '')

    tournaments = Tournament.objects.select_related('game').all()

    if q:
        tournaments = tournaments.filter(
            Q(title__icontains=q) | Q(game__display_name__icontains=q)
        )
    if status_filter:
        tournaments = tournaments.filter(status=status_filter)
    if fee_filter == 'free':
        tournaments = tournaments.filter(entry_fee=0)
    elif fee_filter == 'paid':
        tournaments = tournaments.filter(entry_fee__gt=0)
    if game_filter:
        tournaments = tournaments.filter(game__name=game_filter)

    paginator = Paginator(tournaments, 9)
    page = request.GET.get('page', 1)
    tournaments_page = paginator.get_page(page)
    games = Game.objects.filter(is_active=True)

    context = {
        'tournaments': tournaments_page,
        'games': games,
        'q': q,
        'status_filter': status_filter,
        'fee_filter': fee_filter,
        'game_filter': game_filter,
    }
    return render(request, 'core/tournaments/list.html', context)


def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_registered = False
    user_registration = None
    if request.user.is_authenticated:
        user_registration = Registration.objects.filter(
            user=request.user, tournament=tournament
        ).first()
        user_registered = user_registration is not None

    results = TournamentResult.objects.filter(tournament=tournament).select_related('registration')[:10]

    context = {
        'tournament': tournament,
        'user_registered': user_registered,
        'user_registration': user_registration,
        'results': results,
    }
    return render(request, 'core/tournaments/detail.html', context)


def leaderboard(request):
    # Global leaderboard by points
    top_users = UserProfile.objects.select_related('user').order_by('-total_points')[:50]
    # Recent winners
    recent_winners = TournamentResult.objects.filter(
        is_winner=True
    ).select_related('registration__user', 'tournament').order_by('-created_at')[:20]

    # Tournament-specific leaderboard
    tournament_id = request.GET.get('tournament')
    tournament_results = None
    selected_tournament = None
    if tournament_id:
        selected_tournament = get_object_or_404(Tournament, pk=tournament_id, status='COMPLETED')
        tournament_results = TournamentResult.objects.filter(
            tournament=selected_tournament
        ).select_related('registration').order_by('rank')

    completed_tournaments = Tournament.objects.filter(status='COMPLETED')

    context = {
        'top_users': top_users,
        'recent_winners': recent_winners,
        'tournament_results': tournament_results,
        'selected_tournament': selected_tournament,
        'completed_tournaments': completed_tournaments,
    }
    return render(request, 'core/leaderboard.html', context)


def contact(request):
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent! We'll get back to you soon.")
            return redirect('contact')
    return render(request, 'core/contact.html', {'form': form})


def about(request):
    return render(request, 'core/about.html')


# ═══════════════════════════════════════════════════════════
# AUTHENTICATION VIEWS
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# AUTHENTICATION VIEWS (ERROR FREE)
# Replace old auth views in views.py
# ═══════════════════════════════════════════════════════════

from django.db import transaction

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = SignupForm()

    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():

                    user = form.save()
                    user.is_active = False
                    user.save()

                    profile, created = UserProfile.objects.get_or_create(
                        user=user
                    )

                    profile.mobile = form.cleaned_data['mobile']
                    profile.save()

                    otp = profile.generate_otp()

                    send_mail(
                        'OGTRMS OTP Verification',
                        f'Your OTP is: {otp}',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True
                    )

                    request.session['verify_user_id'] = user.id

                    messages.success(
                        request,
                        "OTP sent to your email."
                    )

                    return redirect('verify_email')

            except Exception as e:
                print(e)
                messages.error(
                    request,
                    "Account creation failed."
                )

        else:
            print(form.errors)

    return render(
        request,
        'core/auth/signup.html',
        {'form': form}
    )

def verify_email(request):
    user_id = request.session.get('verify_user_id')

    if not user_id:
        return redirect('signup')

    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)

        if form.is_valid():
            otp = form.cleaned_data['otp']

            if user.profile.is_otp_valid(otp):

                user.is_active = True   # 🔥 MOST IMPORTANT
                user.save()

                profile = user.profile
                profile.is_verified = True
                profile.otp = ''
                profile.save()

                login(request, user)

                del request.session['verify_user_id']

                messages.success(request, "Account verified successfully")
                return redirect('home')

    else:
        form = OTPVerificationForm()

    return render(request, 'core/auth/verify_email.html', {'form': form})


def resend_otp(request):
    user_id = request.session.get('verify_user_id')

    if not user_id:
        return redirect('signup')

    user = get_object_or_404(User, pk=user_id)

    try:
        profile = user.profile
        otp = profile.generate_otp()

        send_mail(
            subject='OGTRMS New OTP',
            message=f'Your new OTP is: {otp}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )

        messages.success(
            request,
            "New OTP sent successfully."
        )

    except Exception as e:
        print("OTP Error:", e)
        messages.error(
            request,
            "Unable to resend OTP."
        )

    return redirect('verify_email')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful")
            return redirect('home')

        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'core/auth/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)

    messages.success(
        request,
        "Logged out successfully."
    )

    return redirect('home')


def forgot_password(request):
    form = ForgotPasswordForm()

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                user = User.objects.get(email=email)

                profile, created = UserProfile.objects.get_or_create(
                    user=user
                )

                otp = profile.generate_otp()

                send_mail(
                    subject='OGTRMS Password Reset OTP',
                    message=f'Your OTP is: {otp}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True
                )

                request.session['reset_user_id'] = user.id

                messages.success(
                    request,
                    "OTP sent to email."
                )

                return redirect('reset_password')

            except User.DoesNotExist:
                messages.error(
                    request,
                    "Email not found."
                )

    return render(
        request,
        'core/auth/forgot_password.html',
        {'form': form}
    )


def reset_password(request):
    user_id = request.session.get('reset_user_id')

    if not user_id:
        return redirect('forgot_password')

    user = get_object_or_404(User, pk=user_id)

    otp_form = OTPVerificationForm()
    pwd_form = ChangePasswordForm()

    otp_verified = request.session.get(
        'otp_verified',
        False
    )

    if request.method == 'POST':

        if 'verify_otp' in request.POST:
            otp_form = OTPVerificationForm(request.POST)

            if otp_form.is_valid():
                otp = otp_form.cleaned_data['otp']

                if user.profile.is_otp_valid(otp):
                    request.session['otp_verified'] = True
                    otp_verified = True

                    messages.success(
                        request,
                        "OTP verified."
                    )

                else:
                    messages.error(
                        request,
                        "Wrong OTP."
                    )

        elif 'change_password' in request.POST:

            if otp_verified:
                pwd_form = ChangePasswordForm(
                    request.POST
                )

                if pwd_form.is_valid():
                    user.set_password(
                        pwd_form.cleaned_data[
                            'new_password'
                        ]
                    )

                    user.save()

                    del request.session[
                        'reset_user_id'
                    ]

                    request.session.pop(
                        'otp_verified',
                        None
                    )

                    messages.success(
                        request,
                        "Password changed."
                    )

                    return redirect('login')

    return render(
        request,
        'core/auth/reset_password.html',
        {
            'otp_form': otp_form,
            'pwd_form': pwd_form,
            'otp_verified': otp_verified,
            'email': user.email
        }
    )

# ═══════════════════════════════════════════════════════════
# USER DASHBOARD
# ═══════════════════════════════════════════════════════════



@login_required
def dashboard(request):
    user = request.user

    registrations = Registration.objects.filter(
        user=user
    ).select_related(
        'tournament__game'
    ).order_by('-registered_at')

    upcoming = registrations.filter(
        tournament__status='UPCOMING'
    )[:5]

    my_wins = TournamentResult.objects.filter(
        registration__user=user,
        is_winner=True
    )

    # ✅ FIRST create queryset without slicing
    notifications_qs = Notification.objects.filter(
        Q(user=user) | Q(is_global=True)
    ).order_by('-created_at')

    # ✅ count before slice
    unread_count = notifications_qs.filter(
        is_read=False
    ).count()

    # ✅ now slice
    notifications = notifications_qs[:10]

    context = {
        'registrations': registrations[:5],
        'upcoming': upcoming,
        'my_wins': my_wins,
        'notifications': notifications,
        'unread_count': unread_count,

        'total_registrations': registrations.count(),
        'approved_count': registrations.filter(
            registration_status='APPROVED'
        ).count(),

        'pending_count': registrations.filter(
            registration_status='PENDING'
        ).count(),
    }

    return render(
        request,
        'core/user/dashboard.html',
        context
    )


@login_required
def my_registrations(request):
    registrations = Registration.objects.filter(
        user=request.user
    ).select_related('tournament__game').order_by('-registered_at')
    paginator = Paginator(registrations, 10)
    page = request.GET.get('page', 1)
    context = {'registrations': paginator.get_page(page)}
    return render(request, 'core/user/my_registrations.html', context)


@login_required
def registration_detail_user(request, pk):
    registration = get_object_or_404(Registration, pk=pk, user=request.user)
    return render(request, 'core/user/registration_detail.html', {'registration': registration})


@login_required
def download_receipt(request, pk):
    registration = get_object_or_404(Registration, pk=pk, user=request.user)
    # Generate simple text receipt
    receipt_content = f"""
====================================================
   OGTRMS - TOURNAMENT REGISTRATION RECEIPT
====================================================
Registration No : {registration.registration_number}
Tournament      : {registration.tournament.title}
Game            : {registration.tournament.game.display_name}
Player Name     : {registration.full_name}
Email           : {registration.email}
Mobile          : {registration.mobile}
In-Game UID     : {registration.ingame_uid}
In-Game Name    : {registration.ingame_name}
Team Name       : {registration.team_name or 'N/A'}
Entry Fee       : ₹{registration.tournament.entry_fee}
Payment Status  : {registration.get_payment_status_display()}
Reg. Status     : {registration.get_registration_status_display()}
Registered At   : {registration.registered_at.strftime('%d %b %Y, %I:%M %p')}
====================================================
Thank you for participating! Good Luck!
Visit: http://127.0.0.1:8000
====================================================
"""
    response = HttpResponse(receipt_content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="receipt_{registration.registration_number}.txt"'
    return response


@login_required
def user_profile(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    form = UserProfileForm(instance=profile, initial={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    })
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('user_profile')
    return render(request, 'core/user/profile.html', {'form': form, 'profile': profile})


@login_required
def change_password_user(request):
    form = ChangePasswordForm()
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password changed successfully.")
            return redirect('user_profile')
    return render(request, 'core/user/change_password.html', {'form': form})


@login_required
def mark_notifications_read(request):
    Notification.objects.filter(
        Q(user=request.user) | Q(is_global=True), is_read=False
    ).update(is_read=True)
    return JsonResponse({'status': 'ok'})


# ═══════════════════════════════════════════════════════════
# TOURNAMENT REGISTRATION
# ═══════════════════════════════════════════════════════════

@login_required
def register_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    if not tournament.registration_open:
        messages.error(request, "Registration closed.")
        return redirect('tournament_detail', pk=tournament_id)

    if Registration.objects.filter(
        user=request.user,
        tournament=tournament
    ).exists():
        messages.warning(request, "Already registered.")
        return redirect('tournament_detail', pk=tournament_id)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    initial_data = {
        'full_name': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
        'mobile': profile.mobile,
    }

    if request.method == "POST":
        form = RegistrationForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            reg = form.save(commit=False)
            reg.user = request.user
            reg.tournament = tournament
            reg.save()

            tournament.registered_slots += 1
            tournament.save()

            messages.success(
                request,
                f"Registration Successful! Reg No: {reg.registration_number}"
            )

            return redirect(
                'registration_detail_user',
                pk=reg.pk
            )

        else:
            print("FORM ERRORS:", form.errors)

    else:
        form = RegistrationForm(initial=initial_data)

    return render(
        request,
        'core/tournaments/register.html',
        {
            'form': form,
            'tournament': tournament
        }
    )

# ═══════════════════════════════════════════════════════════
# ADMIN VIEWS
# ═══════════════════════════════════════════════════════════

@user_passes_test(is_admin, login_url='/auth/login/')
def admin_dashboard(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)

    total_users = User.objects.filter(is_staff=False).count()
    total_tournaments = Tournament.objects.count()
    total_registrations = Registration.objects.count()
    total_revenue = Registration.objects.filter(
        payment_status='VERIFIED'
    ).aggregate(total=Sum('tournament__entry_fee'))['total'] or 0

    pending_payments = Registration.objects.filter(payment_status='PENDING', tournament__entry_fee__gt=0).count()
    pending_registrations = Registration.objects.filter(registration_status='PENDING').count()
    live_tournaments = Tournament.objects.filter(status='LIVE').count()
    upcoming_tournaments = Tournament.objects.filter(status='UPCOMING').count()

    # Monthly registration data
    monthly_data = []
    for i in range(6):
        month = today.replace(day=1) - timedelta(days=30*i)
        count = Registration.objects.filter(
            registered_at__year=month.year,
            registered_at__month=month.month
        ).count()
        monthly_data.append({'month': month.strftime('%b %Y'), 'count': count})
    monthly_data.reverse()

    # Game popularity
    game_stats = Tournament.objects.values('game__display_name').annotate(
        total=Count('registrations')
    ).order_by('-total')[:6]

    recent_registrations = Registration.objects.select_related(
        'user', 'tournament__game'
    ).order_by('-registered_at')[:10]

    context = {
        'total_users': total_users,
        'total_tournaments': total_tournaments,
        'total_registrations': total_registrations,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'pending_registrations': pending_registrations,
        'live_tournaments': live_tournaments,
        'upcoming_tournaments': upcoming_tournaments,
        'monthly_data': json.dumps(monthly_data),
        'game_stats': list(game_stats),
        'recent_registrations': recent_registrations,
    }
    return render(request, 'core/admin/dashboard.html', context)


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_tournaments(request):
    tournaments = Tournament.objects.select_related('game').order_by('-created_at')
    paginator = Paginator(tournaments, 10)
    page = request.GET.get('page', 1)
    return render(request, 'core/admin/tournaments.html', {
        'tournaments': paginator.get_page(page)
    })


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_tournament_add(request):
    form = TournamentForm()

    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Tournament added successfully!")
            return redirect('admin_tournaments')

        else:
            # show error in console for debugging
            print(form.errors)
            messages.error(request, "Please fix form errors.")

    return render(request, 'core/admin/tournament_form.html', {
        'form': form,
        'action': 'Add'
    })

@user_passes_test(is_admin, login_url='/auth/login/')
def admin_tournament_edit(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    if request.method == 'POST':
        form = TournamentForm(
            request.POST,
            request.FILES,
            instance=tournament
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Tournament updated successfully.")
            return redirect('admin_tournaments')

        else:
            print(form.errors)

    else:
        form = TournamentForm(instance=tournament)

    return render(request, 'core/admin/tournament_form.html', {
        'form': form,
        'action': 'Edit'
    })

@user_passes_test(is_admin, login_url='/auth/login/')
def admin_tournament_delete(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if request.method == 'POST':
        tournament.delete()
        messages.success(request, "Tournament deleted.")
        return redirect('admin_tournaments')
    return render(request, 'core/admin/confirm_delete.html', {'obj': tournament, 'type': 'Tournament'})


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_registrations(request):
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')
    q = request.GET.get('q', '')

    registrations = Registration.objects.select_related(
        'user', 'tournament__game'
    ).order_by('-registered_at')

    # 🔥 STATUS FILTER
    if status_filter:
        registrations = registrations.filter(
            registration_status=status_filter
        )

    # 🔥 PAYMENT FILTER (THIS WAS THE ISSUE)
    if payment_filter:
        registrations = registrations.filter(
            payment_status=payment_filter
        )

    # 🔥 SEARCH FILTER
    if q:
        registrations = registrations.filter(
            Q(full_name__icontains=q) |
            Q(registration_number__icontains=q) |
            Q(tournament__title__icontains=q)
        )

    paginator = Paginator(registrations, 15)
    page = request.GET.get('page', 1)

    return render(request, 'core/admin/registrations.html', {
        'registrations': paginator.get_page(page),
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'q': q,
    })

@user_passes_test(is_admin, login_url='/auth/login/')
def admin_registration_detail(request, pk):
    registration = get_object_or_404(Registration, pk=pk)
    return render(request, 'core/admin/registration_detail.html', {'registration': registration})


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_approve_registration(request, pk):
    registration = get_object_or_404(Registration, pk=pk)

    registration.registration_status = 'APPROVED'
    registration.payment_status = 'VERIFIED'   # 🔥 ADD THIS

    registration.approved_at = timezone.now()
    registration.save()

    Notification.objects.create(
        user=registration.user,
        title="Registration Approved! ✅",
        message=f"Your registration for {registration.tournament.title} has been APPROVED! Room details will be shared before the match.",
        notification_type='SUCCESS'
    )

    messages.success(request, f"Registration {registration.registration_number} approved.")
    return redirect('admin_registrations')


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_reject_registration(request, pk):
    registration = get_object_or_404(Registration, pk=pk)

    registration.registration_status = 'REJECTED'
    registration.payment_status = 'REJECTED'   # 🔥 ADD THIS

    registration.save()

    Notification.objects.create(
        user=registration.user,
        title="Registration Rejected ❌",
        message=f"Your registration for {registration.tournament.title} has been rejected. Contact support for details.",
        notification_type='DANGER'
    )

    messages.warning(request, f"Registration {registration.registration_number} rejected.")
    return redirect('admin_registrations')

@user_passes_test(is_admin, login_url='/auth/login/')
def admin_verify_payment(request, pk):
    registration = get_object_or_404(Registration, pk=pk)
    registration.payment_status = 'VERIFIED'
    registration.save()
    Notification.objects.create(
        user=registration.user,
        title="Payment Verified! 💰",
        message=f"Your payment for {registration.tournament.title} has been verified successfully.",
        notification_type='SUCCESS'
    )
    messages.success(request, "Payment verified.")
    return redirect('admin_registrations')


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_reject_payment(request, pk):
    registration = get_object_or_404(Registration, pk=pk)
    registration.payment_status = 'REJECTED'
    registration.save()
    messages.warning(request, "Payment rejected.")
    return redirect('admin_registrations')


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_users(request):
    q = request.GET.get('q', '')
    users = User.objects.filter(is_staff=False).select_related('profile')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q))
    paginator = Paginator(users, 15)
    page = request.GET.get('page', 1)
    return render(request, 'core/admin/users.html', {
        'users': paginator.get_page(page), 'q': q
    })


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_games(request):
    games = Game.objects.all()
    return render(request, 'core/admin/games.html', {'games': games})


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_game_add(request):
    form = GameForm()

    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Game Added Successfully")
            return redirect('admin_games')

    return render(request, 'core/admin/game_form.html', {
        'form': form,
        'game': None
    })

@user_passes_test(is_admin, login_url='/auth/login/')
def admin_game_edit(request, pk):
    game = get_object_or_404(Game, pk=pk)

    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES, instance=game)

        if form.is_valid():
            form.save()
            messages.success(request, "Game updated successfully!")
            return redirect('admin_games')

        else:
            print(form.errors)

    else:
        form = GameForm(instance=game)

    return render(request, 'core/admin/game_form.html', {
        'form': form,
        'game': game
    })
    
@user_passes_test(is_admin, login_url='/auth/login/') 
def admin_game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk)
    game.delete()
    messages.success(request, "Game deleted successfully!")
    return redirect('admin_games')


@user_passes_test(is_admin, login_url='/auth/login/')
def admin_announce_winner(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    registrations = Registration.objects.filter(
        tournament=tournament, registration_status='APPROVED'
    )
    if request.method == 'POST':
        # Process winner data
        for reg in registrations:
            rank = request.POST.get(f'rank_{reg.pk}', '')
            kills = request.POST.get(f'kills_{reg.pk}', 0)
            points = request.POST.get(f'points_{reg.pk}', 0)
            if rank:
                result, _ = TournamentResult.objects.get_or_create(
                    tournament=tournament, registration=reg
                )
                result.rank = int(rank)
                result.kills = int(kills)
                result.points = int(points)
                result.is_winner = int(rank) <= 3
                if int(rank) == 1:
                    result.prize_won = tournament.first_prize
                elif int(rank) == 2:
                    result.prize_won = tournament.second_prize
                elif int(rank) == 3:
                    result.prize_won = tournament.third_prize
                result.save()
                # Update user points
                try:
                    reg.user.profile.total_points += int(points)
                    if int(rank) == 1:
                        reg.user.profile.total_wins += 1
                    reg.user.profile.save()
                except Exception:
                    pass
                # Notify
                if result.is_winner:
                    Notification.objects.create(
                        user=reg.user,
                        title=f"🏆 You Won! Rank #{rank}",
                        message=f"Congratulations! You achieved Rank {rank} in {tournament.title}. Prize: ₹{result.prize_won}",
                        notification_type='SUCCESS'
                    )
        tournament.status = 'COMPLETED'
        tournament.save()
        messages.success(request, "Winners announced successfully!")
        return redirect('admin_tournaments')

    return render(request, 'core/admin/announce_winner.html', {
        'tournament': tournament, 'registrations': registrations
    })



@user_passes_test(is_admin, login_url='/auth/login/')
def admin_reports(request):

    from django.db.models import Count, Sum
    from django.utils import timezone

    # ===============================
    # Summary
    # ===============================
    total_registrations = Registration.objects.count()

    approved_registrations = Registration.objects.filter(
        registration_status='APPROVED'
    ).count()

    pending_registrations = Registration.objects.filter(
        registration_status='PENDING'
    ).count()

    total_revenue = Registration.objects.filter(
        payment_status='VERIFIED'
    ).aggregate(
        total=Sum('tournament__entry_fee')
    )['total'] or 0


    # ===============================
    # Game Statistics
    # ===============================
    game_stats = Game.objects.annotate(
        tournament_count=Count(
            'tournaments',
            distinct=True
        ),

        registration_count=Count(
            'tournaments__registrations',
            distinct=True
        ),

        revenue=Sum(
            'tournaments__entry_fee'
        )

    ).order_by('-registration_count')


    # ===============================
    # Monthly Trends
    # ===============================
    monthly_revenue = []

    today = timezone.now().date()

    for i in range(6):

        month = today.month - i
        year = today.year

        while month <= 0:
            month += 12
            year -= 1

        count = Registration.objects.filter(
            registered_at__year=year,
            registered_at__month=month
        ).count()

        month_name = timezone.datetime(
            year, month, 1
        ).strftime('%b %Y')

        monthly_revenue.append({
            'month': month_name,
            'count': count
        })

    monthly_revenue.reverse()

    max_month_count = max(
        [m['count'] for m in monthly_revenue],
        default=1
    )


    # ===============================
    # Context
    # ===============================
    context = {
        'total_registrations': total_registrations,
        'approved_registrations': approved_registrations,
        'pending_registrations': pending_registrations,
        'total_revenue': total_revenue,
        'game_stats': game_stats,
        'monthly_revenue': monthly_revenue,
        'max_month_count': max_month_count,
    }

    return render(
        request,
        'core/admin/reports.html',
        context
    )
@user_passes_test(is_admin, login_url='/auth/login/')
def admin_export_csv(request):
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="registrations_export.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Reg No', 'Full Name', 'Email', 'Mobile', 'Tournament',
        'Game', 'In-Game UID', 'Team Name', 'Entry Fee',
        'Payment Status', 'Reg Status', 'Registered At'
    ])
    for reg in Registration.objects.select_related('tournament__game').all():
        writer.writerow([
            reg.registration_number, reg.full_name, reg.email, reg.mobile,
            reg.tournament.title, reg.tournament.game.display_name,
            reg.ingame_uid, reg.team_name, reg.tournament.entry_fee,
            reg.payment_status, reg.registration_status,
            reg.registered_at.strftime('%Y-%m-%d %H:%M')
        ])
    return response


# ═══════════════════════════════════════════════════════════
# API / AJAX VIEWS
# ═══════════════════════════════════════════════════════════

def api_tournament_slots(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    return JsonResponse({
        'slots_left': tournament.slots_left,
        'total_slots': tournament.total_slots,
        'fill_percentage': tournament.fill_percentage,
        'status': tournament.status,
        'registration_open': tournament.registration_open,
    })


def api_live_tournaments(request):
    live = Tournament.objects.filter(status='LIVE').values(
        'id', 'title', 'registered_slots', 'total_slots'
    )
    return JsonResponse({'tournaments': list(live)})


# ═══════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════

def error_404(request, exception):
    return render(request, 'core/404.html', status=404)

def error_500(request):
    return render(request, 'core/500.html', status=500)



@login_required
@user_passes_test(lambda u: u.is_staff)
@admin_pin_required
def admin_change_password(request):
    """Change admin PIN"""
    if request.method == 'POST':
        current_pin = request.POST.get('current_pin', '').strip()
        new_pin = request.POST.get('new_pin', '').strip()
        confirm_pin = request.POST.get('confirm_pin', '').strip()
        
        # Validation
        import re
        if not re.match(r'^\d{6}$', current_pin):
            messages.error(request, 'Current PIN must be 6 digits.')
        elif not re.match(r'^\d{6}$', new_pin):
            messages.error(request, 'New PIN must be 6 digits.')
        elif new_pin != confirm_pin:
            messages.error(request, 'New PINs do not match.')
        elif current_pin == new_pin:
            messages.error(request, 'New PIN cannot be same as current.')
        else:
            # Verify current PIN
            correct_pin = load_admin_pin() or getattr(settings, 'ADMIN_PIN', '123456')
            if current_pin == correct_pin:
                if save_admin_pin(new_pin):
                    messages.success(request, '✅ Admin PIN updated successfully!')
                    messages.info(request, f'New PIN: <strong>{new_pin}</strong> (Save this!)')
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, 'Failed to save new PIN.')
            else:
                messages.error(request, '❌ Current PIN is incorrect.')
        
        # Reload PIN for form display
        settings.ADMIN_PIN = load_admin_pin() or '123456'
    
    return render(request, 'core/admin/change_password.html')

from django.contrib import messages
from django.conf import settings
from django.shortcuts import render, redirect
from .utils import load_admin_pin

def admin_pin_verify(request):

    if request.method == "POST":
        pin = request.POST.get("admin_pin")

        correct_pin = load_admin_pin() or "123456"

        if pin == correct_pin:
            request.session['admin_pin_verified'] = True
            request.session['admin_pin_timeout'] = (timezone.now() + timedelta(minutes=30)).timestamp()
            return redirect('admin_dashboard')

        messages.error(request, "Wrong PIN")

    return render(request, "core/admin/pin_protect.html")



