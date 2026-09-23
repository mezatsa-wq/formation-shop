"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import home
from app.views import admin_dashboard


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),

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