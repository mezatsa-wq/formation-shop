
from django.http import HttpResponse

from django.shortcuts import render

# Create your views here.
def home_page(request):
    nombre_produit=0
    nom_produit="orange"
    content={
        'nombre_produit':nombre_produit,
        'nom_produit':nom_produit
    }

    return render(request,'index.html',content)
def about(request):
    return render(request,'about.html')
