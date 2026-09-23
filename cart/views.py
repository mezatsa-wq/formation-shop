from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .models import Cart, CartItem
from products.models import Product
from courses.models import Course
from orders.models import Order


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
def clear_cart(request):

    cart = get_or_create_cart(request)

    cart.items.all().delete()

    messages.success(
        request,
        "Votre panier a été vidé."
    )

    return redirect("cart")

@login_required
@transaction.atomic
def create_order(request):

    cart = get_or_create_cart(request)

    product_items = cart.items.filter(
        product__isnull=False
    ).select_related("product")

    if not product_items.exists():

        messages.error(
            request,
            "Votre panier ne contient aucun produit à commander."
        )

        return redirect("cart")

    if request.method == "POST":

        full_name = request.POST.get("full_name", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        delivery_address = request.POST.get(
            "delivery_address",
            ""
        ).strip()

        if not full_name or not phone_number or not delivery_address:

            messages.error(
                request,
                "Veuillez remplir toutes les informations de livraison."
            )

            return render(
                request,
                "orders/delivery.html",
                {
                    "items": product_items,
                }
            )

        for item in product_items:

            product = item.product

            if product.stock < item.quantity:

                messages.error(
                    request,
                    f"Stock insuffisant pour le produit : {product.name}"
                )

                return redirect("cart")

        created_orders = []

        for item in product_items:

            product = item.product

            total_price = product.price * item.quantity

            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone_number,
                delivery_address=delivery_address,
                product=product,
                quantity=item.quantity,
                total_price=total_price,
                status="pending",
                payment_status="pending",
                reward_given=False
            )

            product.stock -= item.quantity
            product.save()

            item.delete()

            created_orders.append(order)

        total_amount = sum(
            order.total_price
            for order in created_orders
        )

        return render(
            request,
            "orders/order_success.html",
            {
                "orders": created_orders,
                "total_amount": total_amount,
                "full_name": full_name,
                "phone_number": phone_number,
                "delivery_address": delivery_address,
            }
        )

    return render(
        request,
        "orders/delivery.html",
        {
            "items": product_items,
        }
    )