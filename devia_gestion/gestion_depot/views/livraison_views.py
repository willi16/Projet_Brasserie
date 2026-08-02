from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from gestion_depot.models import Produit, Fournisseur, Mouvement
from gestion_depot.models.bon_livraison import BonLivraison
from gestion_depot.models.ligne_livraison import LigneLivraison
from gestion_depot.decorators import group_required


@group_required('Gérant', 'Admin')
@transaction.atomic
def creer_bon_livraison(request):
    if request.method == 'POST':
        fournisseur_id = request.POST.get('fournisseur')
        produits = request.POST.getlist('produit')
        casiers = request.POST.getlist('casier_contenu')
        prix_achats = request.POST.getlist('prix_achat_casier')
        quantites = request.POST.getlist('quantite')

        if not produits:
            messages.error(request, "Veuillez ajouter au moins une ligne.")
            return redirect('gestion_depot:creer_bon_livraison')

        try:
            fournisseur_obj = Fournisseur.objects.get(id=fournisseur_id)
        except Fournisseur.DoesNotExist:
            messages.error(request, "Fournisseur introuvable.")
            return redirect('gestion_depot:creer_bon_livraison')

        produit_ids = [int(p) for p in produits]
        produits_dict = Produit.objects.in_bulk(produit_ids)

        # Préparer toutes les lignes avant toute écriture en base
        lignes_a_creer = []
        mouvements_a_creer = []
        for p, c, pa, q in zip(produits, casiers, prix_achats, quantites):
            prod = produits_dict.get(int(p))
            if not prod:
                messages.error(request, "Produit introuvable.")
                return redirect('gestion_depot:creer_bon_livraison')
            try:
                quantite = Decimal(q)
                prix_achat = Decimal(pa)
                casier_contenu = int(c)
            except (ValueError, TypeError, InvalidOperation):
                messages.error(request, f"Données invalides pour {prod.nom}.")
                return redirect('gestion_depot:creer_bon_livraison')

            if quantite <= 0 or prix_achat < 0:
                messages.error(request, f"Quantité ou prix invalide pour {prod.nom}.")
                return redirect('gestion_depot:creer_bon_livraison')

            lignes_a_creer.append((prod, quantite, casier_contenu, prix_achat))

        bon = BonLivraison.objects.create(
            fournisseur=fournisseur_obj,
            utilisateur=request.user,
        )

        for prod, quantite, casier_contenu, prix_achat in lignes_a_creer:
            ligne = LigneLivraison.objects.create(
                bon=bon,
                produit=prod,
                quantite_casiers=quantite,
                casier_contenu=casier_contenu,
                prix_achat_casier=prix_achat,
            )
            # Créer un mouvement d'entrée
            Mouvement.objects.create(
                produit=prod,
                type_mouvement='entree',
                quantite_casiers=quantite,
                fournisseur=fournisseur_obj,
                utilisateur=request.user,
            )

        messages.success(request, f"Livraison {bon.reference} enregistrée avec succès !")
        return redirect('gestion_depot:liste_livraisons')

    produits = Produit.objects.all()
    fournisseurs = Fournisseur.objects.all()
    return render(request, 'gestion_depot/creer_bon_livraison.html', {
        'produits': produits,
        'fournisseurs': fournisseurs
    })


@group_required('Gérant', 'Admin')
def liste_livraisons(request):
    livraisons = BonLivraison.objects.select_related('fournisseur', 'utilisateur').order_by('-date_livraison')
    return render(request, 'gestion_depot/livraison_liste.html', {'livraisons': livraisons})


@group_required('Gérant', 'Admin')
def detail_bon_livraison(request, id):
    bon = get_object_or_404(BonLivraison, id=id)
    return render(request, 'gestion_depot/detail_bon_livraison.html', {'bon': bon})
