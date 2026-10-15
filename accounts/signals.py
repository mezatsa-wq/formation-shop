import logging

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse, NoReverseMatch

from .models import (
    SellerNotification,
    TrainerNotification,
    TokenWallet,
    PushSubscription,
)
from .push_service import send_public_push, send_push_to_user

from orders.models import OrderNotification
from products.models import Product
from courses.models import Course
from documents.models import Document

logger = logging.getLogger(__name__)


# =========================================================
# PORTEFEUILLE INITIAL DE L'UTILISATEUR
# =========================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_token_wallet(sender, instance, created, **kwargs):
    if created:
        TokenWallet.objects.get_or_create(user=instance)


# =========================================================
# OUTILS
# =========================================================

def safe_url(name, args=None, fallback="/"):
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return fallback


def queue_private_notification(user, title, url="/"):
    """
    Envoie une notification push privée après validation
    de la transaction en base de données.
    """
    if not user:
        return

    transaction.on_commit(
        lambda: send_push_to_user(
            user=user,
            title=title,
            body=(
                "Ouvrez FormaShop pour consulter les détails "
                "de votre notification."
            ),
            url=url,
        )
    )


def queue_public_notification(title, body, url="/"):
    """
    Envoie une notification aux abonnements enregistrés.
    """
    transaction.on_commit(
        lambda: send_public_push(
            title=title,
            body=body,
            url=url,
        )
    )


# =========================================================
# NOTIFICATIONS PRIVÉES
# =========================================================

@receiver(post_save, sender=OrderNotification)
def order_notification_push(sender, instance, created, **kwargs):
    if created:
        queue_private_notification(
            instance.recipient,
            instance.title,
            "/",
        )


@receiver(post_save, sender=SellerNotification)
def seller_notification_push(sender, instance, created, **kwargs):
    if created:
        queue_private_notification(
            instance.user,
            instance.title,
            "/",
        )


@receiver(post_save, sender=TrainerNotification)
def trainer_notification_push(sender, instance, created, **kwargs):
    if created:
        queue_private_notification(
            instance.trainer,
            instance.title,
            "/",
        )


# =========================================================
# NOUVEAUX PRODUITS
# =========================================================

@receiver(post_save, sender=Product)
def new_product_push(sender, instance, created, **kwargs):
    if not created:
        return

    stock = getattr(instance, "stock", 0)

    if stock <= 0:
        return

    product_name = (
        getattr(instance, "name", None)
        or "Nouveau produit"
    )

    url = "/"

    queue_public_notification(
        title=f"Nouveau produit : {product_name}",
        body="Un nouveau produit est disponible sur FormaShop.",
        url=url,
    )


# =========================================================
# NOUVELLES FORMATIONS
# =========================================================

@receiver(post_save, sender=Course)
def new_course_push(sender, instance, created, **kwargs):
    if not created:
        return

    # Si le modèle possède is_published, respecter sa valeur.
    # Sinon, ne pas provoquer d'AttributeError.
    if not getattr(instance, "is_published", True):
        return

    course_title = (
        getattr(instance, "title", None)
        or getattr(instance, "name", None)
        or "Nouvelle formation"
    )

    slug = getattr(instance, "slug", None)

    url = "/"

    queue_public_notification(
        title=f"Nouvelle formation : {course_title}",
        body="Découvrez cette nouvelle formation sur FormaShop.",
        url=url,
    )


# =========================================================
# NOUVEAUX DOCUMENTS
# =========================================================

@receiver(post_save, sender=Document)
def new_document_push(sender, instance, created, **kwargs):
    if not created:
        return

    document_title = (
        getattr(instance, "title", None)
        or getattr(instance, "name", None)
        or "Nouveau document"
    )

    url = "/"

    queue_public_notification(
        title=f"Nouveau document : {document_title}",
        body="Un nouveau document est disponible sur FormaShop.",
        url=url,
    )