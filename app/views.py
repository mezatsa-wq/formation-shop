from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from accounts.models import (
    TrainerApplication,
    TrainerProfile,
    TrainerWallet,
)
from courses.models import Course
from orders.models import Order, CoursePayment
from products.models import Product


@login_required
def admin_dashboard(request):
    # Sécurité : seul le superadministrateur peut accéder au dashboard
    if not request.user.is_superuser:
        return render(request, "app/access_denied.html", status=403)

    context = {
        "total_users": User.objects.count(),
        "total_trainers": TrainerApplication.objects.filter(
            status="approved"
        ).count(),
        "total_courses": Course.objects.count(),
        "total_products": Product.objects.count(),
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(
            payment_status="pending"
        ).count(),
        "pending_course_payments": CoursePayment.objects.filter(
            status="pending"
        ).count(),
    }

    return render(request, "app/admin_dashboard.html", context)
@login_required
def admin_trainers(request):
    # Seul un superutilisateur peut accéder à cette page
    if not request.user.is_superuser:
        return render(
            request,
            "app/access_denied.html",
            status=403
        )

    applications = TrainerApplication.objects.select_related(
        "user"
    ).order_by("-created_at")

    return render(
        request,
        "app/admin_trainers.html",
        {
            "applications": applications,
        }
    )


@login_required
def admin_trainer_detail(request, application_id):
    # Protection administrateur
    if not request.user.is_superuser:
        return render(
            request,
            "app/access_denied.html",
            status=403
        )

    application = get_object_or_404(
        TrainerApplication,
        id=application_id
    )

    return render(
        request,
        "app/admin_trainer_detail.html",
        {
            "application": application,
        }
    )


@login_required
def admin_trainer_approve(request, application_id):
    # Protection administrateur
    if not request.user.is_superuser:
        return render(
            request,
            "app/access_denied.html",
            status=403
        )

    application = get_object_or_404(
        TrainerApplication,
        id=application_id
    )

    if request.method == "POST":

        # Accepter la candidature
        application.status = "approved"
        application.save(update_fields=["status"])

        # Créer le profil formateur s'il n'existe pas
        TrainerProfile.objects.get_or_create(
            user=application.user,
            defaults={
                "bio": application.description,
                "phone": application.phone,
                "expertise": application.expertise,
            }
        )

        # Créer le portefeuille du formateur s'il n'existe pas
        TrainerWallet.objects.get_or_create(
            user=application.user
        )

        messages.success(
            request,
            f"La candidature de {application.user.username} "
            "a été acceptée."
        )

        return redirect("admin_trainers")

    return redirect("admin_trainers")


@login_required
def admin_trainer_reject(request, application_id):
    # Protection administrateur
    if not request.user.is_superuser:
        return render(
            request,
            "app/access_denied.html",
            status=403
        )

    application = get_object_or_404(
        TrainerApplication,
        id=application_id
    )

    if request.method == "POST":

        application.status = "rejected"
        application.save(update_fields=["status"])

        messages.warning(
            request,
            f"La candidature de {application.user.username} "
            "a été refusée."
        )

        return redirect("admin_trainers")

    return redirect("admin_trainers")