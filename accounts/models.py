from django.conf import settings
from django.db import models
from django.utils import timezone


class TokenWallet(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="token_wallet"
    )

    balance = models.PositiveIntegerField(
        default=20
    )

    last_daily_reward = models.DateField(
        null=True,
        blank=True
    )

    def give_daily_reward(self):

        today = timezone.localdate()

        if self.last_daily_reward != today:

            self.balance += 20

            self.last_daily_reward = today

            self.save(
                update_fields=[
                    "balance",
                    "last_daily_reward"
                ]
            )

            TokenTransaction.objects.create(
                wallet=self,
                amount=20,
                transaction_type="daily",
                description="Bonus quotidien de 20 jetons"
            )

            return True

        return False

    def __str__(self):
        return f"{self.user.username} - {self.balance} jetons"


class TokenTransaction(models.Model):

    TYPE_CHOICES = [
        ("daily", "Bonus quotidien"),
        ("product", "Récompense produit"),
        ("document", "Achat document"),
    ]

    wallet = models.ForeignKey(
        TokenWallet,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    amount = models.IntegerField()

    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    description = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.description
class TrainerApplication(models.Model):

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("approved", "Acceptée"),
        ("rejected", "Refusée"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_application"
    )

    full_name = models.CharField(
        max_length=200
    )

    phone = models.CharField(
        max_length=30
    )

    expertise = models.CharField(
        max_length=255
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def _str_(self):
        return f"{self.user.username} - {self.status}"


class TrainerProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_profile"
    )

    bio = models.TextField(
        blank=True
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    expertise = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def _str_(self):
        return f"Formateur : {self.user.username}"
class TrainerWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_wallet"
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f"Portefeuille de {self.user.username} : {self.balance} FCFA"


class TrainerEarning(models.Model):
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_earnings"
    )
    payment = models.OneToOneField(
        "orders.CoursePayment",
        on_delete=models.CASCADE,
        related_name="trainer_earning"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    description = models.CharField(
        max_length=255,
        default="Gain provenant d'une formation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.trainer.username} - {self.amount} FCFA"


class TrainerNotification(models.Model):
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.trainer.username} - {self.title}"


class WithdrawalRequest(models.Model):
    METHOD_CHOICES = [
        ("mtn", "MTN Mobile Money"),
        ("orange", "Orange Money"),
    ]

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("paid", "Payé"),
        ("rejected", "Refusé"),
    ]

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawal_requests"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES
    )
    phone_number = models.CharField(max_length=30)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def _str_(self):
        return (
            f"Retrait #{self.id} - "
            f"{self.trainer.username} - "
            f"{self.amount} FCFA"
        )

class SellerApplication(models.Model):
    PLAN_CHOICES = [
        ("standard", "Vendeur Standard"),
        ("premium", "Vendeur Premium"),
    ]
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default="standard"
    )
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("approved", "Acceptée"),
        ("rejected", "Refusée"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_application"
    )

    full_name = models.CharField(
        max_length=200
    )

    phone = models.CharField(
        max_length=30
    )

    address = models.TextField()

    neighborhood = models.CharField(
        max_length=200
    )

    city = models.CharField(
        max_length=100
    )

    activity = models.CharField(
        max_length=255
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.status}"


class SellerProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_profile"
    )

    full_name = models.CharField(
        max_length=200
    )

    phone = models.CharField(
        max_length=30
    )

    address = models.TextField()

    neighborhood = models.CharField(
        max_length=200
    )

    city = models.CharField(
        max_length=100
    )

    activity = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True
    )

    plan = models.CharField(
        max_length=20,
        choices=SellerApplication.PLAN_CHOICES,
        default="standard"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Vendeur : {self.user.username}"
class SellerSubscription(models.Model):

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("active", "Active"),
        ("expired", "Expirée"),
        ("rejected", "Refusée"),
    ]

    METHOD_CHOICES = [
        ("mtn", "MTN Mobile Money"),
        ("orange", "Orange Money"),
    ]

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_subscriptions"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000
    )

    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES
    )

    phone_number = models.CharField(
        max_length=30
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    end_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"Premium - {self.seller.username} - "
            f"{self.amount} FCFA - {self.status}"
        )



def is_premium_seller(user):
    """
    Vérifie si un vendeur possède actuellement
    un abonnement Premium actif.
    """

    if not hasattr(user, "seller_profile"):
        return False

    subscription = user.seller_subscriptions.filter(
        status="active"
    ).order_by("-end_date").first()

    if not subscription:
        return False

    today = timezone.localdate()

    if subscription.end_date and subscription.end_date < today:

        subscription.status = "expired"

        subscription.save(
            update_fields=["status"]
        )

        profile = user.seller_profile
        profile.plan = "standard"

        profile.save(
            update_fields=["plan"]
        )

        return False

    return True

def get_seller_plan(user):
        """
        Retourne le niveau actuel du vendeur.
        """

        if not hasattr(user, "seller_profile"):
            return None

        if is_premium_seller(user):
            return "premium"

        return "standard"

def update_expired_seller_subscription(user):
        """
        Passe automatiquement un abonnement Premium expiré
        à l'état expired.
        """

        today = timezone.localdate()

        subscriptions = user.seller_subscriptions.filter(
            status="active"
        )

        for subscription in subscriptions:

            if subscription.end_date and subscription.end_date < today:
                subscription.status = "expired"
                subscription.save(
                    update_fields=["status"]
                )
class SellerEarning(models.Model):

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_earnings"
    )

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="seller_earning"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    description = models.CharField(
        max_length=255,
        default="Vente de produit"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.seller.username} - "
            f"{self.amount} FCFA"
        )