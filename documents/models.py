from django.conf import settings

from django.db import models

class Document(models.Model):

    title = models.CharField(

        max_length=200

    )

    description = models.TextField(

        blank=True

    )

    file = models.FileField(

        upload_to="documents/"

    )

    token_price = models.PositiveIntegerField(

        default=20

    )

    trainer = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.CASCADE,

        related_name="documents_created",

        null=True,

        blank=True

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def _str_(self):

        return self.title

class DocumentPurchase(models.Model):

    user = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.CASCADE

    )

    document = models.ForeignKey(

        Document,

        on_delete=models.CASCADE

    )

    tokens_spent = models.PositiveIntegerField()

    purchased_at = models.DateTimeField(

        auto_now_add=True

    )

    class Meta:

        unique_together = (

            "user",

            "document",

        )

    def _str_(self):

        return f"{self.user.username} - {self.document.title}"