from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
from gestion_depot.models import BonVente, LigneVente, Produit
from gestion_depot.decorators import group_required
from collections import defaultdict
from django.utils.dateformat import DateFormat
import json

@login_required
@group_required('Gérant', 'Admin')
def rapport_ventes(request):
    # Filtres
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    periode = request.GET.get('periode')

    # Appliquer la période si sélectionnée
    if periode == 'journalier':
        date_fin = timezone.now().date()
        date_debut = date_fin
    elif periode == 'hebdomadaire':
        date_fin = timezone.now().date()
        date_debut = date_fin - timedelta(days=7)
    elif periode == 'mensuel':
        date_fin = timezone.now().date()
        date_debut = date_fin.replace(day=1)

    # Filtrer les ventes validées
    ventes = BonVente.objects.filter(statut='valide')

    if date_debut:
        ventes = ventes.filter(date_vente__gte=date_debut)
    if date_fin:
        date_fin_complet = datetime.strptime(date_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        ventes = ventes.filter(date_vente__lte=date_fin_complet)

    # Récupérer toutes les lignes de vente
    lignes = LigneVente.objects.filter(bon__in=ventes).select_related('produit')

    # Calculer le total des ventes
    total_revenu = sum(l.prix_total() for l in lignes)

    # Statistiques par produit
    stats_produits = {}
    for ligne in lignes:
        prod_id = ligne.produit.id
        if prod_id not in stats_produits:
            stats_produits[prod_id] = {
                'nom': ligne.produit.nom,
                'quantite_totale': 0,
                'revenu_total': 0,
                'nombre_ventes': 0,
            }
        stats_produits[prod_id]['quantite_totale'] += ligne.quantite_casiers * ligne.fraction
        stats_produits[prod_id]['revenu_total'] += ligne.prix_total()
        stats_produits[prod_id]['nombre_ventes'] += 1

    # Trier par quantité totale pour trouver le plus/moins vendu
    produits_tries = sorted(stats_produits.values(), key=lambda x: x['quantite_totale'], reverse=True)
    produit_plus_vendu = produits_tries[0] if produits_tries else None
    produit_moins_vendu = produits_tries[-1] if produits_tries else None

    # Inventaire : stock actuel par produit
    inventaire = []
    for produit in Produit.objects.all():
        stock = produit.stock_disponible()
        inventaire.append({
            'nom': produit.nom,
            'stock': stock,
            'seuil_alerte': produit.seuil_alerte,
            'en_alerte': stock <= produit.seuil_alerte,
        })

    # Graphique : ventes par jour (sur la période sélectionnée)
    ventes_par_jour = defaultdict(int)
    for ligne in lignes:
        jour = DateFormat(ligne.bon.date_vente).format('Y-m-d')
        ventes_par_jour[jour] += ligne.prix_total()

    # Trier par date
    labels_jours = sorted(ventes_par_jour.keys())
    data_ventes = [ventes_par_jour[jour] for jour in labels_jours]

    context = {
        'lignes': lignes,
        'total_revenu': total_revenu,
        'produit_plus_vendu': produit_plus_vendu,
        'produit_moins_vendu': produit_moins_vendu,
        'inventaire': inventaire,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'periode': periode,
        'labels_jours': json.dumps(labels_jours),
        'data_ventes': json.dumps(data_ventes),
    }

    return render(request, 'gestion_depot/rapport.html', context)