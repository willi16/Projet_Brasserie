from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import produit, fournisseur, mouvement
from ..models.bon_livraison import BonLivraison
from ..models.ligne_livraison import LigneLivraison
from ..decorators import group_required
from django.contrib.auth.models import User

@group_required('Gérant', 'Admin')
@login_required
def creer_bon_livraison(request):
    if request.method == 'POST':
        fournisseur_id = request.POST.get('fournisseur')
        produits = request.POST.getlist('produit')
        casiers = request.POST.getlist('casier_contenu')
        prix_achats = request.POST.getlist('prix_achat_casier')
        quantites = request.POST.getlist('quantite')

        fournisseur_obj = get_object_or_404(fournisseur.Fournisseur, id=fournisseur_id)

        # Création du bon de livraison
        bon = BonLivraison.objects.create(
            fournisseur=fournisseur_obj,
            utilisateur=request.user,
        )

        # Optimisation : récupérer tous les produits en une seule requête
        produit_ids = [int(p) for p in produits]
        produits_dict = produit.Produit.objects.in_bulk(produit_ids)

        for p, c, pa, q in zip(produits, casiers, prix_achats, quantites):
            prod = produits_dict.get(int(p))
            if prod:
                ligne = LigneLivraison.objects.create(
                    bon=bon,
                    produit=prod,
                    quantite_casiers=float(q),
                    casier_contenu=int(c),
                    prix_achat_casier=float(pa),
                )
                # Créer un mouvement d'entrée
                mouvement.Mouvement.objects.create(
                    produit=prod,
                    type_mouvement='entree',
                    quantite_casiers=float(q),
                    fournisseur=fournisseur_obj,
                    utilisateur=request.user,
                )

        messages.success(request, f"Livraison {bon.reference} enregistrée avec succès !")
        return redirect('gestion_depot:liste_livraisons')

    produits = produit.Produit.objects.all()
    fournisseurs = fournisseur.Fournisseur.objects.all()
    return render(request, 'gestion_depot/creer_bon_livraison.html', {
        'produits': produits,
        'fournisseurs': fournisseurs
    })

@group_required('Gérant', 'Admin')
@login_required
def liste_livraisons(request):
    livraisons = BonLivraison.objects.all().order_by('-date_livraison')
    return render(request, 'gestion_depot/livraison_liste.html', {'livraisons': livraisons})

@group_required('Gérant', 'Admin')
@login_required
def detail_bon_livraison(request, id):
    bon = get_object_or_404(BonLivraison, id=id)
    return render(request, 'gestion_depot/detail_bon_livraison.html', {'bon': bon})