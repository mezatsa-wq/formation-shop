import json
import logging

from django.conf import settings
from django.utils import timezone

from pywebpush import webpush, WebPushException

from .models import PushSubscription

logger = logging.getLogger(__name__)


def _send_to_subscription(subscription, payload):
    private_key = getattr(
        settings,
        "WEBPUSH_VAPID_PRIVATE_KEY",
        "",
    )
    subject = getattr(
        settings,
        "WEBPUSH_VAPID_SUBJECT",
        "",
    )

    if not private_key or not subject:
        logger.warning(
            "Web Push non configuré : clés VAPID manquantes."
        )
        return False

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=private_key,
            vapid_claims={"sub": subject},
            ttl=86400,
        )
        return True

    except WebPushException as exc:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)

        # Le navigateur a supprimé cet abonnement.
        if status_code in (404, 410):
            subscription.delete()
        else:
            logger.warning(
                "Échec d'envoi Web Push (HTTP %s).",
                status_code,
            )

        return False

    except Exception:
        logger.exception("Erreur lors de l'envoi Web Push.")
        return False


def send_user_push(user, title, body, url="/accounts/"):
    """Envoie une notification uniquement aux abonnements d'un compte."""
    if not user or not getattr(user, "is_active", False):
        return 0

    payload = {
        "title": str(title)[:120],
        "body": str(body)[:240],
        "url": url if url.startswith("/") else "/",
        "tag": f"formashop-user-{user.pk}-{int(timezone.now().timestamp())}",
    }

    subscriptions = PushSubscription.objects.filter(user=user)
    sent = 0

    for subscription in subscriptions.iterator():
        if _send_to_subscription(subscription, payload):
            sent += 1

    return sent


def send_public_push(title, body, url="/"):
    """Diffuse une annonce publique aux comptes abonnés actifs."""
    payload = {
        "title": str(title)[:120],
        "body": str(body)[:240],
        "url": url if url.startswith("/") else "/",
        "tag": f"formashop-public-{timezone.now().strftime('%Y%m%d%H%M')}",
    }

    sent = 0
    subscriptions = PushSubscription.objects.filter(
        user__is_active=True
    ).iterator()

    for subscription in subscriptions:
        if _send_to_subscription(subscription, payload):
            sent += 1

    return sent