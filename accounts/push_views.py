import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import PushSubscription

logger = logging.getLogger(__name__)


@require_GET
def push_public_key(request):
    public_key = getattr(
        settings,
        "WEBPUSH_VAPID_PUBLIC_KEY",
        "",
    )

    if not public_key:
        return JsonResponse(
            {"error": "Les notifications push ne sont pas configurées."},
            status=503,
        )

    return JsonResponse({"publicKey": public_key})


@login_required
@require_POST
def push_subscribe(request):
    try:
        data = json.loads(request.body or b"{}")
        endpoint = data.get("endpoint")
        keys = data.get("keys") or {}
        p256dh = keys.get("p256dh")
        auth = keys.get("auth")

        if not all((endpoint, p256dh, auth)):
            return JsonResponse(
                {"error": "Abonnement incomplet."},
                status=400,
            )

        if not endpoint.startswith("https://"):
            return JsonResponse(
                {"error": "Endpoint non sécurisé."},
                status=400,
            )

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": request.user,
                "p256dh": p256dh,
                "auth": auth,
            },
        )

        return JsonResponse({"ok": True})

    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Données JSON invalides."},
            status=400,
        )

    except Exception:
        logger.exception("Impossible d'enregistrer l'abonnement push.")
        return JsonResponse(
            {"error": "Impossible d'enregistrer l'abonnement."},
            status=500,
        )


@login_required
@require_POST
def push_unsubscribe(request):
    try:
        data = json.loads(request.body or b"{}")
        endpoint = data.get("endpoint")

        if not endpoint:
            return JsonResponse(
                {"error": "Endpoint manquant."},
                status=400,
            )

        # Un utilisateur ne peut supprimer que son propre abonnement.
        deleted, _ = PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint,
        ).delete()

        return JsonResponse({"ok": True, "deleted": deleted > 0})

    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Données JSON invalides."},
            status=400,
        )