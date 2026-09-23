from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "price",
        "stock",
        "reward_tokens",
        "created_at",
    )

    search_fields = (
        "name",
    )