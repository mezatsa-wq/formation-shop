from django.contrib import admin, messages
from django.db import transaction

from .models import (
    TrainerApplication,
    TrainerProfile,
    TrainerWallet,
    TrainerEarning,
    TrainerNotification,
    WithdrawalRequest,
)


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

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__username",
        "full_name",
        "phone",
        "expertise",
    )

    readonly_fields = (
        "user",
        "full_name",
        "phone",
        "expertise",
        "description",
        "created_at",
        "updated_at",
    )

    actions = [
        "approve_applications",
        "reject_applications",
    ]

    @admin.action(
        description="✅ Accepter les candidatures sélectionnées"
    )
    def approve_applications(self, request, queryset):

        accepted = 0

        for application in queryset:

            # On traite uniquement les candidatures en attente
            if application.status != "pending":
                continue

            with transaction.atomic():

                # 1. Changer le statut
                application.status = "approved"
                application.save(
                    update_fields=["status"]
                )

                # 2. Créer le profil formateur
                TrainerProfile.objects.get_or_create(
                    user=application.user,
                    defaults={
                        "bio": application.description,
                        "phone": application.phone,
                        "expertise": application.expertise,
                    }
                )

                # 3. Créer le portefeuille formateur
                TrainerWallet.objects.get_or_create(
                    user=application.user
                )

                # 4. Créer une notification
                TrainerNotification.objects.create(
                    trainer=application.user,
                    title="Candidature acceptée",
                    message=(
                        "Félicitations ! Votre candidature pour devenir "
                        "formateur a été acceptée. Vous pouvez maintenant "
                        "accéder à votre espace formateur."
                    )
                )

            accepted += 1

        self.message_user(
            request,
            f"{accepted} candidature(s) acceptée(s).",
            messages.SUCCESS
        )


    @admin.action(
        description="❌ Refuser les candidatures sélectionnées"
    )
    def reject_applications(self, request, queryset):

        rejected = 0

        for application in queryset:

            # On traite uniquement les candidatures en attente
            if application.status != "pending":
                continue

            with transaction.atomic():

                # 1. Changer le statut
                application.status = "rejected"
                application.save(
                    update_fields=["status"]
                )

                # 2. Prévenir le candidat
                TrainerNotification.objects.create(
                    trainer=application.user,
                    title="Candidature refusée",
                    message=(
                        "Votre candidature pour devenir formateur "
                        "n'a malheureusement pas été retenue."
                    )
                )

            rejected += 1

        self.message_user(
            request,
            f"{rejected} candidature(s) refusée(s).",
            messages.WARNING
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

    search_fields = (
        "user__username",
    )


@admin.register(TrainerEarning)
class TrainerEarningAdmin(admin.ModelAdmin):

    list_display = (
        "trainer",
        "payment",
        "amount",
        "description",
        "created_at",
    )

    search_fields = (
        "trainer__username",
    )


@admin.register(TrainerNotification)
class TrainerNotificationAdmin(admin.ModelAdmin):

    list_display = (
        "trainer",
        "title",
        "is_read",
        "created_at",
    )

    list_filter = (
        "is_read",
        "created_at",
    )

    search_fields = (
        "trainer__username",
        "title",
        "message",
    )


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