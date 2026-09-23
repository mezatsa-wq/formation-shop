from django.shortcuts import render, get_object_or_404

from .models import Product


def product_list(request):

    products = Product.objects.filter(
        stock__gt=0
    ).order_by("-created_at")

    return render(
        request,
        "products/list.html",
        {
            "products": products
        }
    )


def product_detail(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        stock__gt=0
    )

    return render(
        request,
        "products/detail.html",
        {
            "product": product
        }
    )