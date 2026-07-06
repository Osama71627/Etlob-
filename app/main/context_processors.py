from .models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        return {'unread_notifs': Notification.objects.filter(user=request.user, is_read=False).count()}
    return {'unread_notifs': 0}
