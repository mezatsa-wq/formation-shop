from django.db import models
from django.conf import settings


class CoursePayment(models.Model):
    METHOD_CHOICES = [
        ("mtn", "MTN Mobile Money"),
        ("orange", "Orange Money"),
    ]

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("confirmed", "Confirmé"),
        ("rejected", "Refusé"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE
    )

    phone_number = models.CharField(max_length=20)

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

    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.user} - {self.course} - {self.amount} FCFA"


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("delivered", "Livrée"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "En attente"),
        ("paid", "Payé"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(
        max_length=200
    )

    phone_number = models.CharField(
        max_length=30
    )

    delivery_address = models.TextField()

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

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

    reward_given = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        if self.product:
            return f"Commande #{self.id} - {self.product.name}"

        return f"Commande #{self.id}"