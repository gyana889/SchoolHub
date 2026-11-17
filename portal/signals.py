import logging

from django.contrib.auth.signals import user_logged_out
from django.db import DatabaseError
from django.dispatch import receiver
from django.utils import timezone

from .models import LoginUserHistory


logger = logging.getLogger(__name__)


@receiver(user_logged_out)
def record_logout(sender, request, user, **kwargs):
    if request is None or user is None or not user.is_authenticated:
        return
    history_id = request.session.get("login_history_id")
    credential_id = request.session.get("credential_user_id")
    if history_id and credential_id:
        try:
            LoginUserHistory.objects.filter(
                pk=history_id,
                user_id=credential_id,
                logout_time__isnull=True,
            ).update(logout_time=timezone.now())
        except DatabaseError:
            logger.exception("Unable to update logout history")