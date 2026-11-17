import json
import logging

from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone

from .models import LoginUserHistory


logger = logging.getLogger(__name__)


class ExpiredSessionLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        response = self.get_response(request)
        if (
            not session_key
            or request.user.is_authenticated
            or request.session.session_key is not None
        ):
            return response

        try:
            histories = LoginUserHistory.objects.filter(
                logout_time__isnull=True,
                session_history__contains=session_key,
            ).only("pk", "session_history")
            for history in histories:
                try:
                    session_data = json.loads(history.session_history or "")
                except (TypeError, ValueError):
                    continue
                if isinstance(session_data, dict) and session_data.get("session_id") == session_key:
                    LoginUserHistory.objects.filter(
                        pk=history.pk,
                        logout_time__isnull=True,
                    ).update(logout_time=timezone.now())
        except DatabaseError:
            logger.exception("Unable to update expired-session logout history")
            return response

        response.delete_cookie(
            settings.SESSION_COOKIE_NAME,
            path=settings.SESSION_COOKIE_PATH,
            domain=settings.SESSION_COOKIE_DOMAIN,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )
        return response