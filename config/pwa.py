from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def service_worker(request):
    worker_path = (
        Path(settings.BASE_DIR)
        / "config"
        / "static"
        / "service-worker.js"
    )

    if not worker_path.is_file():
        return HttpResponseNotFound(
            "Le service worker FormaShop est introuvable."
        )

    response = HttpResponse(
        worker_path.read_text(encoding="utf-8"),
        content_type="application/javascript; charset=utf-8",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


@never_cache
def offline_page(request):
    return render(request, "pwa/offline.html")