from django.contrib import admin

from .models import CoursePayment, Order
from courses.models import Enrollment


# =========================================================
# PAIEMENTS DES FORMATIONS
# =========================================================

@admin.register(CoursePayment)
class CoursePaymentAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "course",
        "phone_number",
        "method",
        "amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "method",
        "created_at",
    )

    search_fields = (
        "user__username",
        "course__title",
        "phone_number",
    )

    actions = [
        "confirm_payments",
        "reject_payments",
    ]

    @admin.action(
        description="✅ Confirmer les paiements sélectionnés"
    )
    def confirm_payments(self, request, queryset):

        confirmed = 0

        for payment in queryset:

            if payment.status != "pending":
                continue

            payment.status = "confirmed"

            payment.save(
                update_fields=["status"]
            )

            Enrollment.objects.get_or_create(
                user=payment.user,
                course=payment.course
            )

            confirmed += 1

        self.message_user(
            request,
            f"{confirmed} paiement(s) confirmé(s)."
        )

    @admin.action(
        description="❌ Refuser les paiements sélectionnés"
    )
    def reject_payments(self, request, queryset):

        rejected = 0

        for payment in queryset:

            if payment.status != "pending":
                continue

            payment.status = "rejected"

            payment.save(
                update_fields=["status"]
            )

            rejected += 1

        self.message_user(
            request,
            f"{rejected} paiement(s) refusé(s)."
        )


# =========================================================
# COMMANDES DE PRODUITS
# =========================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "product",
        "quantity",
        "total_price",
        "full_name",
        "phone_number",
        "status",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "created_at",
    )

    search_fields = (
        "user__username",
        "product__name",
        "full_name",
        "phone_number",
        "delivery_address",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    fieldsets = (
        (
            "📦 Commande",
            {
                "fields": (
                    "user",
                    "product",
                    "quantity",
                    "total_price",
                )
            }
        ),

        (
            "🚚 Informations de livraison",
            {
                "fields": (
                    "full_name",
                    "phone_number",
                    "delivery_address",
                )
            }
        ),

        (
            "💰 Paiement et livraison",
            {
                "fields": (
                    "status",
                    "payment_status",
                    "reward_given",
                )
            }
        ),

        (
            "📅 Informations système",
            {
                "fields": (
                    "created_at",
                )
            }
        ),
    )