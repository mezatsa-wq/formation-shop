# ============================================================
# ADMINISTRATION FORMSHOP
# ============================================================

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from courses.models import Course
from products.models import Product
from accounts.models import SellerApplication
from orders.models import Order, CoursePayment
from accounts.models import (
    TrainerApplication,
    TrainerProfile,
    TrainerWallet,
)


@login_required
def admin_dashboard(request):

    if not request.user.is_superuser:
        return render(
            request,
            "app/access_denied.html",
            status=403
        )

    pending_applications = TrainerApplication.objects.filter(
        status="pending"
    ).select_related("user").order_by("-created_at")[:5]
    pending_seller_application_list = SellerApplication.objects.filter(
        status="pending"
    ).select_related("user").order_by("-created_at")

    pending_seller_applications = pending_seller_application_list.count()
    context = {
        "total_users": User.objects.count(),

        "total_trainers": TrainerApplication.objects.filter(
            status="approved"
        ).count(),
        "pending_seller_applications": pending_seller_applications,
        "pending_seller_application_list": pending_seller_application_list,
        "total_courses": Course.objects.count(),

        "total_products": Product.objects.count(),

        "total_orders": Order.objects.count(),

        "pending_orders": Order.objects.filter(
            payment_status="pending"
        ).count(),

        "pending_course_payments": CoursePayment.objects.filter(
            status="pending"
        ).count(),

        "pending_applications": pending_applications,

        "pending_trainers_count": TrainerApplication.objects.filter(
            status="pending"
        ).count(),
    }

    return render(
        request,
        "app/admin_dashboard.html",
        context
    )


@login_required
def admin_trainers(request):

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
            "applications": applications
        }
    )


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
        application.save(update_fields=["status"])

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
        application.save(update_fields=["status"])

        messages.warning(
            request,
            f"La candidature de {application.user.username} "
            "a été refusée."
        )

    return redirect("admin_trainers")