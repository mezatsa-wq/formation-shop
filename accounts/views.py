from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from documents.models import DocumentPurchase

from .models import (
    TrainerApplication,
    TrainerProfile,
    TrainerWallet,
    TrainerEarning,
    TrainerNotification,
    TokenWallet,
)


def register_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        form = UserCreationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            # Création du portefeuille de jetons
            wallet, created = TokenWallet.objects.get_or_create(
                user=user
            )

            # Bonus quotidien de 20 jetons
            wallet.give_daily_reward()

            return redirect("home")

    else:
        form = UserCreationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            # Récupération ou création du portefeuille
            wallet, created = TokenWallet.objects.get_or_create(
                user=user
            )

            # Attribution du bonus quotidien
            wallet.give_daily_reward()

            return redirect("home")

    else:
        form = AuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {"form": form}
    )


def logout_view(request):

    logout(request)

    return redirect("home")


@login_required
def profile_view(request):

    wallet, created = TokenWallet.objects.get_or_create(
        user=request.user
    )

    document_purchases = DocumentPurchase.objects.filter(
        user=request.user
    ).select_related(
        "document"
    ).order_by(
        "-purchased_at"
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "wallet": wallet,
            "document_purchases": document_purchases,
        }
    )

@login_required
def become_trainer(request):

    existing_application = TrainerApplication.objects.filter(
        user=request.user
    ).first()

    if existing_application:

        if existing_application.status == "pending":
            messages.info(
                request,
                "Votre candidature pour devenir formateur est déjà en attente."
            )
            return redirect("home")

        if existing_application.status == "approved":
            messages.info(
                request,
                "Vous êtes déjà formateur."
            )
            return redirect("home")

        if existing_application.status == "rejected":
            messages.info(
                request,
                "Votre candidature a été refusée."
            )
            return redirect("home")

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        expertise = request.POST.get("expertise")
        description = request.POST.get("description")

        if not full_name or not phone or not expertise or not description:

            messages.error(
                request,
                "Veuillez remplir tous les champs."
            )

            return render(
                request,
                "accounts/become_trainer.html"
            )

        TrainerApplication.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            expertise=expertise,
            description=description
        )

        messages.success(
            request,
            "Votre candidature a été envoyée à l'administrateur."
        )

        return redirect("home")

    return render(
        request,
        "accounts/become_trainer.html"
    )

@login_required
def trainer_dashboard(request):

    trainer_profile = TrainerProfile.objects.filter(
        user=request.user
    ).first()

    trainer_wallet = None
    notifications = []
    unread_notifications = 0
    earnings = []
    trainer_courses = []

    if trainer_profile:
        trainer_wallet, created = TrainerWallet.objects.get_or_create(
            user=request.user
        )

        notifications = TrainerNotification.objects.filter(
            trainer=request.user
        ).order_by("-created_at")[:5]

        unread_notifications = notifications.filter(
            is_read=False
        ).count()

        earnings = TrainerEarning.objects.filter(
            trainer=request.user
        ).order_by("-created_at")

        trainer_courses = request.user.courses.all()

    wallet, created = TokenWallet.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        "accounts/trainer_dashboard.html",
        {
            "wallet": wallet,
            "trainer_profile": trainer_profile,
            "trainer_wallet": trainer_wallet,
            "notifications": notifications,
            "unread_notifications": unread_notifications,
            "earnings": earnings,
            "trainer_courses": trainer_courses,
        }
    )