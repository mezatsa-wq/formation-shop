from django.db import models
from django.conf import settings


class CoursePayment(models.Model):

    METHOD_CHOICES = [
        ("mtn", "MTN Mobile Money"),
        ("orange", "Orange Money"),
    ]

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("seller_delivered", "Livrée par le vendeur"),
        ("customer_received", "Réception confirmée"),
        ("delivered", "Validée par l'administrateur"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE
    )

    phone_number = models.CharField(
        max_length=20
    )

    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user} - {self.course} - {self.amount} FCFA"


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("seller_delivered", "Livrée par le vendeur"),
        ("customer_received", "Réception confirmée"),
        ("delivered", "Livrée"),
        ("cancelled", "Annulée"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "En attente"),
        ("paid", "Payé"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_orders_received"
    )

    full_name = models.CharField(
        max_length=200
    )

    phone_number = models.CharField(
        max_length=30
    )

    neighborhood = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )

    delivery_address = models.TextField()

    delivery_deadline = models.DateTimeField(
        null=True,
        blank=True
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    seller_confirmed = models.BooleanField(
        default=False
    )

    customer_confirmed = models.BooleanField(
        default=False
    )

    admin_validated = models.BooleanField(
        default=False
    )

    seller_confirmed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    customer_confirmed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    admin_validated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    reward_given = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        if self.product:
            return f"Commande #{self.id} - {self.product.name}"

        return f"Commande #{self.id}"


class OrderNotification(models.Model):

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="order_notifications"
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"