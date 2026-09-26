"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import home

from app.views import (
    admin_dashboard,
    admin_trainers,
    admin_trainer_detail,
    admin_trainer_approve,
    admin_trainer_reject,
)


urlpatterns = [

    # =========================================================
    # ADMIN DJANGO
    # =========================================================

    path(
        "admin/",
        admin.site.urls
    ),


    # =========================================================
    # ADMINISTRATION FORMASHOP
    # =========================================================

    path(
        "admin-dashboard/",
        admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "admin-dashboard/formateurs/",
        admin_trainers,
        name="admin_trainers"
    ),

    path(
        "admin-dashboard/formateurs/<int:application_id>/",
        admin_trainer_detail,
        name="admin_trainer_detail"
    ),

    path(
        "admin-dashboard/formateurs/<int:application_id>/accepter/",
        admin_trainer_approve,
        name="admin_trainer_approve"
    ),

    path(
        "admin-dashboard/formateurs/<int:application_id>/refuser/",
        admin_trainer_reject,
        name="admin_trainer_reject"
    ),


    # =========================================================
    # SITE PRINCIPAL
    # =========================================================

    path(
        "",
        home,
        name="home"
    ),


    # =========================================================
    # COMPTES / PROFIL / DASHBOARD
    # =========================================================

    path(
        "accounts/",
        include("accounts.urls")
    ),


    # =========================================================
    # FORMATIONS
    # =========================================================

    path(
        "courses/",
        include("courses.urls")
    ),


    # =========================================================
    # PRODUITS
    # =========================================================

    path(
        "products/",
        include("products.urls")
    ),


    # =========================================================
    # COMMANDES / PAIEMENTS
    # =========================================================

    path(
        "orders/",
        include("orders.urls")
    ),


    # =========================================================
    # PANIER
    # =========================================================

    path(
        "cart/",
        include("cart.urls")
    ),


    # =========================================================
    # DOCUMENTS
    # =========================================================

    path(
        "documents/",
        include("documents.urls")
    ),
]


# =============================================================
# FICHIERS MEDIA
# =============================================================
#
# Permet à Django de servir les images/photos/fichiers présents
# dans MEDIA_ROOT pendant le développement.
#
# MEDIA_URL  = /media/
# MEDIA_ROOT = BASE_DIR / "media/"
#
# =============================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )