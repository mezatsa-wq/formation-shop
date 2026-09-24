from django.db.models import Count, Sum
from django.shortcuts import render

from courses.models import Course
from products.models import Product


def home(request):

    courses = (
        Course.objects
        .filter(
            is_published=True,
            students__isnull=False
        )
        .annotate(
            popularity=Count("students", distinct=True)
        )
        .order_by("-popularity", "-created_at")[:6]
    )

    products = (
        Product.objects
        .filter(
            stock__gt=0,
            order__isnull=False
        )
        .annotate(
            popularity=Sum("order__quantity")
        )
        .order_by("-popularity", "-created_at")[:6]
    )

    courses_count = Course.objects.filter(
        is_published=True
    ).count()

    products_count = Product.objects.filter(
        stock__gt=0
    ).count()

    return render(
        request,
        "home.html",
        {
            "courses": courses,
            "products": products,
            "courses_count": courses_count,
            "products_count": products_count,
        }
    )