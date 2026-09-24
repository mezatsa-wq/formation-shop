from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Q

from .models import Order


@staff_member_required
def admin_orders(request):

    status_filter = request.GET.get("status", "all")
    search = request.GET.get("search", "").strip()

    orders = Order.objects.select_related(
        "user",
        "seller",
        "product",
    ).order_by("-created_at")

    # =====================================================
    # FILTRE PAR STATUT
    # =====================================================

    if status_filter == "pending_delivery":

        orders = orders.filter(
            seller_confirmed=False,
            admin_validated=False
        )

    elif status_filter == "seller_delivered":

        orders = orders.filter(
            seller_confirmed=True,
            customer_confirmed=False,
            admin_validated=False
        )

    elif status_filter == "ready":

        orders = orders.filter(
            seller_confirmed=True,
            customer_confirmed=True,
            admin_validated=False
        )

    elif status_filter == "completed":

        orders = orders.filter(
            admin_validated=True
        )

    # =====================================================
    # RECHERCHE
    # =====================================================

    if search:

        orders = orders.filter(
            Q(user__username__icontains=search)
            | Q(seller__username__icontains=search)
            | Q(product__name__icontains=search)
            | Q(full_name__icontains=search)
            | Q(phone_number__icontains=search)
        )

    # =====================================================
    # STATISTIQUES
    # =====================================================

    total_orders = Order.objects.count()

    pending_delivery = Order.objects.filter(
        seller_confirmed=False,
        admin_validated=False
    ).count()

    seller_delivered = Order.objects.filter(
        seller_confirmed=True,
        customer_confirmed=False,
        admin_validated=False
    ).count()

    ready_for_validation = Order.objects.filter(
        seller_confirmed=True,
        customer_confirmed=True,
        admin_validated=False
    ).count()

    completed_orders = Order.objects.filter(
        admin_validated=True
    ).count()

    context = {
        "orders": orders,

        "total_orders": total_orders,
        "pending_delivery": pending_delivery,
        "seller_delivered": seller_delivered,
        "ready_for_validation": ready_for_validation,
        "completed_orders": completed_orders,

        "status_filter": status_filter,
        "search": search,
    }

    return render(
        request,
        "accounts/admin_orders.html",
        context
    )