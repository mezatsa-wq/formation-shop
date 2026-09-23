from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "token_price",
        "created_at",
    )

    search_fields = (
        "title",
    )