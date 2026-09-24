from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import (
    TrainerApplication,
    TrainerProfile,
    TrainerWallet,
    TrainerEarning,
    TrainerNotification,
    WithdrawalRequest,
    SellerApplication,
    SellerProfile,
    SellerSubscription,
)


# ============================================================
# FORMATEURS
# ============================================================

@admin.register(TrainerApplication)
class TrainerApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "phone",
        "expertise",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "user__username",
        "full_name",
        "phone",
        "expertise",
    )
    actions = ["approve_applications", "reject_applications"]

    @admin.action(description="Accepter les demandes sélectionnées")
    def approve_applications(self, request, queryset):
        approved = 0

        for application in queryset:
            if application.status == "approved":
                continue

            application.status = "approved"
            application.save(update_fields=["status", "updated_at"])

            TrainerProfile.objects.get_or_create(
                user=application.user,
                defaults={
                    "phone": application.phone,
                    "expertise": application.expertise,
                    "bio": application.description,
                },
            )

            TrainerWallet.objects.get_or_create(
                user=application.user
            )

            TrainerNotification.objects.create(
                trainer=application.user,
                title="Demande de formateur acceptée",
                message=(
                    "Félicitations ! Votre demande pour devenir formateur "
                    "sur FormaShop a été acceptée. Vous pouvez maintenant "
                    "créer et gérer vos formations."
                ),
            )

            approved += 1

        self.message_user(
            request,
            f"{approved} demande(s) de formateur acceptée(s).",
            messages.SUCCESS,
        )

    @admin.action(description="Refuser les demandes sélectionnées")
    def reject_applications(self, request, queryset):
        rejected = 0

        for application in queryset:
            if application.status == "rejected":
                continue

            application.status = "rejected"
            application.save(update_fields=["status", "updated_at"])

            TrainerNotification.objects.create(
                trainer=application.user,
                title="Demande de formateur refusée",
                message=(
                    "Votre demande pour devenir formateur sur FormaShop "
                    "a été refusée."
                ),
            )

            rejected += 1

        self.message_user(
            request,
            f"{rejected} demande(s) de formateur refusée(s).",
            messages.WARNING,
        )


@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "expertise",
        "phone",
        "created_at",
    )
    search_fields = (
        "user__username",
        "expertise",
        "phone",
    )


@admin.register(TrainerWallet)
class TrainerWalletAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "balance",
        "updated_at",
    )
    search_fields = ("user__username",)


@admin.register(TrainerEarning)
class TrainerEarningAdmin(admin.ModelAdmin):
    list_display = (
        "trainer",
        "amount",
        "description",
        "created_at",
    )
    search_fields = (
        "trainer__username",
        "description",
    )
    list_filter = ("created_at",)


@admin.register(TrainerNotification)
class TrainerNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "trainer",
        "title",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "created_at")
    search_fields = (
        "trainer__username",
        "title",
        "message",
    )


# ============================================================
# RETRAITS DES FORMATEURS
# ============================================================

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "trainer",
        "amount",
        "method",
        "phone_number",
        "status",
        "created_at",
        "paid_at",
    )
    list_filter = (
        "status",
        "method",
        "created_at",
    )
    search_fields = (
        "trainer__username",
        "phone_number",
    )
    actions = ["pay_withdrawals", "reject_withdrawals"]

    @admin.action(description="Marquer les retraits comme payés")
    def pay_withdrawals(self, request, queryset):
        paid = 0
        insufficient = 0
        skipped = 0

        for withdrawal in queryset:

            if withdrawal.status != "pending":
                skipped += 1
                continue

            with transaction.atomic():

                wallet, created = TrainerWallet.objects.get_or_create(
                    user=withdrawal.trainer
                )

                if wallet.balance < withdrawal.amount:
                    insufficient += 1
                    continue

                wallet.balance -= withdrawal.amount
                wallet.save(update_fields=["balance", "updated_at"])

                withdrawal.status = "paid"
                withdrawal.paid_at = timezone.now()
                withdrawal.save(
                    update_fields=["status", "paid_at"]
                )

                TrainerNotification.objects.create(
                    trainer=withdrawal.trainer,
                    title="Retrait effectué",
                    message=(
                        f"Votre demande de retrait de "
                        f"{withdrawal.amount} FCFA a été payée "
                        f"sur le numéro {withdrawal.phone_number} "
                        f"via {withdrawal.get_method_display()}."
                    ),
                )

                paid += 1

        if paid:
            self.message_user(
                request,
                f"{paid} retrait(s) marqué(s) comme payé(s).",
                messages.SUCCESS,
            )

        if insufficient:
            self.message_user(
                request,
                (
                    f"{insufficient} retrait(s) n'ont pas été payé(s) "
                    f"car le solde du portefeuille est insuffisant."
                ),
                messages.ERROR,
            )

        if skipped:
            self.message_user(
                request,
                f"{skipped} retrait(s) ignoré(s) car ils ne sont plus en attente.",
                messages.WARNING,
            )

    @admin.action(description="Refuser les retraits sélectionnés")
    def reject_withdrawals(self, request, queryset):
        rejected = 0
        skipped = 0

        for withdrawal in queryset:

            if withdrawal.status != "pending":
                skipped += 1
                continue

            withdrawal.status = "rejected"
            withdrawal.save(update_fields=["status"])

            TrainerNotification.objects.create(
                trainer=withdrawal.trainer,
                title="Retrait refusé",
                message=(
                    f"Votre demande de retrait de "
                    f"{withdrawal.amount} FCFA a été refusée."
                ),
            )

            rejected += 1

        if rejected:
            self.message_user(
                request,
                f"{rejected} retrait(s) refusé(s).",
                messages.WARNING,
            )

        if skipped:
            self.message_user(
                request,
                f"{skipped} retrait(s) ignoré(s) car ils ne sont plus en attente.",
                messages.WARNING,
            )


