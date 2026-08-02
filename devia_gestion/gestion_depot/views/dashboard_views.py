from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, FloatField
from gestion_depot.models import Produit, BonVente


@login_required
def dashboard(request):
    user = request.user

    produits = Produit.objects.annotate(
        stock_actuel=Sum(
            Case(
                When(mouvement__type_mouvement='entree', then=F('mouvement__quantite_casiers')),
                When(mouvement__type_mouvement='sortie', then=-F('mouvement__quantite_casiers')),
                default=0,
                output_field=FloatField(),
            )
        )
    )

    # Liste des produits disponibles (tous les rôles peuvent voir)
    produits_disponibles = [p for p in produits if (p.stock_actuel or 0) > 0]

    ventes_recentes = BonVente.objects.filter(statut='valide') \
        .select_related('client') \
        .order_by('-date_vente')[:10] \
        if user.groups.filter(name__in=['Gérant', 'Caissier', 'Admin']).exists() or user.is_staff else None

    produits_en_alerte = [p for p in produits if (p.stock_actuel or 0) <= p.seuil_alerte] \
        if user.groups.filter(name__in=['Gérant', 'Admin']).exists() or user.is_staff else None

    context = {
        'produits_disponibles': produits_disponibles,
        'ventes_recentes': ventes_recentes,
        'produits_en_alerte': produits_en_alerte,
        'is_caissier': user.groups.filter(name='Caissier').exists(),
        'is_gerant': user.groups.filter(name='Gérant').exists() or user.is_staff,
    }

    return render(request, 'gestion_depot/dashboard.html', context)
