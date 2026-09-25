from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth.models import User
from products.models import Product
from courses.models import Course, Enrollment

from accounts.models import (
    TokenWallet,
    TokenTransaction,
    SellerEarning,
)

from .models import (
    CoursePayment,
    Order,
    OrderNotification,
)


@login_required
def course_payment(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id,
        is_published=True
    )

    if request.method == "POST":

        method = request.POST.get("method")
        phone_number = request.POST.get("phone_number")

        if not method:
            messages.error(
                request,
                "Veuillez choisir un moyen de paiement."
            )

            return render(
                request,
                "orders/course_payment.html",
                {"course": course}
            )

        if not phone_number:
            messages.error(
                request,
                "Veuillez entrer votre numéro de téléphone."
            )

            return render(
                request,
                "orders/course_payment.html",
                {"course": course}
            )

        CoursePayment.objects.create(
            user=request.user,
            course=course,
            phone_number=phone_number,
            method=method,
            amount=course.price,
            status="pending"
        )

        return render(
            request,
            "orders/course_payment_pending.html",
            {
                "course": course
            }
        )

    return render(
        request,
        "orders/course_payment.html",
        {
            "course": course
        }
    )


@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order.objects.select_related(
            "product",
            "seller",
            "user"
        ),
        id=order_id
    )

    product_seller = None

    if order.product:
        product_seller = order.product.seller

    allowed = (
        request.user.is_staff
        or order.user == request.user
        or order.seller == request.user
        or product_seller == request.user
    )

    if not allowed:
        messages.error(
            request,
            "Vous n'êtes pas autorisé à consulter cette commande."
        )
        return redirect("home")

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order
        }
    )


