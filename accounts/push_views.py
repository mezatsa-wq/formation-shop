import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import PushSubscription

logger = logging.getLogger(__name__)


def json_error(message, status=400):
    return JsonResponse(
        {"success": False, "error": message},
        status=status,
    )


@require_GET
def push_public_key(request):
    public_key = getattr(
        settings,
        "WEBPUSH_VAPID_PUBLIC_KEY",
        "",
    )

    if not public_key:
        return json_error(
            "La clé publique VAPID n'est pas configurée.",
            status=503,
        )

    return JsonResponse({"publicKey": public_key})


@require_POST
def push_subscribe(request):
    if not request.user.is_authenticated:
        return json_error(
            "Connectez-vous pour activer les notifications.",
            status=401,
        )

    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return json_error("Le JSON envoyé est invalide.")

    endpoint = payload.get("endpoint")
    keys = payload.get("keys") or {}
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (endpoint, p256dh, auth)
    ):
        return json_error(
            "Abonnement incomplet : endpoint ou clés manquants."
        )

    if not endpoint.startswith("https://"):
        return json_error(
            "L'adresse de l'abonnement doit utiliser HTTPS."
        )

    try:
        with transaction.atomic():
            subscription, created = (
                PushSubscription.objects.update_or_create(
                    endpoint=endpoint,
                    defaults={
                        "user": request.user,
                        "p256dh": p256dh,
                        "auth": auth,
                    },
                )
            )
    except IntegrityError:
        logger.exception(
            "Erreur d'intégrité lors de l'enregistrement push."
        )
        return json_error(
            "Impossible d'enregistrer cet abonnement.",
            status=500,
        )
    except Exception:
        logger.exception(
            "Erreur lors de l'enregistrement push."
        )
        return json_error(
            "Erreur serveur pendant l'enregistrement.",
            status=500,
        )

    return JsonResponse({
        "success": True,
        "registered": True,
        "created": created,
        "subscription_id": subscription.pk,
    })


@require_POST
def push_unsubscribe(request):
    if not request.user.is_authenticated:
        return json_error(
            "Connectez-vous pour gérer vos notifications.",
            status=401,
        )

    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return json_error("Le JSON envoyé est invalide.")

    endpoint = payload.get("endpoint")

    if not isinstance(endpoint, str) or not endpoint.strip():
        return json_error("L'adresse de l'abonnement est manquante.")

    deleted_count, _ = PushSubscription.objects.filter(
        user=request.user,
        endpoint=endpoint,
    ).delete()

    return JsonResponse({
        "success": True,
        "unsubscribed": True,
        "deleted": deleted_count > 0,
    })