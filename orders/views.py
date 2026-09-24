from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

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
        Order,
        id=order_id
    )

    # Seul le client concerné, le vendeur concerné
    # ou un administrateur peut voir cette commande.

    allowed = (
        request.user.is_staff
        or order.user == request.user
        or order.seller == request.user
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
        Order.objects.select_for_update(),
        id=order_id
    )

    # Vérification du vendeur

    if order.seller != request.user:

        messages.error(
            request,
            "Cette commande ne vous appartient pas."
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

    order.seller_confirmed = True
    order.seller_confirmed_at = timezone.now()
    order.status = "seller_delivered"

    order.save(
        update_fields=[
            "seller_confirmed",
            "seller_confirmed_at",
            "status",
        ]
    )

    # Notification du client

    OrderNotification.objects.create(
        recipient=order.user,
        order=order,
        title="Commande livrée",
        message=(
            f"Le vendeur vous informe que votre commande "
            f"pour « {order.product.name} » a été livrée.\n\n"
            f"Veuillez confirmer la réception de votre commande."
        )
    )

    # Notification des administrateurs

    for admin in request.user.__class__.objects.filter(
        is_staff=True,
        is_active=True
    ):

        OrderNotification.objects.create(
            recipient=admin,
            order=order,
            title="Livraison confirmée par le vendeur",
            message=(
                f"Le vendeur {order.seller.username} a confirmé "
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
        Order.objects.select_for_update(),
        id=order_id
    )

    # Vérification du client

    if order.user != request.user:

        messages.error(
            request,
            "Cette commande ne vous appartient pas."
        )

        return redirect(
            "home"
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

    # Notification du vendeur

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

    # Notification des administrateurs

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


@staff_member_required
@transaction.atomic
def admin_validate_order(request, order_id):

    if request.method != "POST":

        return redirect(
            "order_detail",
            order_id=order_id
        )

    order = get_object_or_404(
        Order.objects.select_for_update(),
        id=order_id
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

    # Les deux confirmations sont obligatoires.

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

    # Validation définitive

    order.admin_validated = True
    order.admin_validated_at = timezone.now()

    order.status = "delivered"
    order.payment_status = "paid"

    # Récompense du client
    # Le nombre de jetons vient du produit.

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
            description=(
                f"Récompense commande #{order.id}"
            )
        )

        order.reward_given = True

    # Revenu du vendeur
    # Il n'est créé qu'après validation administrative.

    if order.seller:

        SellerEarning.objects.get_or_create(
            order=order,
            defaults={
                "seller": order.seller,
                "amount": order.total_price,
                "description": (
                    f"Vente du produit "
                    f"« {order.product.name} » "
                    f"- commande #{order.id}"
                )
            }
        )

    order.save(
        update_fields=[
            "admin_validated",
            "admin_validated_at",
            "status",
            "payment_status",
            "reward_given",
        ]
    )

    # Notification client

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

    # Notification vendeur

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
        seller=request.user
    ).select_related(
        "product",
        "user"
    ).order_by(
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

    notifications = OrderNotification.objects.filter(
        recipient=request.user
    ).select_related(
        "order"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "orders/notifications.html",
        {
            "notifications": notifications
        }
    )
