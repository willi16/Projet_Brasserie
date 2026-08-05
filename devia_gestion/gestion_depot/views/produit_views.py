# gestion_depot/views/produit_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Func, Sum, Case, When, F, DecimalField
from django.forms import modelformset_factory
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
def produits_multi_create(request, nb_forms):
    """Enregistre plusieurs produits à la fois (ajout multiple)."""
    if nb_forms < 2 or nb_forms > 20:
        messages.error(request, "Le nombre de produits doit être compris entre 2 et 20.")
        return redirect('gestion_depot:liste_produits')

    ProduitFormSet = modelformset_factory(
        Produit,
        form=ProduitForm,
        extra=nb_forms,
        min_num=nb_forms,
        max_num=nb_forms,
        validate_min=True,
        validate_max=True,
        can_delete=False,
    )

    if request.method == 'POST':
        formset = ProduitFormSet(request.POST, queryset=Produit.objects.none())
        if formset.is_valid():
            produits = formset.save(commit=False)
            for produit in produits:
                produit.save()
            messages.success(request, f"{len(produits)} produit(s) ajouté(s) avec succès.")
            return redirect('gestion_depot:liste_produits')
    else:
        formset = ProduitFormSet(queryset=Produit.objects.none())

    return render(request, 'gestion_depot/produits_multi_create.html', {
        'formset': formset,
        'nb_forms': nb_forms,
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
