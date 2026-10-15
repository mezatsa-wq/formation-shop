import json
import logging

from django.conf import settings

from pywebpush import WebPushException, webpush

from .models import PushSubscription

logger = logging.getLogger(__name__)


def send_push_to_user(user, title, body, url="/"):
    """
    Envoie une notification à tous les appareils abonnés
    de l'utilisateur. Retourne le nombre d'envois réussis.
    """
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
        logger.error("Configuration VAPID incomplète.")
        return 0

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
    })

    sent = 0

    subscriptions = PushSubscription.objects.filter(user=user)

    for subscription in subscriptions.iterator():
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth,
                    },
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={"sub": subject},
                timeout=10,
            )
            sent += 1

        except WebPushException as exc:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)

            logger.warning(
                "Échec Web Push pour l'abonnement %s : %s",
                subscription.pk,
                exc,
            )

            # Ces statuts indiquent généralement un abonnement
            # expiré ou devenu invalide.
            if status_code in (404, 410):
                subscription.delete()

        except Exception:
            logger.exception(
                "Erreur inattendue lors de l'envoi Web Push."
            )

    return sent


def send_push_to_all(title, body, url="/"):
    """
    Envoie une notification à tous les abonnements actifs
    enregistrés dans FormaShop.
    """
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
        logger.error("Configuration VAPID incomplète.")
        return 0

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
    })

    sent = 0

    for subscription in PushSubscription.objects.all().iterator():
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth,
                    },
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={"sub": subject},
                timeout=10,
            )
            sent += 1

        except WebPushException as exc:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)

            logger.warning(
                "Échec Web Push pour l'abonnement %s : %s",
                subscription.pk,
                exc,
            )

            if status_code in (404, 410):
                subscription.delete()

        except Exception:
            logger.exception(
                "Erreur inattendue lors de l'envoi Web Push."
            )

    return sent
def send_public_push(title, body, url="/"):
    """
    Envoie une notification aux abonnements enregistrés.
    Alias de compatibilité pour le code qui appelle
    send_public_push().
    """
    return send_push_to_all(
        title=title,
        body=body,
        url=url,
    )