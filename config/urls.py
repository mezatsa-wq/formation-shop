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

    # Django Admin classique
    path(
        "admin/",
        admin.site.urls
    ),

    # =========================
    # ADMINISTRATION FORMSHOP
    # =========================

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

    # =========================
    # SITE
    # =========================

    path(
        "",
        home,
        name="home"
    ),

    path(
        "accounts/",
        include("accounts.urls")
    ),

    path(
        "courses/",
        include("courses.urls")
    ),

    path(
        "products/",
        include("products.urls")
    ),

    path(
        "orders/",
        include("orders.urls")
    ),

    path(
        "cart/",
        include("cart.urls")
    ),

    path(
        "documents/",
        include("documents.urls")
    ),
]


urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)