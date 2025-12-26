# gestion_depot/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, F, FloatField, Case, When, Value
from django.db.models.functions import Cast, Coalesce
from django.utils import timezone
from datetime import datetime, timedelta, time
from gestion_depot.models import BonVente, LigneVente, Produit
from gestion_depot.decorators import group_required
from collections import defaultdict
from django.utils.dateformat import DateFormat
import json
import openpyxl
from openpyxl.styles import Font, Alignment


@login_required
@group_required('Gérant', 'Admin')
def rapport_ventes(request):
    # === 1. Gestion des filtres ===
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    periode = request.GET.get('periode')

    today = timezone.now().date()
    if periode == 'journalier':
        date_debut_obj = today
        date_fin_obj = today
    elif periode == 'hebdomadaire':
        date_debut_obj = today - timedelta(days=7)
        date_fin_obj = today
    elif periode == 'mensuel':
        date_debut_obj = today.replace(day=1)
        date_fin_obj = today
    else:
        date_debut_obj = date_fin_obj = None
        if date_debut:
            try:
                date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            except ValueError:
                pass
        if date_fin:
            try:
                date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            except ValueError:
                pass

    if date_debut_obj and date_fin_obj and date_debut_obj > date_fin_obj:
        date_debut_obj = date_fin_obj = None

    # === 2. Filtrer les bons validés ===
    ventes_qs = BonVente.objects.filter(statut='valide')
    if date_debut_obj:
        ventes_qs = ventes_qs.filter(date_vente__gte=date_debut_obj)
    if date_fin_obj:
        ventes_qs = ventes_qs.filter(date_vente__lte=datetime.combine(date_fin_obj, time.max))

    bon_ids = list(ventes_qs.values_list('id', flat=True))

    # === 3. Statistiques par produit (annotate) ===
    lignes_qs = LigneVente.objects.filter(bon_id__in=bon_ids)

    stats_produits = lignes_qs.values(
        'produit__id',
        'produit__nom'
    ).annotate(
        quantite_totale=Sum(Cast(F('quantite_casiers') * F('fraction'), FloatField())),
        revenu_total=Sum(
            F('produit__prix_vente_casier') * Cast(F('quantite_casiers') * F('fraction'), FloatField()),
            output_field=FloatField()
        ),
        nombre_ventes=Count('id')
    ).order_by('-quantite_totale')

    stats_produits = list(stats_produits)

    total_revenu_agg = lignes_qs.aggregate(
        total=Sum(
            F('produit__prix_vente_casier') * Cast(F('quantite_casiers') * F('fraction'), FloatField()),
            output_field=FloatField()
        )
    )
    total_revenu = total_revenu_agg['total'] or 0

    produit_plus_vendu = stats_produits[0] if stats_produits else None
    produit_moins_vendu = stats_produits[-1] if stats_produits else None

    # === 4. Inventaire avec stock annoté ===
    produits_stock = Produit.objects.annotate(
        stock_actuel=Coalesce(
            Sum(
                Case(
                    When(mouvement__type_mouvement='entree', then=F('mouvement__quantite_casiers')),
                    When(mouvement__type_mouvement='sortie', then=-F('mouvement__quantite_casiers')),
                    default=Value(0.0),
                    output_field=FloatField()
                )
            ),
            Value(0.0)
        )
    ).only('nom', 'seuil_alerte')

    inventaire = [
        {
            'nom': p.nom,
            'stock': round(p.stock_actuel, 2),
            'seuil_alerte': p.seuil_alerte,
            'en_alerte': p.stock_actuel <= p.seuil_alerte,
        }
        for p in produits_stock
    ]

    # === 5. Données graphique ===
    ventes_par_jour = defaultdict(float)
    for ligne in lignes_qs.only('bon__date_vente', 'quantite_casiers', 'fraction', 'produit__prix_vente_casier'):
        jour = DateFormat(ligne.bon.date_vente).format('Y-m-d')
        total_ligne = float(ligne.produit.prix_vente_casier * ligne.quantite_casiers * ligne.fraction)
        ventes_par_jour[jour] += total_ligne

    labels_jours = sorted(ventes_par_jour.keys())
    data_ventes = [round(ventes_par_jour[jour], 0) for jour in labels_jours]

    # === 6. Export Excel ===
    if request.GET.get('export') == 'excel':
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="rapport_ventes.xlsx"'

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Rapport de Ventes"

        ws.merge_cells('A1:D1')
        ws['A1'] = "RAPPORT DE VENTES"
        ws['A1'].font = Font(size=16, bold=True)
        ws['A1'].alignment = Alignment(horizontal='center')

        debut_str = str(date_debut_obj) if date_debut_obj else "Indéfini"
        fin_str = str(date_fin_obj) if date_fin_obj else "Indéfini"
        ws.merge_cells('A2:D2')
        ws['A2'] = f"Période : du {debut_str} au {fin_str}"
        ws['A2'].alignment = Alignment(horizontal='center')

        ws.append([])
        ws.append(['Produit', 'Quantité totale', 'Revenu total (FCFA)', 'Nombre de ventes'])
        for cell in ws[4]:
            cell.font = Font(bold=True)

        for stat in stats_produits:
            ws.append([
                stat['produit__nom'],
                round(stat['quantite_totale'], 2),
                round(stat['revenu_total'], 0),
                stat['nombre_ventes']
            ])

        ws.append([])
        ws.append(['Total général', '', round(total_revenu, 0), ''])

        wb.save(response)
        return response

    # === 7. Récupérer les lignes pour le tableau détaillé ===
    lignes = LigneVente.objects.filter(bon_id__in=bon_ids).select_related('bon', 'produit').order_by('-bon__date_vente')

    # === 8. Contexte final ===
    context = {
        'total_revenu': round(total_revenu, 2),
        'produit_plus_vendu': produit_plus_vendu,
        'produit_moins_vendu': produit_moins_vendu,
        'inventaire': inventaire,
        'date_debut': date_debut_obj,
        'date_fin': date_fin_obj,
        'periode': periode,
        'labels_jours': json.dumps(labels_jours),
        'data_ventes': json.dumps(data_ventes),
        'lignes': lignes,  # ⬅️ Crucial pour afficher le tableau des ventes
    }

    return render(request, 'gestion_depot/rapport.html', context)