from django.db import models
from django.conf import settings


class Product(models.Model):

    name = models.CharField(
        max_length=200
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products_created"
    )

    description = models.TextField(
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    reward_tokens = models.PositiveIntegerField(
        default=20
    )

    is_featured = models.BooleanField(
        default=False
    )

    boost_until = models.DateTimeField(
        null=True,
        blank=True
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name