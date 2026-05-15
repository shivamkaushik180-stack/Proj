from django.db.models import Q
from .models import Notification, Tournament, Announcement


def site_context(request):
    context = {
        'site_name': 'OGTRMS',
        'site_tagline': 'Online Gaming Tournament Registration & Management System',
    }
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            Q(user=request.user) | Q(is_global=True),
            is_read=False
        ).count()
        context['unread_notifications'] = unread_count
    live_count = Tournament.objects.filter(status='LIVE').count()
    context['live_tournament_count'] = live_count
    return context