from .models import ChatLog


def recent_chat_logs(request):
    if not request.user.is_authenticated:
        return {'recent_chat_logs': []}

    logs = list(ChatLog.objects.filter(user=request.user)[:8])
    return {'recent_chat_logs': list(reversed(logs))}
