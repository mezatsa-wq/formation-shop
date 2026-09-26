from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Q, Sum
from django.conf import settings

from courses.models import Course
from documents.models import DocumentPurchase

from .models import (
    TrainerApplication,
    TrainerProfile,
    TrainerWallet,
    TrainerEarning,
    TrainerNotification,
    TokenWallet,
    SellerApplication,
    SellerSubscription,
    SellerProfile,
    SellerEarning,
    UserProfile,
    is_premium_seller,
    get_seller_plan,
)

from orders.models import Order, OrderNotification
from products.models import Product


# =========================================================
# INSCRIPTION
# =========================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        form = UserCreationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            wallet, created = TokenWallet.objects.get_or_create(
                user=user
            )

            wallet.give_daily_reward()

            messages.success(
                request,
                "Votre compte FormaShop a été créé avec succès."
            )

            return redirect("home")

    else:
        form = UserCreationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


# =========================================================
# CONNEXION
# =========================================================

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

            wallet, created = TokenWallet.objects.get_or_create(
                user=user
            )

            wallet.give_daily_reward()

            messages.success(
                request,
                f"Bienvenue sur FormaShop, {user.username}."
            )

            return redirect("home")

    else:
        form = AuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form
        }
    )


# =========================================================
# DÉCONNEXION
# =========================================================

def logout_view(request):

    logout(request)

    return redirect("home")


# =========================================================
# PROFIL UTILISATEUR
# =========================================================

@login_required
def profile_view(request):

    wallet, created = TokenWallet.objects.get_or_create(
        user=request.user
    )

    profile, profile_created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        photo = request.FILES.get("photo")

        if photo:

            profile.photo = photo

            profile.save(
                update_fields=["photo"]
            )

            messages.success(
                request,
                "Votre photo de profil a été mise à jour."
            )

            return redirect("profile")

        messages.error(
            request,
            "Veuillez sélectionner une image."
        )

    document_purchases = (
        DocumentPurchase.objects
        .filter(user=request.user)
        .select_related("document")
        .order_by("-purchased_at")
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "wallet": wallet,
            "document_purchases": document_purchases,
            "profile": profile,
        }
    )


# =========================================================
# TABLEAU DE BORD PRINCIPAL
# =========================================================

