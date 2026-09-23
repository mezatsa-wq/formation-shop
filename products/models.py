from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(default=0)

    reward_tokens = models.PositiveIntegerField(default=20)

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.name