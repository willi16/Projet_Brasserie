from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from gestion_depot.models import bon_vente,client, ligne_vente
from gestion_depot.models import produit, mouvement
from django.contrib.auth.models import User
from datetime import datetime

@login_required
def creer_bon_vente(request):
    if request.method == 'POST':
        client_nom = request.POST.get('client_nom')
        type_paiement = request.POST.get('type_paiement')
        vendeur = request.user
        
        # Récupère ou crée le client
        client_obj, created = client.Client.objects.get_or_create(nom=client_nom)



        # Récupération des lignes dynamiques (produit, fraction, quantité)
        produits = request.POST.getlist('produit')
        fractions = request.POST.getlist('fraction')
        quantites = request.POST.getlist('quantite')
        
        # Optimisation : récupérer tous les produits en une seule requête
        produit_ids = [int(p) for p in produits]
        produits_dict = produit.Produit.objects.in_bulk(produit_ids)
        
        # Vérification du stock avant création
        for p, f, q in zip(produits, fractions, quantites):
            prod = produits_dict.get(int(p))
            if prod and prod.stock_disponible() < (float(f) * float(q)):
                messages.error(request, f"Stock insuffisant pour {prod.nom}")
                return redirect('creer_bon_vente')

        # Création du bon de vente
        bon = bon_vente.BonVente.objects.create(
            client=client_obj,
            type_paiement=type_paiement,
            vendeur=vendeur,
        )

        # Création des lignes de vente
        for p, f, q in zip(produits, fractions, quantites):
            prod = produits_dict.get(int(p))
            if prod:
                ligne_vente.LigneVente.objects.create(
                    bon=bon,
                    produit=prod,
                    fraction=float(f),
                    quantite_casiers=float(q),
                )

        messages.success(request, f"Bon de vente {bon.reference} créé avec succès !")
        return redirect('gestion_depot:liste_bons_vente')

    produits = produit.Produit.objects.all()
    return render(request, 'gestion_depot/creer_bon_vente.html', {'produits': produits})

@login_required
def valider_bon_vente(request, id):
    bon = get_object_or_404(bon_vente.BonVente, id=id)
    if bon.statut != 'valide':
        for ligne in bon.lignes.all():
            # Créer un mouvement de sortie
            mouvement.Mouvement.objects.create(
                produit=ligne.produit,
                type_mouvement='sortie',
                quantite_casiers=ligne.quantite_casiers,
                utilisateur=request.user,
                ligne_vente=ligne,
            )
        bon.statut = 'valide'
        bon.save()
        messages.success(request, f"Le bon de vente {bon.reference} a été validé.")
    else:
        messages.warning(request, "Ce bon est déjà validé.")
    return redirect('gestion_depot/liste_bons_vente')

@login_required
def annuler_bon_vente(request, id):
    bon = get_object_or_404(bon_vente.BonVente, id=id)
    if bon.statut == 'valide':
        # Créer des mouvements inverses (entrée)
        for ligne in bon.lignes.all():
            mouvement.Mouvement.objects.create(
                produit=ligne.produit,
                type_mouvement='entree',
                quantite_casiers=ligne.quantite_casiers,
                utilisateur=request.user,
                fournisseur=None,
            )
        bon.statut = 'annule'
        bon.save()
        messages.success(request, f"Le bon de vente {bon.reference} a été annulé et le stock restauré.")
    else:
        messages.warning(request, "Ce bon n’est pas encore validé ou est déjà annulé.")
    return redirect('gestion_depot/liste_bons_vente')


@login_required
def liste_bons_vente(request):
    bons = bon_vente.BonVente.objects.all()

    # Filtres
    statut = request.GET.get('statut')
    vendeur_id = request.GET.get('vendeur')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    if statut:
        bons = bons.filter(statut=statut)
    if vendeur_id:
        bons = bons.filter(vendeur_id=vendeur_id)
    if date_debut:
        bons = bons.filter(date_vente__gte=date_debut)
    if date_fin:
        date_fin_complet = datetime.strptime(date_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        bons = bons.filter(date_vente__lte=date_fin_complet)

    bons = bons.order_by('-date_vente')
    vendeurs = User.objects.all()

    return render(request, 'gestion_depot/liste_bons_vente.html', {
        'bons': bons,
        'vendeurs': vendeurs,
        'statut_filter': statut,
        'vendeur_filter': vendeur_id,
        'date_debut': date_debut,
        'date_fin': date_fin,
    })

@login_required
def detail_bon_vente(request, id):
    bon = get_object_or_404(bon_vente.BonVente, id=id)
    return render(request, 'gestion_depot/detail_bon_vente.html', {'bon': bon})