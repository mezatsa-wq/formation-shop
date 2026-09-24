from django.contrib import admin
from django.db import transaction

from .models import (
    CoursePayment,
    Order,
    OrderNotification,
)

from courses.models import Enrollment

from accounts.models import (
    TrainerWallet,
    TrainerEarning,
    TrainerNotification,
    TokenWallet,
    TokenTransaction,
    SellerEarning,
)


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

            # =========================================
            # 1. CONFIRMER LE PAIEMENT
            # =========================================

            payment.status = "confirmed"

            payment.save(
                update_fields=["status"]
            )

            # =========================================
            # 2. INSCRIRE L'ÉTUDIANT À LA FORMATION
            # =========================================

            Enrollment.objects.get_or_create(
                user=payment.user,
                course=payment.course
            )

            # =========================================
            # 3. RÉCUPÉRER LE FORMATEUR
            # =========================================

            trainer = payment.course.instructor

            # =========================================
            # 4. AJOUTER L'ARGENT AU PORTEFEUILLE
            # =========================================

            trainer_wallet, created = TrainerWallet.objects.get_or_create(
                user=trainer
            )

            trainer_wallet.balance += payment.amount

            trainer_wallet.save()

            # =========================================
            # 5. CRÉER L'HISTORIQUE DU REVENU
            # =========================================

            TrainerEarning.objects.create(
                trainer=trainer,
                payment=payment,
                amount=payment.amount,
                description=(
                    f"Gain provenant de la formation : "
                    f"{payment.course.title}"
                )
            )

            # =========================================
            # 6. NOTIFICATION DU FORMATEUR
            # =========================================

            notification_title = "💰 Nouveau revenu"

            notification_message = (
                f"Vous avez reçu {payment.amount} FCFA "
                f"pour la vente de votre formation "
                f"« {payment.course.title} »."
            )

            TrainerNotification.objects.filter(
                trainer=trainer,
                title=notification_title,
                message=notification_message
            ).delete()

            TrainerNotification.objects.create(
                trainer=trainer,
                title=notification_title,
                message=notification_message
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
        "seller",
        "product",
        "quantity",
        "total_price",
        "status",
        "payment_status",
        "seller_confirmed",
        "customer_confirmed",
        "admin_validated",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "seller_confirmed",
        "customer_confirmed",
        "admin_validated",
        "created_at",
    )

    search_fields = (
        "user__username",
        "seller__username",
        "product__name",
        "full_name",
        "phone_number",
        "neighborhood",
        "delivery_address",
    )

    readonly_fields = (
        "created_at",
        "seller_confirmed_at",
        "customer_confirmed_at",
        "admin_validated_at",
    )

    ordering = (
        "-created_at",
    )

    actions = [
        "validate_selected_orders",
    ]

    fieldsets = (

        # =================================================
        # COMMANDE
        # =================================================

        (
            "📦 Commande",
            {
                "fields": (
                    "user",
                    "seller",
                    "product",
                    "quantity",
                    "total_price",
                )
            }
        ),

        # =================================================
        # CLIENT
        # =================================================

        (
            "👤 Informations du client",
            {
                "fields": (
                    "full_name",
                    "phone_number",
                    "neighborhood",
                    "delivery_address",
                )
            }
        ),

        # =================================================
        # LIVRAISON
        # =================================================

        (
            "🚚 Livraison",
            {
                "fields": (
                    "delivery_deadline",
                    "status",
                )
            }
        ),

        # =================================================
        # CONFIRMATIONS
        # =================================================

        (
            "✅ Confirmations",
            {
                "fields": (
                    "seller_confirmed",
                    "seller_confirmed_at",
                    "customer_confirmed",
                    "customer_confirmed_at",
                    "admin_validated",
                    "admin_validated_at",
                )
            }
        ),

        # =================================================
        # PAIEMENT ET RÉCOMPENSE
        # =================================================

        (
            "💰 Paiement et récompense",
            {
                "fields": (
                    "payment_status",
                    "reward_given",
                )
            }
        ),

        # =================================================
        # SYSTÈME
        # =================================================

        (
            "📅 Informations système",
            {
                "fields": (
                    "created_at",
                )
            }
        ),
    )

    # =====================================================
    # ACTION : VALIDER LES COMMANDES
    # =====================================================

    @admin.action(
        description="✅ Valider définitivement les commandes sélectionnées"
    )
    @transaction.atomic
    def validate_selected_orders(self, request, queryset):

        validated = 0
        refused = 0

        for order in queryset:

            # ---------------------------------------------
            # Déjà validée
            # ---------------------------------------------

            if order.admin_validated:
                continue

            # ---------------------------------------------
            # Le vendeur doit avoir confirmé
            # ---------------------------------------------

            if not order.seller_confirmed:
                refused += 1
                continue

            # ---------------------------------------------
            # Le client doit avoir confirmé
            # ---------------------------------------------

            if not order.customer_confirmed:
                refused += 1
                continue

            # ---------------------------------------------
            # 1. VALIDATION ADMINISTRATEUR
            # ---------------------------------------------

            order.admin_validated = True

            # ---------------------------------------------
            # 2. DATE DE VALIDATION
            # ---------------------------------------------

            from django.utils import timezone

            order.admin_validated_at = timezone.now()

            # ---------------------------------------------
            # 3. STATUT DE LA COMMANDE
            # ---------------------------------------------

            order.status = "delivered"

            # ---------------------------------------------
            # 4. PAIEMENT FINAL
            # ---------------------------------------------

            order.payment_status = "paid"

            # =================================================
            # 5. RÉCOMPENSE CLIENT
            # =================================================

            if order.product and not order.reward_given:

                wallet, created = TokenWallet.objects.get_or_create(
                    user=order.user
                )

                reward = order.product.reward_tokens

                wallet.balance += reward

                wallet.save(
                    update_fields=["balance"]
                )

                TokenTransaction.objects.create(
                    wallet=wallet,
                    amount=reward,
                    transaction_type="product",
                    description=(
                        f"Récompense commande #{order.id}"
                    )
                )

                order.reward_given = True

            # =================================================
            # 6. ENREGISTRER LE REVENU DU VENDEUR
            # =================================================

            if order.seller:

                SellerEarning.objects.get_or_create(
                    order=order,
                    defaults={
                        "seller": order.seller,
                        "amount": order.total_price,
                        "description": (
                            f"Vente du produit "
                            f"« {order.product.name} » "
                            f"- commande #{order.id}"
                        ),
                    }
                )

            # =================================================
            # 7. SAUVEGARDER LA COMMANDE
            # =================================================

            order.save(
                update_fields=[
                    "admin_validated",
                    "admin_validated_at",
                    "status",
                    "payment_status",
                    "reward_given",
                ]
            )

            # =================================================
            # 8. NOTIFICATION CLIENT
            # =================================================

            OrderNotification.objects.create(
                recipient=order.user,
                order=order,
                title="Commande validée",
                message=(
                    f"La commande #{order.id} a été validée "
                    f"par l'administrateur.\n\n"
                    f"Votre récompense de "
                    f"{order.product.reward_tokens if order.product else 0} "
                    f"jetons a été ajoutée à votre portefeuille."
                )
            )

            # =================================================
            # 9. NOTIFICATION VENDEUR
            # =================================================

            if order.seller:

                OrderNotification.objects.create(
                    recipient=order.seller,
                    order=order,
                    title="Vente validée",
                    message=(
                        f"La commande #{order.id} a été validée "
                        f"par l'administrateur.\n\n"
                        f"Votre revenu de "
                        f"{order.total_price} FCFA "
                        f"a été enregistré."
                    )
                )

            validated += 1

        # =====================================================
        # MESSAGE ADMIN
        # =====================================================

        if validated:

            self.message_user(
                request,
                f"{validated} commande(s) validée(s) définitivement."
            )

        if refused:

            self.message_user(
                request,
                f"{refused} commande(s) n'ont pas pu être validée(s) "
                f"car les confirmations vendeur/client sont incomplètes.",
                level="warning"
            )