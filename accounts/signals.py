import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse, NoReverseMatch

from .models import SellerNotification, TrainerNotification
from .push_service import send_public_push, send_user_push

from orders.models import OrderNotification
from products.models import Product
from courses.models import Course
from documents.models import Document

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TokenWallet



@receiver(
    post_save,
    sender=settings.AUTH_USER_MODEL
)
def create_token_wallet(
    sender,
    instance,
    created,
    **kwargs
):

    if created:
        TokenWallet.objects.create(
            user=instance
        )
logger = logging.getLogger(__name__)


def safe_url(name, args=None, fallback="/"):
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return fallback


def queue_private_notification(user, title, url="/accounts/"):
    # Ne transmet pas le texte potentiellement sensible de la notification
    # interne vers l'écran verrouillé du téléphone.
    transaction.on_commit(
        lambda: send_user_push(
            user,
            title,
            "Ouvrez FormaShop pour consulter les détails de votre notification.",
            url,
        )
    )


@receiver(post_save, sender=OrderNotification)
def order_notification_push(sender, instance, created, **kwargs):
    if created:
        queue_private_notification(
            instance.recipient,
            instance.title,
            "/orders/",
        )


@receiver(post_save, sender=SellerNotification)
def seller_notification_push(sender, instance, created, **kwargs):
    if created:
        queue_private_notification(
            instance.user,
            instance.title,
            "/accounts/",
        )


@receiver(post_save, sender=TrainerNotification)
def trainer_notification_push(sender, instance, created, **kwargs):
    if created:
        queue_private_notification(
            instance.trainer,
            instance.title,
            "/accounts/",
        )


@receiver(post_save, sender=Product)
def new_product_push(sender, instance, created, **kwargs):
    if not created or instance.stock <= 0:
        return

    url = safe_url(
        "product_detail",
        args=[instance.pk],
        fallback=f"/products/{instance.pk}/",
    )

    transaction.on_commit(
        lambda: send_public_push(
            f"Nouveau produit : {instance.name}",
            "Un nouveau produit est disponible sur FormaShop.",
            url,
        )
    )


@receiver(post_save, sender=Course)
def new_course_push(sender, instance, created, **kwargs):
    if not created or not instance.is_published:
        return

    url = safe_url(
        "course_detail",
        args=[instance.slug],
        fallback=f"/courses/{instance.slug}/",
    )

    transaction.on_commit(
        lambda: send_public_push(
            f"Nouvelle formation : {instance.title}",
            "Découvrez cette nouvelle formation sur FormaShop.",
            url,
        )
    )


@receiver(post_save, sender=Document)
def new_document_push(sender, instance, created, **kwargs):
    if not created:
        return

    url = safe_url(
        "document_detail",
        args=[instance.pk],
        fallback=f"/documents/{instance.pk}/",
    )

    transaction.on_commit(
        lambda: send_public_push(
            f"Nouveau document : {instance.title}",
            "Un nouveau document est disponible sur FormaShop.",
            url,
        )
    )