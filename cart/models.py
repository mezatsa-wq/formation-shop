from django.db import models
from django.contrib.auth.models import User


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def _str_(self):
        return f"Panier de {self.user.username}"

class CartItem(models.Model):
        cart = models.ForeignKey(
            Cart,
            on_delete=models.CASCADE,
            related_name="items"
        )

        product = models.ForeignKey(
            "products.Product",
            on_delete=models.CASCADE,
            null=True,
            blank=True
        )

        course = models.ForeignKey(
            "courses.Course",
            on_delete=models.CASCADE,
            null=True,
            blank=True
        )

        quantity = models.PositiveIntegerField(
            default=1
        )

        def _str_(self):
            return f"Article du panier #{self.cart.id}"