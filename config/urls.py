"""
URL configuration for config project.
"""
from pathlib import Path

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .pwa import  offline_page
from django.http import FileResponse

from django.http import HttpResponse, Http404
from .views import (
    home,
    about,
    privacy_policy,
    terms_of_use,
)

from app.views import (
    admin_dashboard,
    admin_trainers,
    admin_trainer_detail,
    admin_trainer_approve,
    admin_trainer_reject,
)

def service_worker_file(request):
    file_path = (
        Path(settings.BASE_DIR)
        / "config"
        / "static"
        / "service-worker.js"
    )

    if not file_path.is_file():
        raise Http404("service-worker.js introuvable")

    response = FileResponse(
        file_path.open("rb"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
urlpatterns = [
    # ADMIN DJANGO
    path("admin/", admin.site.urls),

    # ADMINISTRATION FORMASHOP
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/formateurs/", admin_trainers, name="admin_trainers"),
    path(
        "admin-dashboard/formateurs/<int:application_id>/",
        admin_trainer_detail,
        name="admin_trainer_detail",
    ),
    path(
        "admin-dashboard/formateurs/<int:application_id>/accepter/",
        admin_trainer_approve,
        name="admin_trainer_approve",
    ),
    path(
        "admin-dashboard/formateurs/<int:application_id>/refuser/",
        admin_trainer_reject,
        name="admin_trainer_reject",
    ),

    # SITE PRINCIPAL
    path("", home, name="home"),

    # PAGES INFORMATIVES ET JURIDIQUES
    path("a-propos/", about, name="about"),
    path(
        "politique-confidentialite/",
        privacy_policy,
        name="privacy_policy",
    ),
    path(
        "conditions-utilisation/",
        terms_of_use,
        name="terms_of_use",
    ),

    # COMPTES / PROFIL / DASHBOARD
    path("accounts/", include("accounts.urls")),

    # FORMATIONS
    path("courses/", include("courses.urls")),

    # PRODUITS
    path("products/", include("products.urls")),

    # COMMANDES / PAIEMENTS
    path("orders/", include("orders.urls")),

    # PANIER
    path("cart/", include("cart.urls")),

    # DOCUMENTS
    path("documents/", include("documents.urls")),

    path(
        "service-worker.js",
        service_worker_file,
        name="service_worker",
    ),
    path("offline/", offline_page, name="offline"),

]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )