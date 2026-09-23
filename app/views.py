from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User

from courses.models import Course
from products.models import Product
from orders.models import Order, CoursePayment
from accounts.models import TrainerApplication


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