@login_required
def dashboard(request):

    user = request.user

    # =====================================================
    # CLIENT
    # =====================================================

    wallet, created = TokenWallet.objects.get_or_create(
        user=user
    )
    wallet.give_daily_reward()

    user_orders = (
        Order.objects
        .filter(user=user)
        .select_related("product", "seller")
        .order_by("-created_at")
    )

    my_orders = user_orders

    total_orders = user_orders.count()

    pending_orders = user_orders.filter(
        status="pending"
    )

    completed_orders = user_orders.filter(
        status="delivered"
    )

    cancelled_orders = user_orders.filter(
        status="cancelled"
    )

    # Notifications reçues par le client
    unread_order_notifications = (
        OrderNotification.objects
        .filter(
            recipient=user,
            is_read=False
        )
        .count()
    )

    # =====================================================
    # VENDEUR
    # =====================================================

    seller_profile = getattr(
        user,
        "seller_profile",
        None
    )

    seller_products = (
        Product.objects
        .filter(seller=user)
        .order_by("-created_at")
    )

    seller_orders = (
        Order.objects
        .filter(
            Q(seller=user) |
            Q(product__seller=user)
        )
        .select_related(
            "product",
            "user",
            "seller"
        )
        .distinct()
        .order_by("-created_at")
    )

    seller_pending_orders = seller_orders.filter(
        status="pending"
    )

    seller_delivered_orders = seller_orders.filter(
        status="seller_delivered"
    )

    seller_completed_orders = seller_orders.filter(
        status="delivered"
    )

    seller_cancelled_orders = seller_orders.filter(
        status="cancelled"
    )

    seller_orders_to_deliver = seller_orders.filter(
        status="pending",
        seller_confirmed=False,
        admin_validated=False
    )

    seller_orders_to_deliver_count = (
        seller_orders_to_deliver.count()
    )

    seller_late_orders = (
        seller_orders
        .filter(
            delivery_deadline__isnull=False,
            delivery_deadline__lt=timezone.now()
        )
        .exclude(
            status__in=[
                "delivered",
                "cancelled"
            ]
        )
    )

    seller_late_orders_count = seller_late_orders.count()

    seller_earnings = (
        SellerEarning.objects
        .filter(seller=user)
        .select_related("order")
        .order_by("-created_at")
    )

    seller_revenue = (
        seller_earnings
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # =====================================================
    # NOTIFICATIONS VENDEUR
    # =====================================================

    seller_notifications = (
        OrderNotification.objects
        .filter(recipient=user)
        .order_by("-created_at")
    )

    seller_unread_notifications = (
        seller_notifications
        .filter(is_read=False)
        .count()
    )

    seller_is_premium = is_premium_seller(user)

    # =====================================================
    # FORMATEUR
    # =====================================================

    trainer_profile = (
        TrainerProfile.objects
        .filter(user=user)
        .first()
    )

    trainer_courses = []
    trainer_wallet = None
    trainer_revenue = 0
    trainer_notifications = []
    trainer_unread_notifications = 0

    if trainer_profile:

        trainer_wallet, created = (
            TrainerWallet.objects.get_or_create(
                user=user
            )
        )

        trainer_courses = (
            user.courses
            .all()
            .order_by("-created_at")
        )

        trainer_earnings = (
            TrainerEarning.objects
            .filter(trainer=user)
            .order_by("-created_at")
        )

        trainer_revenue = sum(
            earning.amount
            for earning in trainer_earnings
        )

        trainer_notifications = (
            TrainerNotification.objects
            .filter(trainer=user)
            .order_by("-created_at")
        )

        trainer_unread_notifications = (
            trainer_notifications
            .filter(is_read=False)
            .count()
        )

    # =====================================================
    # CONTEXTE
    # =====================================================

    context = {

        # -------------------------
        # CLIENT
        # -------------------------

        "wallet": wallet,

        "user_orders": user_orders,
        "my_orders": my_orders,

        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,

        "unread_order_notifications":
            unread_order_notifications,


        # -------------------------
        # VENDEUR
        # -------------------------

        "seller_profile":
            seller_profile,

        "seller_products":
            seller_products,

        "seller_orders":
            seller_orders,

        "seller_pending_orders":
            seller_pending_orders,

        "seller_delivered_orders":
            seller_delivered_orders,

        "seller_completed_orders":
            seller_completed_orders,

        "seller_cancelled_orders":
            seller_cancelled_orders,

        "seller_orders_to_deliver":
            seller_orders_to_deliver,

        "seller_orders_to_deliver_count":
            seller_orders_to_deliver_count,

        "seller_late_orders":
            seller_late_orders,

        "seller_late_orders_count":
            seller_late_orders_count,

        "seller_earnings":
            seller_earnings,

        "seller_revenue":
            seller_revenue,

        "seller_notifications":
            seller_notifications,

        "seller_unread_notifications":
            seller_unread_notifications,

        "seller_is_premium":
            seller_is_premium,


        # -------------------------
        # FORMATEUR
        # -------------------------

        "trainer_profile":
            trainer_profile,

        "trainer_courses":
            trainer_courses,

        "trainer_wallet":
            trainer_wallet,

        "trainer_revenue":
            trainer_revenue,

        "trainer_notifications":
            trainer_notifications,

        "trainer_unread_notifications":
            trainer_unread_notifications,
    }

    return render(
        request,
        "accounts/dashboard.html",
        context
    )


# =========================================================
# DEVENIR FORMATEUR
# =========================================================

@login_required
def become_trainer(request):

    existing_application = (
        TrainerApplication.objects
        .filter(user=request.user)
        .first()
    )

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

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        expertise = request.POST.get(
            "expertise",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        if not all([
            full_name,
            phone,
            expertise,
            description
        ]):

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


# =========================================================
# DASHBOARD FORMATEUR
# =========================================================

@login_required
def trainer_dashboard(request):

    trainer_profile = (
        TrainerProfile.objects
        .filter(user=request.user)
        .first()
    )

    trainer_wallet = None
    notifications = []
    unread_notifications = 0
    earnings = []
    trainer_courses = []

    if trainer_profile:

        trainer_wallet, created = (
            TrainerWallet.objects.get_or_create(
                user=request.user
            )
        )

        notifications = (
            TrainerNotification.objects
            .filter(trainer=request.user)
            .order_by("-created_at")[:5]
        )

        unread_notifications = (
            TrainerNotification.objects
            .filter(
                trainer=request.user,
                is_read=False
            )
            .count()
        )

        earnings = (
            TrainerEarning.objects
            .filter(trainer=request.user)
            .order_by("-created_at")
        )

        trainer_courses = (
            request.user.courses
            .all()
            .order_by("-created_at")
        )

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


# =========================================================
# DEVENIR VENDEUR
# =========================================================

@login_required
def become_seller(request):

    existing_application = (
        SellerApplication.objects
        .filter(user=request.user)
        .first()
    )

    if existing_application:

        if existing_application.status == "pending":

            messages.info(
                request,
                "Votre candidature vendeur est déjà en attente."
            )

            return redirect("home")

        if existing_application.status == "approved":

            messages.info(
                request,
                "Vous êtes déjà vendeur."
            )

            return redirect("home")

        if existing_application.status == "rejected":

            messages.info(
                request,
                "Votre candidature vendeur a été refusée."
            )

            return redirect("home")

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        neighborhood = request.POST.get(
            "neighborhood",
            ""
        ).strip()

        city = request.POST.get(
            "city",
            ""
        ).strip()

        activity = request.POST.get(
            "activity",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        plan = request.POST.get(
            "plan",
            "standard"
        ).strip().lower()

        payment_method = request.POST.get(
            "payment_method",
            ""
        ).strip().lower()

        payment_phone = request.POST.get(
            "payment_phone",
            ""
        ).strip()

        if plan not in [
            "standard",
            "premium"
        ]:

            messages.error(
                request,
                "Veuillez choisir une formule vendeur valide."
            )

            return render(
                request,
                "accounts/become_seller.html"
            )

        if not all([
            full_name,
            phone,
            address,
            neighborhood,
            city,
            activity,
            description
        ]):

            messages.error(
                request,
                "Veuillez remplir tous les champs."
            )

            return render(
                request,
                "accounts/become_seller.html"
            )

        if plan == "premium":

            if payment_method not in [
                "mtn",
                "orange"
            ]:

                messages.error(
                    request,
                    "Veuillez choisir un moyen de paiement Premium valide."
                )

                return render(
                    request,
                    "accounts/become_seller.html"
                )

            if not payment_phone:

                messages.error(
                    request,
                    "Veuillez entrer le numéro utilisé pour le paiement Premium."
                )

                return render(
                    request,
                    "accounts/become_seller.html"
                )

        SellerApplication.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            neighborhood=neighborhood,
            city=city,
            activity=activity,
            description=description,
            plan=plan
        )

        if plan == "premium":

            SellerSubscription.objects.create(
                seller=request.user,
                amount=1000,
                method=payment_method,
                phone_number=payment_phone,
                status="pending"
            )

            messages.success(
                request,
                "Votre candidature vendeur Premium a été envoyée. "
                "Votre paiement de 1 000 FCFA doit maintenant être vérifié "
                "par l'administrateur."
            )

        else:

            messages.success(
                request,
                "Votre candidature vendeur Standard a été envoyée "
                "à l'administrateur."
            )

        return redirect("home")

    return render(
        request,
        "accounts/become_seller.html"
    )


# =========================================================
# PASSER VENDEUR PREMIUM
# =========================================================

@login_required
def upgrade_to_premium(request):

    seller_profile = (
        SellerProfile.objects
        .filter(user=request.user)
        .first()
    )

    if not seller_profile:

        messages.error(
            request,
            "Vous devez être vendeur avant de passer Premium."
        )

        return redirect("dashboard")

    if is_premium_seller(request.user):

        messages.info(
            request,
            "Votre compte est déjà Premium."
        )

        return redirect("dashboard")

    premium_mtn_number = settings.PREMIUM_MTN_NUMBER
    premium_orange_number = settings.PREMIUM_ORANGE_NUMBER

    if request.method == "POST":

        payment_method = request.POST.get(
            "payment_method",
            ""
        ).strip().lower()

        payment_phone = request.POST.get(
            "payment_phone",
            ""
        ).strip()

        if payment_method not in [
            "mtn",
            "orange"
        ]:

            messages.error(
                request,
                "Veuillez choisir MTN Mobile Money ou Orange Money."
            )

            return render(
                request,
                "accounts/upgrade_premium.html",
                {
                    "seller_profile": seller_profile,
                    "premium_mtn_number": premium_mtn_number,
                    "premium_orange_number": premium_orange_number,
                    "selected_method": payment_method,
                    "payment_phone": payment_phone,
                }
            )

        if not payment_phone:

            messages.error(
                request,
                "Veuillez saisir le numéro utilisé pour effectuer le paiement."
            )

            return render(
                request,
                "accounts/upgrade_premium.html",
                {
                    "seller_profile": seller_profile,
                    "premium_mtn_number": premium_mtn_number,
                    "premium_orange_number": premium_orange_number,
                    "selected_method": payment_method,
                    "payment_phone": payment_phone,
                }
            )

        existing_pending = (
            SellerSubscription.objects
            .filter(
                seller=request.user,
                status="pending"
            )
            .exists()
        )

        if existing_pending:

            messages.info(
                request,
                "Une demande Premium est déjà en attente de validation."
            )

            return redirect("dashboard")

        SellerSubscription.objects.create(
            seller=request.user,
            amount=1000,
            method=payment_method,
            phone_number=payment_phone,
            status="pending"
        )

        messages.success(
            request,
            "Votre demande Premium a été enregistrée. "
            "Elle sera activée après validation du paiement."
        )

        return redirect("dashboard")

    return render(
        request,
        "accounts/upgrade_premium.html",
        {
            "seller_profile": seller_profile,
            "premium_mtn_number": premium_mtn_number,
            "premium_orange_number": premium_orange_number,
        }
    )