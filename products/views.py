from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models
from .models import Product
from .forms import ProductForm
from django.utils import timezone

def update_expired_boosts():
    """
    Désactive automatiquement les mises en avant expirées.
    """

    now = timezone.now()

    Product.objects.filter(
        is_featured=True,
        boost_until__isnull=False,
        boost_until__lt=now
    ).update(
        is_featured=False,
        boost_until=None
    )
def product_list(request):

    update_expired_boosts()

    search = request.GET.get("search", "").strip()

    products = Product.objects.filter(
        stock__gt=0
    )

    if search:
        products = products.filter(
            models.Q(name__icontains=search) |
            models.Q(description__icontains=search)
        )

    products = products.order_by(
        "-is_featured",
        "-created_at"
    )

    return render(
        request,
        "products/list.html",
        {
            "products": products,
            "search": search,
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


@login_required
def create_product(request):

    if not hasattr(request.user, "seller_profile"):

        messages.error(
            request,
            "Vous devez être un vendeur approuvé pour créer un produit."
        )

        return redirect("home")

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            product = form.save(
                commit=False
            )

            product.seller = request.user

            product.save()

            messages.success(
                request,
                "Votre produit a été créé avec succès."
            )

            return redirect(
                "my_products"
            )

    else:

        form = ProductForm()

    return render(
        request,
        "products/create.html",
        {
            "form": form
        }
    )


@login_required
def my_products(request):

    if not hasattr(request.user, "seller_profile"):

        messages.error(
            request,
            "Vous devez être un vendeur approuvé."
        )

        return redirect("home")

    products = Product.objects.filter(
        seller=request.user
    ).order_by("-created_at")

    return render(
        request,
        "products/my_products.html",
        {
            "products": products
        }
    )
@login_required
def feature_product(request, product_id):

    if not hasattr(request.user, "seller_profile"):
        messages.error(
            request,
            "Vous devez être un vendeur approuvé."
        )
        return redirect("home")

    from accounts.models import is_premium_seller

    if not is_premium_seller(request.user):
        messages.error(
            request,
            "La mise en avant des produits est réservée aux vendeurs Premium."
        )
        return redirect("my_products")

    product = get_object_or_404(
        Product,
        id=product_id,
        seller=request.user
    )

    if request.method == "POST":

        days = request.POST.get("days", "7")

        try:
            days = int(days)
        except ValueError:
            days = 7

        if days not in [7, 15, 30]:
            messages.error(
                request,
                "Durée de mise en avant invalide."
            )
            return redirect("my_products")

        product.is_featured = True
        product.boost_until = timezone.now() + timezone.timedelta(
            days=days
        )

        product.save(
            update_fields=[
                "is_featured",
                "boost_until"
            ]
        )

        messages.success(
            request,
            f"Votre produit est maintenant mis en avant pendant {days} jours."
        )

        return redirect("my_products")

    return render(
        request,
        "products/feature.html",
        {
            "product": product
        }
    )


@login_required
def edit_product(request, product_id):

    if not hasattr(request.user, "seller_profile"):

        messages.error(
            request,
            "Vous devez être un vendeur approuvé."
        )

        return redirect("home")

    product = get_object_or_404(
        Product,
        id=product_id,
        seller=request.user
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Votre produit a été modifié avec succès."
            )

            return redirect(
                "my_products"
            )

    else:

        form = ProductForm(
            instance=product
        )

    return render(
        request,
        "products/edit.html",
        {
            "form": form,
            "product": product,
        }
    )


@login_required
def delete_product(request, product_id):

    if not hasattr(request.user, "seller_profile"):

        messages.error(
            request,
            "Vous devez être un vendeur approuvé."
        )

        return redirect("home")

    product = get_object_or_404(
        Product,
        id=product_id,
        seller=request.user
    )

    if request.method == "POST":

        product.delete()

        messages.success(
            request,
            "Votre produit a été supprimé."
        )

        return redirect(
            "my_products"
        )

    return render(
        request,
        "products/delete.html",
        {
            "product": product
        }
    )