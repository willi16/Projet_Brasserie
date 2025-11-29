# gestion_depot/views/produit_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from gestion_depot.models import Produit
from gestion_depot.decorators import group_required

from django.db.models import Sum, Case, When, F, Func, DecimalField


class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'


@group_required('Gérant', 'Admin')



def liste_produits_avec_stock(request):
    produits = Produit.objects.annotate(
        stock_actuel=Round(
            Sum(
                Case(
                    When(mouvement__type_mouvement='entree', then=F('mouvement__quantite_casiers')),
                    When(mouvement__type_mouvement='sortie', then=-F('mouvement__quantite_casiers')),
                    default=0,
                    output_field=DecimalField(max_digits=10, decimal_places=2)  # ← AJOUTE CETTE LIGNE
            
                )
            )
        )
    ).prefetch_related('mouvement_set')

   
    return render(request, 'gestion_depot/produit_liste.html', {'produits': produits})

@group_required('Gérant', 'Admin')
def ajouter_produit(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        categorie = request.POST.get('categorie')
        casier_contenu = int(request.POST.get('casier_contenu'))
        prix_achat = int(request.POST.get('prix_achat_casier'))
        prix_vente = int(request.POST.get('prix_vente_casier'))
        seuil_alerte = int(request.POST.get('seuil_alerte'))

        produit = Produit.objects.create(
            nom=nom,
            categorie=categorie,
            casier_contenu=casier_contenu,
            prix_achat_casier=prix_achat,
            prix_vente_casier=prix_vente,
            seuil_alerte=seuil_alerte
        )
        messages.success(request, f"✅ Produit '{produit.nom}' ajouté avec succès.")
        return redirect('gestion_depot:liste_produits')

    return render(request, 'gestion_depot/produit_form.html', {
        'action': 'Ajouter',
        'categories': Produit.CATEGORIE_CHOICES,
        'casiers': [6, 12, 20, 24]
    })

@group_required('Gérant', 'Admin')
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == 'POST':
        produit.nom = request.POST.get('nom')
        produit.categorie = request.POST.get('categorie')
        produit.casier_contenu = int(request.POST.get('casier_contenu'))
        produit.prix_achat_casier = int(request.POST.get('prix_achat_casier'))
        produit.prix_vente_casier = int(request.POST.get('prix_vente_casier'))
        produit.seuil_alerte = int(request.POST.get('seuil_alerte'))
        produit.save()

        messages.success(request, f"✅ Produit '{produit.nom}' mis à jour.")
        return redirect('gestion_depot:liste_produits')

    return render(request, 'gestion_depot/produit_form.html', {
        'action': 'Modifier',
        'produit': produit,
        'categories': Produit.CATEGORIE_CHOICES,
        'casiers': [6, 12, 20, 24]
    })

@group_required('Gérant', 'Admin')
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    nom = produit.nom
    produit.delete()
    messages.success(request, f"🗑️ Produit '{nom}' supprimé.")
    return redirect('gestion_depot:liste_produits')