# gestion_depot/views/produit_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Func, Sum, Case, When, F, DecimalField
from gestion_depot.models import Produit
from gestion_depot.decorators import group_required
from gestion_depot.forms import ProduitForm


class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'


@group_required('Caissier', 'Gérant', 'Admin')
def liste_produits_avec_stock(request):
    produits = Produit.objects.annotate(
        stock_actuel=Round(
            Sum(
                Case(
                    When(mouvement__type_mouvement='entree', then=F('mouvement__quantite_casiers')),
                    When(mouvement__type_mouvement='sortie', then=-F('mouvement__quantite_casiers')),
                    default=0,
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
        )
    ).prefetch_related('mouvement_set')

    return render(request, 'gestion_depot/produit_liste.html', {'produits': produits})


@group_required('Gérant', 'Admin')
def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            produit = form.save()
            messages.success(request, f"Produit '{produit.nom}' ajouté avec succès.")
            return redirect('gestion_depot:liste_produits')
    else:
        form = ProduitForm()

    return render(request, 'gestion_depot/produit_form.html', {
        'form': form,
        'action': 'Ajouter',
        'categories': Produit.CATEGORIE_CHOICES,
        'casiers': [c for c, _ in Produit.CASIER_CHOICES],
    })


@group_required('Gérant', 'Admin')
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Produit '{produit.nom}' mis à jour.")
            return redirect('gestion_depot:liste_produits')
    else:
        form = ProduitForm(instance=produit)

    return render(request, 'gestion_depot/produit_form.html', {
        'form': form,
        'action': 'Modifier',
        'produit': produit,
        'categories': Produit.CATEGORIE_CHOICES,
        'casiers': [c for c, _ in Produit.CASIER_CHOICES],
    })


@group_required('Gérant', 'Admin')
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    nom = produit.nom
    produit.delete()
    messages.success(request, f"Produit '{nom}' supprimé.")
    return redirect('gestion_depot:liste_produits')
