# ============================================================
# ADMINISTRATION FORMSHOP
# ============================================================

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from courses.models import Course
from products.models import Product

from accounts.models import (
    SellerApplication,
    SellerSubscription,
    TrainerApplication,
    TrainerProfile,
    TrainerWallet,
)

from orders.models import Order, CoursePayment


@login_required
def admin_dashboard(request):

    if not request.user.is_superuser:
        return render(
            request,
            "app/access_denied.html",
            status=403
        )

    # ========================================================
    # FORMATEURS
    # ========================================================

    pending_applications = (
        TrainerApplication.objects
        .filter(status="pending")
        .select_related("user")
        .order_by("-created_at")[:5]
    )

    pending_trainers_count = TrainerApplication.objects.filter(
        status="pending"
    ).count()

    total_trainers = TrainerApplication.objects.filter(
        status="approved"
    ).count()

    # ========================================================
    # VENDEURS
    # ========================================================

    pending_seller_application_list = (
        SellerApplication.objects
        .filter(status="pending")
        .select_related("user")
        .order_by("-created_at")
    )

    pending_seller_applications = (
        pending_seller_application_list.count()
    )

    # ========================================================
    # PREMIUM
    # ========================================================

    pending_premium_subscription_list = (
        SellerSubscription.objects
        .filter(status="pending")
        .select_related("seller")
        .order_by("-created_at")
    )

    pending_premium_subscriptions = (
        pending_premium_subscription_list.count()
    )

    # ========================================================
    # STATISTIQUES
    # ========================================================

    context = {

        "total_users": User.objects.count(),

        "total_trainers": total_trainers,

        "pending_trainers_count": pending_trainers_count,

        "pending_applications": pending_applications,

        "total_courses": Course.objects.count(),

        "total_products": Product.objects.count(),

        "total_orders": Order.objects.count(),

        "pending_orders": Order.objects.filter(
            payment_status="pending"
        ).count(),

        "pending_course_payments": CoursePayment.objects.filter(
            status="pending"
        ).count(),

        # ----------------------------------------------------
        # VENDEURS
        # ----------------------------------------------------

        "pending_seller_applications": pending_seller_applications,

        "pending_seller_application_list": (
            pending_seller_application_list
        ),

        # ----------------------------------------------------
        # PREMIUM
        # ----------------------------------------------------

        "pending_premium_subscriptions": (
            pending_premium_subscriptions
        ),

        "pending_premium_subscription_list": (
            pending_premium_subscription_list
        ),
    }

    return render(
        request,
        "app/admin_dashboard.html",
        context
    )


# ============================================================
# LISTE DES CANDIDATURES FORMATEURS
# ============================================================

@login_required
def admin_trainers(request):

    if not request.user.is_superuser:
        return render(
            request,
            "app/access_denied.html",
            status=403
        )

    applications = (
        TrainerApplication.objects
        .select_related("user")
        .order_by("-created_at")
    )

    return render(
        request,
        "app/admin_trainers.html",
        {
            "applications": applications
        }
    )


# ============================================================
# DETAIL CANDIDATURE FORMATEUR
# ============================================================

@login_required
def admin_trainer_detail(request, application_id):

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
            "application": application
        }
    )


# ============================================================
# ACCEPTER FORMATEUR
# ============================================================

@login_required
def admin_trainer_approve(request, application_id):

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

        application.status = "approved"

        application.save(
            update_fields=["status"]
        )

        TrainerProfile.objects.get_or_create(
            user=application.user,
            defaults={
                "bio": application.description,
                "phone": application.phone,
                "expertise": application.expertise,
            }
        )

        TrainerWallet.objects.get_or_create(
            user=application.user
        )

        messages.success(
            request,
            f"{application.user.username} est maintenant formateur."
        )

    return redirect("admin_trainers")


# ============================================================
# REFUSER FORMATEUR
# ============================================================

@login_required
def admin_trainer_reject(request, application_id):

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

        application.save(
            update_fields=["status"]
        )

        messages.warning(
            request,
            f"La candidature de {application.user.username} "
            f"a été refusée."
        )

    return redirect("admin_trainers")