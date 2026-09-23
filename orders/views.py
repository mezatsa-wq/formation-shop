from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from courses.models import Course, Enrollment

from accounts.models import TokenWallet, TokenTransaction

from .models import CoursePayment, Order


# ============================================================
# PAIEMENT D'UNE FORMATION
# ============================================================




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
@staff_member_required
def mark_order_delivered(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )


    # Marquer la commande comme livrée
    order.status = "delivered"


    # Le paiement à la livraison devient payé
    order.payment_status = "paid"


    # ========================================================
    # RÉCOMPENSE EN JETONS
    # ========================================================

    if not order.reward_given:

        wallet, created = TokenWallet.objects.get_or_create(
            user=order.user
        )


        # Récompense de 20 jetons
        reward = 20


        wallet.balance += reward

        wallet.save()


        # Enregistrer la transaction
        TokenTransaction.objects.create(

            wallet=wallet,

            amount=reward,

            transaction_type="product",

            description=f"Récompense commande #{order.id}"
        )


        # Empêcher de donner les jetons plusieurs fois
        order.reward_given = True


    # Sauvegarder la commande
    order.save()


    # Retour vers la liste des commandes dans l'administration
    return redirect(
        "/admin/orders/order/"
    )