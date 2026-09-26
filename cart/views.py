from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Cart, CartItem
from products.models import Product
from courses.models import Course
from orders.models import Order, OrderNotification


def get_or_create_cart(request):
    cart, created = Cart.objects.get_or_create(
        user=request.user
    )
    return cart


@login_required
def cart_detail(request):

    cart = get_or_create_cart(request)

    items = cart.items.select_related(
        "product",
        "course"
    )

    total = 0

    for item in items:

        if item.product:
            total += item.product.price * item.quantity

        elif item.course:
            total += item.course.price * item.quantity

    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,
            "items": items,
            "total": total,
        }
    )


@login_required
def add_product_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        stock__gt=0
    )

    cart = get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        course=None
    )

    if not created:

        if item.quantity < product.stock:
            item.quantity += 1
        else:
            messages.warning(
                request,
                "Vous avez déjà atteint la quantité disponible pour ce produit."
            )
            return redirect("cart")

    item.save()

    return redirect("cart")


@login_required
def add_course_to_cart(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id,
        is_published=True
    )

    cart = get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        course=course,
        product=None
    )

    if not created:
        item.quantity += 1

    item.save()

    return redirect("cart")


@login_required
def increase_quantity(request, item_id):

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    if item.product:

        if item.quantity < item.product.stock:
            item.quantity += 1
            item.save()
        else:
            messages.warning(
                request,
                "La quantité maximale disponible est atteinte."
            )

    else:

        item.quantity += 1
        item.save()

    return redirect("cart")


@login_required
def decrease_quantity(request, item_id):

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    if item.quantity > 1:

        item.quantity -= 1
        item.save()

    else:

        item.delete()

    return redirect("cart")


@login_required
def remove_from_cart(request, item_id):

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    item.delete()

    return redirect("cart")


@login_required
@transaction.atomic
def create_order(request):

    cart = get_or_create_cart(request)

    product_items = list(
        cart.items.filter(
            product__isnull=False
        ).select_related(
            "product",
            "product__seller"
        )
    )

    if not product_items:

        messages.error(
            request,
            "Votre panier ne contient aucun produit à commander."
        )

        return redirect("cart")

    total = sum(
        item.product.price * item.quantity
        for item in product_items
        if item.product
    )

    checkout_context = {
        "cart": cart,
        "items": product_items,
        "total": total,
    }

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        phone_number = request.POST.get(
            "phone_number",
            ""
        ).strip()

        neighborhood = request.POST.get(
            "neighborhood",
            ""
        ).strip()

        delivery_address = request.POST.get(
            "delivery_address",
            ""
        ).strip()

        if not full_name:

            messages.error(
                request,
                "Veuillez entrer votre nom complet."
            )

            return render(
                request,
                "cart/checkout.html",
                checkout_context
            )

        if not phone_number:

            messages.error(
                request,
                "Veuillez entrer votre numéro de téléphone."
            )

            return render(
                request,
                "cart/checkout.html",
                checkout_context
            )

        if not neighborhood:

            messages.error(
                request,
                "Veuillez entrer votre quartier."
            )

            return render(
                request,
                "cart/checkout.html",
                checkout_context
            )

        if not delivery_address:

            messages.error(
                request,
                "Veuillez entrer votre adresse de livraison."
            )

            return render(
                request,
                "cart/checkout.html",
                checkout_context
            )

        created_orders = []
        grand_total = 0

        for item in product_items:

            product = (
                Product.objects
                .select_for_update()
                .select_related("seller")
                .get(id=item.product.id)
            )

            if not product.seller:

                messages.error(
                    request,
                    f"Le produit « {product.name} » n'a pas de vendeur."
                )

                return render(
                    request,
                    "cart/checkout.html",
                    checkout_context
                )

            if product.stock <= 0:

                messages.error(
                    request,
                    f"Le produit « {product.name} » n'est plus disponible."
                )

                return render(
                    request,
                    "cart/checkout.html",
                    checkout_context
                )

            if product.stock < item.quantity:

                messages.error(
                    request,
                    (
                        f"Stock insuffisant pour « {product.name} ». "
                        f"Il reste seulement {product.stock} unité(s)."
                    )
                )

                return render(
                    request,
                    "cart/checkout.html",
                    checkout_context
                )

            total_price = product.price * item.quantity

            deadline = (
                timezone.now()
                + timedelta(hours=24)
            )

            order = Order.objects.create(

                user=request.user,

                seller=product.seller,

                full_name=full_name,

                phone_number=phone_number,

                neighborhood=neighborhood,

                delivery_address=delivery_address,

                delivery_deadline=deadline,

                product=product,

                quantity=item.quantity,

                total_price=total_price,

                status="pending",

                payment_status="pending",

                seller_confirmed=False,

                customer_confirmed=False,

                admin_validated=False,

                reward_given=False
            )

            # Réduction réelle du stock
            product.stock -= item.quantity

            product.save(
                update_fields=["stock"]
            )

            # Notification du vendeur
            OrderNotification.objects.create(

                recipient=product.seller,

                order=order,

                title="Nouvelle commande",

                message=(
                    f"Vous avez reçu une nouvelle commande "
                    f"pour le produit « {product.name} ».\n\n"
                    f"Client : {full_name}\n"
                    f"Téléphone : {phone_number}\n"
                    f"Quartier : {neighborhood}\n"
                    f"Adresse : {delivery_address}\n"
                    f"Quantité : {item.quantity}\n"
                    f"Montant : {total_price} FCFA\n\n"
                    f"Vous devez effectuer la livraison dans les "
                    f"24 heures suivant la commande."
                )
            )

            # Notification du client
            OrderNotification.objects.create(

                recipient=request.user,

                order=order,

                title="Commande créée",

                message=(
                    f"Votre commande pour « {product.name} » "
                    f"a été créée avec succès.\n\n"
                    f"Le vendeur doit effectuer la livraison "
                    f"dans les 24 heures."
                )
            )

            created_orders.append(order)

            grand_total += total_price

            # Retirer l'article du panier
            item.delete()

        # Page de confirmation
        return render(
            request,
            "cart/order_success.html",
            {
                "orders": created_orders,
                "grand_total": grand_total,
                "created_count": len(created_orders),
            }
        )

    return render(
        request,
        "cart/checkout.html",
        checkout_context
    )
@login_required
def clear_cart(request):

    cart = get_or_create_cart(request)

    if request.method == "POST":

        cart.items.all().delete()

        messages.success(
            request,
            "Votre panier a été vidé."
        )

    return redirect("cart")