# ============================================================
# VENDEURS
# ============================================================

@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "phone",
        "activity",
        "plan",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "plan",
        "created_at",
    )
    search_fields = (
        "user__username",
        "full_name",
        "phone",
        "activity",
    )
    actions = ["approve_applications", "reject_applications"]

    @admin.action(description="Accepter les demandes de vendeur")
    def approve_applications(self, request, queryset):
        approved = 0

        for application in queryset:

            if application.status == "approved":
                continue

            application.status = "approved"
            application.save(update_fields=["status", "updated_at"])

            SellerProfile.objects.update_or_create(
                user=application.user,
                defaults={
                    "full_name": application.full_name,
                    "phone": application.phone,
                    "address": application.address,
                    "neighborhood": application.neighborhood,
                    "city": application.city,
                    "activity": application.activity,
                    "description": application.description,
                    "plan": "standard",
                },
            )

            from accounts.models import TrainerNotification

            TrainerNotification.objects.create(
                trainer=application.user,
                title="Compte vendeur accepté",
                message=(
                    "Votre demande pour devenir vendeur sur FormaShop "
                    "a été acceptée. Vous pouvez maintenant gérer "
                    "vos produits depuis votre espace."
                ),
            )

            approved += 1

        self.message_user(
            request,
            f"{approved} demande(s) de vendeur acceptée(s).",
            messages.SUCCESS,
        )

    @admin.action(description="Refuser les demandes de vendeur")
    def reject_applications(self, request, queryset):
        rejected = 0

        for application in queryset:

            if application.status == "rejected":
                continue

            application.status = "rejected"
            application.save(update_fields=["status", "updated_at"])

            TrainerNotification.objects.create(
                trainer=application.user,
                title="Demande de vendeur refusée",
                message=(
                    "Votre demande pour devenir vendeur sur FormaShop "
                    "a été refusée."
                ),
            )

            rejected += 1

        self.message_user(
            request,
            f"{rejected} demande(s) de vendeur refusée(s).",
            messages.WARNING,
        )


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "activity",
        "plan",
        "city",
        "created_at",
    )
    list_filter = ("plan", "city", "created_at")
    search_fields = (
        "user__username",
        "full_name",
        "phone",
        "activity",
        "city",
    )


# ============================================================
# ABONNEMENTS VENDEUR PREMIUM
# ============================================================

@admin.register(SellerSubscription)
class SellerSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "seller",
        "amount",
        "method",
        "phone_number",
        "status",
        "start_date",
        "end_date",
        "created_at",
    )
    list_filter = (
        "status",
        "method",
        "created_at",
    )
    search_fields = (
        "seller__username",
        "phone_number",
    )
    actions = [
        "validate_subscriptions",
        "reject_subscriptions",
    ]

    @admin.action(description="Valider les abonnements Premium")
    def validate_subscriptions(self, request, queryset):
        validated = 0
        skipped = 0

        for subscription in queryset:

            if subscription.status != "pending":
                skipped += 1
                continue

            if subscription.amount != 1000:
                self.message_user(
                    request,
                    (
                        f"L'abonnement #{subscription.id} ne peut pas "
                        f"être validé : montant incorrect."
                    ),
                    messages.ERROR,
                )
                continue

            seller_profile = SellerProfile.objects.filter(
                user=subscription.seller
            ).first()

            seller_application = SellerApplication.objects.filter(
                user=subscription.seller
            ).first()

            if not seller_profile:
                self.message_user(
                    request,
                    (
                        f"L'abonnement #{subscription.id} ne peut pas "
                        f"être validé : profil vendeur introuvable."
                    ),
                    messages.ERROR,
                )
                continue

            if not seller_application or seller_application.status != "approved":
                self.message_user(
                    request,
                    (
                        f"L'abonnement #{subscription.id} ne peut pas "
                        f"être validé : demande vendeur non acceptée."
                    ),
                    messages.ERROR,
                )
                continue

            today = timezone.localdate()

            subscription.status = "active"
            subscription.start_date = today
            subscription.end_date = today + timedelta(days=30)

            subscription.save(
                update_fields=[
                    "status",
                    "start_date",
                    "end_date",
                ]
            )

            seller_profile.plan = "premium"
            seller_profile.save(update_fields=["plan"])

            TrainerNotification.objects.create(
                trainer=subscription.seller,
                title="Abonnement Premium activé",
                message=(
                    "Votre abonnement vendeur Premium a été validé. "
                    "Votre compte Premium est maintenant actif pendant "
                    "30 jours."
                ),
            )

            validated += 1

        self.message_user(
            request,
            f"{validated} abonnement(s) Premium validé(s).",
            messages.SUCCESS,
        )

        if skipped:
            self.message_user(
                request,
                f"{skipped} abonnement(s) déjà traité(s) ignoré(s).",
                messages.WARNING,
            )

    @admin.action(description="Refuser les abonnements Premium")
    def reject_subscriptions(self, request, queryset):
        rejected = 0

        for subscription in queryset:

            if subscription.status != "pending":
                continue

            subscription.status = "rejected"
            subscription.save(update_fields=["status"])

            TrainerNotification.objects.create(
                trainer=subscription.seller,
                title="Abonnement Premium refusé",
                message=(
                    "Votre demande d'abonnement vendeur Premium "
                    "a été refusée."
                ),
            )

            rejected += 1

        self.message_user(
            request,
            f"{rejected} abonnement(s) Premium refusé(s).",
            messages.WARNING,
        )