from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone

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

            # Création du portefeuille de jetons
            wallet, created = TokenWallet.objects.get_or_create(
                user=user
            )

            # Attribution du bonus quotidien
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

            # Récupération ou création du portefeuille
            wallet, created = TokenWallet.objects.get_or_create(
                user=user
            )

            # Attribution du bonus quotidien
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


# =========================================================
# TABLEAU DE BORD PRINCIPAL
# =========================================================

@login_required
def dashboard(request):

    user = request.user

    # =====================================================
    # PORTEFEUILLE DE JETONS
    # =====================================================

    wallet, created = TokenWallet.objects.get_or_create(
        user=user
    )

    # =====================================================
    # ESPACE CLIENT
    # =====================================================

    my_orders = Order.objects.filter(
        user=user
    ).select_related(
        "product",
        "seller"
    ).order_by(
        "-created_at"
    )

    my_notifications = OrderNotification.objects.filter(
        recipient=user
    ).select_related(
        "order"
    ).order_by(
        "-created_at"
    )

    unread_order_notifications = my_notifications.filter(
        is_read=False
    ).count()

    # =====================================================
    # ESPACE VENDEUR
    # =====================================================

    seller_profile = SellerProfile.objects.filter(
        user=user
    ).first()

    seller_products = []
    seller_orders = []
    seller_earnings = []
    seller_notifications = []

    seller_unread_notifications = 0
    seller_revenue = 0
    seller_orders_to_deliver = 0
    seller_late_orders = 0

    seller_pending_orders = []
    seller_delivered_orders = []
    seller_completed_orders = []

    if seller_profile:

        # Produits du vendeur
        seller_products = Product.objects.filter(
            seller=user
        ).order_by(
            "-created_at"
        )

        # Commandes reçues
        seller_orders = Order.objects.filter(
            seller=user
        ).select_related(
            "product",
            "user"
        ).order_by(
            "-created_at"
        )

        # Revenus
        seller_earnings = SellerEarning.objects.filter(
            seller=user
        ).order_by(
            "-created_at"
        )

        seller_revenue = sum(
            earning.amount
            for earning in seller_earnings
        )

        # Commandes que le vendeur doit encore traiter
        seller_orders_to_deliver = seller_orders.filter(
            seller_confirmed=False,
            admin_validated=False
        ).count()

        # Commandes dont le délai est dépassé
        now = timezone.now()

        seller_late_orders = seller_orders.filter(
            seller_confirmed=False,
            admin_validated=False,
            delivery_deadline__lt=now
        ).count()

        # Notifications vendeur
        seller_notifications = OrderNotification.objects.filter(
            recipient=user
        ).select_related(
            "order"
        ).order_by(
            "-created_at"
        )[:5]

        # Nombre réel de notifications non lues
        seller_unread_notifications = OrderNotification.objects.filter(
            recipient=user,
            is_read=False
        ).count()

        # Commandes en attente de livraison
        seller_pending_orders = seller_orders.filter(
            seller_confirmed=False,
            admin_validated=False
        )

        # Commandes livrées par le vendeur
        # mais pas encore confirmées par le client
        seller_delivered_orders = seller_orders.filter(
            seller_confirmed=True,
            customer_confirmed=False,
            admin_validated=False
        )

        # Commandes totalement terminées
        seller_completed_orders = seller_orders.filter(
            admin_validated=True
        )

    # =====================================================
    # ESPACE FORMATEUR
    # =====================================================

    trainer_profile = TrainerProfile.objects.filter(
        user=user
    ).first()

    trainer_wallet = None
    trainer_courses = []
    trainer_earnings = []
    trainer_notifications = []

    trainer_unread_notifications = 0
    trainer_revenue = 0

    if trainer_profile:

        # Portefeuille du formateur
        trainer_wallet, created = TrainerWallet.objects.get_or_create(
            user=user
        )

        # Formations créées par le formateur
        trainer_courses = user.courses.all().order_by(
            "-created_at"
        )

        # Revenus du formateur
        trainer_earnings = TrainerEarning.objects.filter(
            trainer=user
        ).order_by(
            "-created_at"
        )

        trainer_revenue = sum(
            earning.amount
            for earning in trainer_earnings
        )

        # Dernières notifications
        trainer_notifications = TrainerNotification.objects.filter(
            trainer=user
        ).order_by(
            "-created_at"
        )[:5]

        # Nombre réel de notifications non lues
        trainer_unread_notifications = TrainerNotification.objects.filter(
            trainer=user,
            is_read=False
        ).count()

    # =====================================================
    # CONTEXTE DU DASHBOARD
    # =====================================================

    context = {

        # -------------------------------------------------
        # CLIENT
        # -------------------------------------------------

        "wallet": wallet,

        "my_orders": my_orders,

        "my_notifications": my_notifications,

        "unread_order_notifications": unread_order_notifications,

        # -------------------------------------------------
        # VENDEUR
        # -------------------------------------------------

        "seller_profile": seller_profile,

        "seller_products": seller_products,

        "seller_orders": seller_orders,

        "seller_earnings": seller_earnings,

        "seller_notifications": seller_notifications,

        "seller_revenue": seller_revenue,

        "seller_orders_to_deliver": seller_orders_to_deliver,

        "seller_late_orders": seller_late_orders,

        "seller_unread_notifications": seller_unread_notifications,

        "seller_pending_orders": seller_pending_orders,

        "seller_delivered_orders": seller_delivered_orders,

        "seller_completed_orders": seller_completed_orders,

        # -------------------------------------------------
        # FORMATEUR
        # -------------------------------------------------

        "trainer_profile": trainer_profile,

        "trainer_wallet": trainer_wallet,

        "trainer_courses": trainer_courses,

        "trainer_earnings": trainer_earnings,

        "trainer_notifications": trainer_notifications,

        "trainer_revenue": trainer_revenue,

        "trainer_unread_notifications": trainer_unread_notifications,
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

    existing_application = TrainerApplication.objects.filter(
        user=request.user
    ).first()

    # -----------------------------------------------------
    # CANDIDATURE EXISTANTE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # NOUVELLE CANDIDATURE
    # -----------------------------------------------------

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

        # Dernières notifications
        notifications = TrainerNotification.objects.filter(
            trainer=request.user
        ).order_by(
            "-created_at"
        )[:5]

        # Toutes les notifications non lues
        unread_notifications = TrainerNotification.objects.filter(
            trainer=request.user,
            is_read=False
        ).count()

        # Revenus
        earnings = TrainerEarning.objects.filter(
            trainer=request.user
        ).order_by(
            "-created_at"
        )

        # Formations
        trainer_courses = request.user.courses.all().order_by(
            "-created_at"
        )

    # Portefeuille de jetons client
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

    existing_application = SellerApplication.objects.filter(
        user=request.user
    ).first()

    # -----------------------------------------------------
    # CANDIDATURE EXISTANTE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # NOUVELLE CANDIDATURE
    # -----------------------------------------------------

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

        # -------------------------------------------------
        # VÉRIFICATION DU PLAN
        # -------------------------------------------------

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

        # -------------------------------------------------
        # VÉRIFICATION DES INFORMATIONS
        # -------------------------------------------------

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

        # -------------------------------------------------
        # VÉRIFICATION PREMIUM
        # -------------------------------------------------

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

        # -------------------------------------------------
        # CRÉATION DE LA CANDIDATURE
        # -------------------------------------------------

        application = SellerApplication.objects.create(
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

        # -------------------------------------------------
        # DEMANDE DE SOUSCRIPTION PREMIUM
        # -------------------------------------------------

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