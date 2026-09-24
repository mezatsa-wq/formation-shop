from django.urls import path

from . import views
from . import admin_views


urlpatterns = [

    # =====================================================
    # PAIEMENT DES FORMATIONS
    # =====================================================

    path(
        "course/<int:course_id>/payment/",
        views.course_payment,
        name="course_payment",
    ),


    # =====================================================
    # COMMANDES
    # =====================================================

    path(
        "order/<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),

    path(
        "order/<int:order_id>/seller-delivery/",
        views.seller_confirm_delivery,
        name="seller_confirm_delivery",
    ),

    path(
        "order/<int:order_id>/customer-receipt/",
        views.customer_confirm_receipt,
        name="customer_confirm_receipt",
    ),

    path(
        "order/<int:order_id>/admin-validate/",
        views.admin_validate_order,
        name="admin_validate_order",
    ),


    # =====================================================
    # ESPACE CLIENT
    # =====================================================

    path(
        "mes-commandes/",
        views.my_orders,
        name="my_orders",
    ),


    # =====================================================
    # ESPACE VENDEUR
    # =====================================================

    path(
        "commandes-vendeur/",
        views.seller_orders,
        name="seller_orders",
    ),


    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    path(
        "notifications/",
        views.order_notifications,
        name="order_notifications",
    ),


    # =====================================================
    # ADMINISTRATION FORMASHOP
    # =====================================================

    path(
        "administration/commandes/",
        admin_views.admin_orders,
        name="admin_orders",
    ),
]