from django.shortcuts import render

from courses.models import Course
from products.models import Product


def home(request):

    courses = Course.objects.filter(
        is_published=True
    ).order_by("-created_at")[:6]

    products = Product.objects.filter(
        stock__gt=0
    ).order_by("-created_at")[:6]

    return render(
        request,
        "home.html",
        {
            "courses": courses,
            "products": products,
            "courses_count": Course.objects.filter(
                is_published=True
            ).count(),
            "products_count": Product.objects.filter(
                stock__gt=0
            ).count(),
        }
    )