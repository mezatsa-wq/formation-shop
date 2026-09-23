from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import TokenWallet, TokenTransaction

from .models import Document, DocumentPurchase


def document_list(request):

    documents = Document.objects.all().order_by("-created_at")

    return render(
        request,
        "documents/list.html",
        {
            "documents": documents,
        }
    )


def document_detail(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id
    )

    already_owned = False

    if request.user.is_authenticated:

        already_owned = DocumentPurchase.objects.filter(
            user=request.user,
            document=document
        ).exists()

    return render(
        request,
        "documents/detail.html",
        {
            "document": document,
            "already_owned": already_owned,
        }
    )


@login_required
def buy_document(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id
    )

    already_owned = DocumentPurchase.objects.filter(
        user=request.user,
        document=document
    ).exists()

    if already_owned:

        messages.info(
            request,
            "Vous possédez déjà ce document."
        )

        return redirect(
            "document_detail",
            document_id=document.id
        )

    wallet, created = TokenWallet.objects.get_or_create(
        user=request.user
    )

    if wallet.balance < document.token_price:

        messages.error(
            request,
            "Vous n'avez pas assez de jetons."
        )

        return redirect(
            "document_detail",
            document_id=document.id
        )

    wallet.balance -= document.token_price
    wallet.save()

    DocumentPurchase.objects.create(
        user=request.user,
        document=document,
        tokens_spent=document.token_price
    )

    TokenTransaction.objects.create(
        wallet=wallet,
        amount=-document.token_price,
        transaction_type="document",
        description=f"Achat du document : {document.title}"
    )

    messages.success(
        request,
        "Document acheté avec succès."
    )

    return redirect(
        "document_detail",
        document_id=document.id
    )


@login_required
def download_document(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id
    )

    # Vérifier que l'utilisateur possède réellement le document
    purchase = DocumentPurchase.objects.filter(
        user=request.user,
        document=document
    ).first()

    if not purchase:

        messages.error(
            request,
            "Vous devez acheter ce document avant de pouvoir le télécharger."
        )

        return redirect(
            "document_detail",
            document_id=document.id
        )

    # Vérifier que le fichier existe
    if not document.file:

        raise Http404(
            "Le fichier de ce document est introuvable."
        )

    # Envoyer le fichier au navigateur
    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.file.name.split("/")[-1]
    )