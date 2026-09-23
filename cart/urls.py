from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.cart_detail,
        name="cart"
    ),

    # PRODUITS
    path(
        "add/product/<int:product_id>/",
        views.add_product_to_cart,
        name="add_product_to_cart"
    ),

    # FORMATIONS
    path(
        "add/course/<int:course_id>/",
        views.add_course_to_cart,
        name="add_course_to_cart"
    ),

    # COMMANDER
    path(
        "create-order/",
        views.create_order,
        name="create_order"
    ),

    # QUANTITÉ
    path(
        "increase/<int:item_id>/",
        views.increase_quantity,
        name="increase_quantity"
    ),

    path(
        "decrease/<int:item_id>/",
        views.decrease_quantity,
        name="decrease_quantity"
    ),

    # SUPPRIMER UN ARTICLE
    path(
        "remove/<int:item_id>/",
        views.remove_from_cart,
        name="remove_from_cart"
    ),

    # VIDER LE PANIER
    path(
        "clear/",
        views.clear_cart,
        name="clear_cart"
    ),
]