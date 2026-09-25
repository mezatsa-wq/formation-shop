from django.urls import path

from . import views
from . import admin_views


urlpatterns = [

    path(
        "course/<int:course_id>/payment/",
        views.course_payment,
        name="course_payment"
    ),

    path(
        "order/<int:order_id>/",
        views.order_detail,
        name="order_detail"
    ),

    path(
        "order/<int:order_id>/seller-delivery/",
        views.seller_confirm_delivery,
        name="seller_confirm_delivery"
    ),

    path(
        "order/<int:order_id>/customer-receipt/",
        views.customer_confirm_receipt,
        name="customer_confirm_receipt"
    ),

    path(
        "order/<int:order_id>/cancel/",
        views.cancel_order,
        name="cancel_order"
    ),

    path(
        "order/<int:order_id>/admin-validate/",
        views.admin_validate_order,
        name="admin_validate_order"
    ),

    path(
        "mes-commandes/",
        views.my_orders,
        name="my_orders"
    ),

    path(
        "commandes-vendeur/",
        views.seller_orders,
        name="seller_orders"
    ),

    path(
        "notifications/",
        views.order_notifications,
        name="order_notifications"
    ),

    path(
        "administration/commandes/",
        admin_views.admin_orders,
        name="admin_orders"
    ),
]