import json
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from gestion_depot.models import Produit, Fournisseur, Mouvement
from gestion_depot.models.bon_livraison import BonLivraison
from gestion_depot.models.ligne_livraison import LigneLivraison
from gestion_depot.models.userActionLog import UserActionLog
from gestion_depot.decorators import group_required
from gestion_depot.models.produit import CATEGORIES_AVEC_CASIERS, BOUTEILLES_PAR_MODELE


@group_required('Gérant', 'Admin')
def creer_bon_livraison(request):
    if request.method == 'POST':
        fournisseur_id = request.POST.get('fournisseur')
        produits = request.POST.getlist('produit')
        modeles = request.POST.getlist('modele')
        prix_achats = request.POST.getlist('prix_achat_casier')
        quantites = request.POST.getlist('quantite')

        if not produits:
            messages.error(request, "Veuillez ajouter au moins une ligne.")
            return redirect('gestion_depot:creer_bon_livraison')

        try:
            fournisseur_id_int = int(fournisseur_id)
        except (TypeError, ValueError):
            messages.error(request, "Fournisseur invalide.")
            return redirect('gestion_depot:creer_bon_livraison')

        try:
            fournisseur_obj = Fournisseur.objects.get(id=fournisseur_id_int)
        except Fournisseur.DoesNotExist:
            messages.error(request, "Fournisseur introuvable.")
            return redirect('gestion_depot:creer_bon_livraison')

        try:
            produit_ids = [int(p) for p in produits]
        except (ValueError, TypeError):
            messages.error(request, "Identifiant de produit invalide.")
            return redirect('gestion_depot:creer_bon_livraison')
        produits_dict = Produit.objects.in_bulk(produit_ids)

        # Vérifier que les listes ont la même longueur (pas de troncature silencieuse)
        longueurs = {len(produits), len(modeles), len(prix_achats), len(quantites)}
        if len(longueurs) != 1:
            messages.error(request, "Données du formulaire incomplètes.")
            return redirect('gestion_depot:creer_bon_livraison')

        # Préparer toutes les lignes avant toute écriture en base
        lignes_a_creer = []
        for p, m, pa, q in zip(produits, modeles, prix_achats, quantites):
            try:
                prod = produits_dict.get(int(p))
            except (ValueError, TypeError):
                messages.error(request, "Produit invalide.")
                return redirect('gestion_depot:creer_bon_livraison')
            if not prod:
                messages.error(request, "Produit introuvable.")
                return redirect('gestion_depot:creer_bon_livraison')
            try:
                quantite = Decimal(q)
                prix_achat = Decimal(pa)
            except (ValueError, TypeError, InvalidOperation):
                messages.error(request, f"Données invalides pour {prod.nom}.")
                return redirect('gestion_depot:creer_bon_livraison')

            if quantite <= 0 or quantite > Decimal('999.99'):
                messages.error(request, f"Quantité invalide pour {prod.nom} (1 à 999,99 casiers).")
                return redirect('gestion_depot:creer_bon_livraison')

            if prix_achat < 0 or prix_achat > Decimal('99999999.99'):
                messages.error(request, f"Prix d'achat invalide pour {prod.nom}.")
                return redirect('gestion_depot:creer_bon_livraison')

            # Modèle de casier attendu : petit modèle (< 50cl) → 24 bouteilles ;
            # grand modèle (>= 50cl) → casier du produit (12 ou 20 bouteilles).
            # Les produits non suivis (eau, boisson, canette) gardent le contenu
            # de casier défini sur le produit (emballage / pas de casier).
            if prod.categorie in CATEGORIES_AVEC_CASIERS:
                modele_attendu = prod.modele_livraison()
                casier_contenu = BOUTEILLES_PAR_MODELE.get(modele_attendu, prod.casier_contenu)
            else:
                casier_contenu = prod.casier_contenu

            lignes_a_creer.append((prod, quantite, casier_contenu, prix_achat))

        with transaction.atomic():
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
                # Mettre à jour les prix du produit : achat = prix renseigné, vente = achat × (1 + %)
                pourcentage = prod.pourcentage_prix_vente or Decimal('0')
                prod.prix_achat_casier = prix_achat
                prod.prix_vente_casier = (prix_achat * (Decimal('1') + pourcentage / Decimal('100'))).quantize(Decimal('0.01'))
                prod.save(update_fields=['prix_achat_casier', 'prix_vente_casier'])

            UserActionLog.log_action(
                request.user, 'création_livraison', module='livraisons',
                details=f"Enregistrement de la livraison {bon.reference} "
                        f"(fournisseur : {fournisseur_obj.nom}, {len(lignes_a_creer)} ligne(s))",
                request=request,
            )
        messages.success(request, f"Livraison {bon.reference} enregistrée avec succès !")
        return redirect('gestion_depot:liste_livraisons')

    produits_list = []
    for p in Produit.objects.all():
        categorie_casiers = p.categorie in CATEGORIES_AVEC_CASIERS
        modele_livraison = p.modele_livraison() if categorie_casiers else ''
        produits_list.append({
            'id': p.id,
            'nom': p.nom,
            'prix_achat': f"{float(p.prix_achat_casier):.2f}",
            'casier': p.casier_contenu,
            'tracked': 1 if categorie_casiers else 0,
            'modeles_json': json.dumps([modele_livraison]) if categorie_casiers else '[]',
            'modele_defaut': modele_livraison,
            'libelle': p.libelle_modele,
        })
    fournisseurs = Fournisseur.objects.all()
    return render(request, 'gestion_depot/creer_bon_livraison.html', {
        'produits_list': produits_list,
        'fournisseurs': fournisseurs
    })


@group_required('Gérant', 'Admin')
def liste_livraisons(request):
    livraisons = BonLivraison.objects.select_related('fournisseur', 'utilisateur').order_by('-date_livraison')
    return render(request, 'gestion_depot/livraison_liste.html', {'livraisons': livraisons})


@group_required('Gérant', 'Admin')
def detail_bon_livraison(request, id):
    bon = get_object_or_404(
        BonLivraison.objects.select_related('fournisseur', 'utilisateur')
        .prefetch_related('lignes__produit'),
        id=id,
    )
    return render(request, 'gestion_depot/detail_bon_livraison.html', {'bon': bon})