@login_required
@transaction.atomic
def seller_confirm_delivery(request, order_id):

    if request.method != "POST":
        return redirect(
            "order_detail",
            order_id=order_id
        )

    order = get_object_or_404(
        Order.objects.select_for_update().select_related(
            "product",
            "seller",
            "user"
        ),
        id=order_id
    )

    product_seller = None

    if order.product:
        product_seller = order.product.seller

    is_seller = (
        order.seller == request.user
        or product_seller == request.user
    )

    if not is_seller:
        messages.error(
            request,
            "Cette commande ne vous appartient pas."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if order.status == "cancelled":
        messages.error(
            request,
            "Cette commande a été annulée par le client."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if order.admin_validated:
        messages.error(
            request,
            "Cette commande a déjà été validée par l'administrateur."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if order.seller_confirmed:
        messages.info(
            request,
            "Vous avez déjà confirmé la livraison."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    # Synchronisation des anciennes commandes
    if order.seller != request.user:
        order.seller = request.user

    order.seller_confirmed = True
    order.seller_confirmed_at = timezone.now()
    order.status = "seller_delivered"

    order.save(
        update_fields=[
            "seller",
            "seller_confirmed",
            "seller_confirmed_at",
            "status",
        ]
    )

    product_name = (
        order.product.name
        if order.product
        else "votre produit"
    )

    OrderNotification.objects.create(
        recipient=order.user,
        order=order,
        title="Commande livrée",
        message=(
            f"Le vendeur vous informe que votre commande "
            f"pour « {product_name} » a été livrée.\n\n"
            f"Veuillez confirmer la réception de votre commande."
        )
    )

    for admin in request.user.__class__.objects.filter(
        is_staff=True,
        is_active=True
    ):
        OrderNotification.objects.create(
            recipient=admin,
            order=order,
            title="Livraison confirmée par le vendeur",
            message=(
                f"Le vendeur {request.user.username} a confirmé "
                f"la livraison de la commande #{order.id}."
            )
        )

    messages.success(
        request,
        "La livraison a été confirmée. Le client doit maintenant confirmer la réception."
    )

    return redirect(
        "order_detail",
        order_id=order.id
    )


@login_required
@transaction.atomic
def customer_confirm_receipt(request, order_id):

    if request.method != "POST":
        return redirect(
            "order_detail",
            order_id=order_id
        )

    order = get_object_or_404(
        Order.objects.select_for_update().select_related(
            "product",
            "seller"
        ),
        id=order_id
    )

    if order.user != request.user:
        messages.error(
            request,
            "Cette commande ne vous appartient pas."
        )
        return redirect("home")

    if order.status == "cancelled":
        messages.error(
            request,
            "Cette commande a été annulée."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if order.admin_validated:
        messages.error(
            request,
            "Cette commande a déjà été validée."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if not order.seller_confirmed:
        messages.error(
            request,
            "Le vendeur n'a pas encore confirmé la livraison."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if order.customer_confirmed:
        messages.info(
            request,
            "Vous avez déjà confirmé la réception."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    order.customer_confirmed = True
    order.customer_confirmed_at = timezone.now()
    order.status = "customer_received"

    order.save(
        update_fields=[
            "customer_confirmed",
            "customer_confirmed_at",
            "status",
        ]
    )

    if order.seller:

        OrderNotification.objects.create(
            recipient=order.seller,
            order=order,
            title="Réception confirmée",
            message=(
                f"Le client a confirmé avoir reçu "
                f"la commande #{order.id}."
            )
        )

    for admin in request.user.__class__.objects.filter(
        is_staff=True,
        is_active=True
    ):
        OrderNotification.objects.create(
            recipient=admin,
            order=order,
            title="Réception confirmée par le client",
            message=(
                f"Le client {order.user.username} a confirmé "
                f"la réception de la commande #{order.id}.\n\n"
                f"Les deux confirmations sont maintenant disponibles."
            )
        )

    messages.success(
        request,
        "La réception a été confirmée. La commande peut maintenant être validée par l'administrateur."
    )

    return redirect(
        "order_detail",
        order_id=order.id
    )


@login_required
@transaction.atomic
def cancel_order(request, order_id):

    if request.method != "POST":
        return redirect("order_detail", order_id=order_id)

    order = get_object_or_404(
        Order.objects.select_related(
            "product",
            "seller"
        ),
        id=order_id
    )

    # Seul le client propriétaire peut annuler
    if order.user != request.user:
        messages.error(
            request,
            "Vous n'êtes pas autorisé à annuler cette commande."
        )
        return redirect("order_detail", order_id=order.id)

    # Une commande déjà livrée ou validée ne peut plus être annulée
    if order.status == "cancelled":
        messages.info(
            request,
            "Cette commande est déjà annulée."
        )
        return redirect("order_detail", order_id=order.id)

    if order.seller_confirmed:
        messages.error(
            request,
            "Cette commande ne peut plus être annulée car le vendeur a déjà confirmé la livraison."
        )
        return redirect("order_detail", order_id=order.id)

    if order.customer_confirmed:
        messages.error(
            request,
            "Cette commande ne peut plus être annulée."
        )
        return redirect("order_detail", order_id=order.id)

    if order.admin_validated:
        messages.error(
            request,
            "Cette commande est déjà finalisée."
        )
        return redirect("order_detail", order_id=order.id)

    # Récupération du vendeur si nécessaire
    seller = order.seller

    if not seller and order.product:
        seller = order.product.seller

        if seller:
            order.seller = seller

    # RESTITUTION DU STOCK
    if order.product:

        product = Product.objects.select_for_update().get(
            id=order.product.id
        )

        product.stock += order.quantity

        product.save(
            update_fields=["stock"]
        )

    # Annulation réelle de la commande
    order.status = "cancelled"

    order.save(
        update_fields=[
            "status",
            "seller",
        ]
    )

    # Notification du vendeur
    if seller:

        OrderNotification.objects.create(

            recipient=seller,

            order=order,

            title="Commande annulée",

            message=(
                f"Le client {order.full_name} a annulé "
                f"la commande #{order.id}.\n\n"
                f"Produit : {order.product.name if order.product else 'Produit'}\n"
                f"Quantité : {order.quantity}\n"
                f"Le stock a automatiquement été rétabli."
            )
        )

    # Notification de l'administration
    for admin_user in User.objects.filter(
        is_staff=True,
        is_active=True
    ):

        OrderNotification.objects.create(

            recipient=admin_user,

            order=order,

            title="Commande annulée",

            message=(
                f"La commande #{order.id} a été annulée "
                f"par le client {order.full_name}."
            )
        )

    messages.success(
        request,
        (
            f"La commande #{order.id} a été annulée. "
            f"Le stock du produit a été automatiquement rétabli."
        )
    )

    return redirect("order_detail", order_id=order.id)


@staff_member_required
@transaction.atomic
def admin_validate_order(request, order_id):

    if request.method != "POST":
        return redirect(
            "order_detail",
            order_id=order_id
        )

    order = get_object_or_404(
        Order.objects.select_for_update().select_related(
            "product",
            "seller",
            "user"
        ),
        id=order_id
    )

    if order.status == "cancelled":
        messages.error(
            request,
            "Une commande annulée ne peut pas être validée."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if order.admin_validated:
        messages.info(
            request,
            "Cette commande est déjà validée."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if not order.seller_confirmed:
        messages.error(
            request,
            "Impossible de valider : le vendeur n'a pas confirmé la livraison."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    if not order.customer_confirmed:
        messages.error(
            request,
            "Impossible de valider : le client n'a pas confirmé la réception."
        )
        return redirect(
            "order_detail",
            order_id=order.id
        )

    # Synchronisation des anciennes commandes
    if order.seller is None and order.product:
        order.seller = order.product.seller

    order.admin_validated = True
    order.admin_validated_at = timezone.now()
    order.status = "delivered"
    order.payment_status = "paid"

    if order.product and not order.reward_given:

        wallet, created = TokenWallet.objects.get_or_create(
            user=order.user
        )

        reward = order.product.reward_tokens

        wallet.balance += reward

        wallet.save(
            update_fields=["balance"]
        )

        TokenTransaction.objects.create(
            wallet=wallet,
            amount=reward,
            transaction_type="product",
            description=f"Récompense commande #{order.id}"
        )

        order.reward_given = True

    if order.seller:

        SellerEarning.objects.get_or_create(
            order=order,
            defaults={
                "seller": order.seller,
                "amount": order.total_price,
                "description": (
                    f"Vente du produit "
                    f"« {order.product.name if order.product else 'Produit'} » "
                    f"- commande #{order.id}"
                )
            }
        )

    order.save(
        update_fields=[
            "seller",
            "admin_validated",
            "admin_validated_at",
            "status",
            "payment_status",
            "reward_given",
        ]
    )

    OrderNotification.objects.create(
        recipient=order.user,
        order=order,
        title="Commande validée",
        message=(
            f"La commande #{order.id} a été validée "
            f"par l'administrateur.\n\n"
            f"Votre récompense de "
            f"{order.product.reward_tokens if order.product else 0} "
            f"jetons a été ajoutée à votre portefeuille."
        )
    )

    if order.seller:

        OrderNotification.objects.create(
            recipient=order.seller,
            order=order,
            title="Vente validée",
            message=(
                f"La commande #{order.id} a été validée "
                f"par l'administrateur.\n\n"
                f"Votre revenu de {order.total_price} FCFA "
                f"a été enregistré."
            )
        )

    messages.success(
        request,
        f"La commande #{order.id} a été validée définitivement."
    )

    return redirect(
        "order_detail",
        order_id=order.id
    )


@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).select_related(
        "product",
        "seller"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "orders/my_orders.html",
        {
            "orders": orders
        }
    )


@login_required
def seller_orders(request):

    orders = Order.objects.filter(
        Q(seller=request.user)
        | Q(product__seller=request.user)
    ).select_related(
        "product",
        "user",
        "seller"
    ).distinct().order_by(
        "-created_at"
    )

    return render(
        request,
        "orders/seller_orders.html",
        {
            "orders": orders
        }
    )


@login_required
def order_notifications(request):
    notifications = (
        OrderNotification.objects
        .filter(recipient=request.user)
        .select_related("order", "order__product", "order__user", "order__seller")
        .order_by("-created_at")
    )

    unread_notifications = notifications.filter(is_read=False)

    unread_notifications.update(is_read=True)

    return render(
        request,
        "orders/notifications.html",
        {
            "notifications": notifications,
        }
    )