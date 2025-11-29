from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from gestion_depot.models import Produit, BonVente

@login_required
def dashboard(request):
    user = request.user
    
    

    # Liste des produits disponibles (tous les rôles peuvent voir)
    produits_disponibles = [p for p in Produit.objects.all() if p.stock_disponible() > 0]

    ventes_recentes = BonVente.objects.filter(statut='valide').order_by('-date_vente')[:10] \
        if user.groups.filter(name__in=['Gérant', 'Admin']).exists() or user.is_staff else None

    produits_en_alerte = [p for p in Produit.objects.all() if p.en_alerte()] \
        if user.groups.filter(name__in=['Gérant', 'Admin']).exists() or user.is_staff else None

    context = {
        'produits_disponibles': produits_disponibles,
        'ventes_recentes': ventes_recentes,
        'produits_en_alerte': produits_en_alerte,
        'is_caissier': user.groups.filter(name='Caissier').exists(),
        'is_gerant': user.groups.filter(name='Gérant').exists() or user.is_staff,
    }
    
    # for p in Produit.objects.all():
    #     if p.stock_disponible() > 0:
    #         produits_disponibles.append(p)

    # # Dernières ventes (Gérant et Admin)
    # ventes_recentes = Vente.objects.all().order_by('-date')[:10] if user.groups.filter(name__in=['Gérant', 'Admin']).exists() or user.is_staff else None

    # # Alertes stock (Gérant et Admin)
    # produits_en_alerte = [p for p in Produit.objects.all() if p.en_alerte()] if user.groups.filter(name__in=['Gérant', 'Admin']).exists() or user.is_staff else None

    # context = {
    #     'produits_disponibles': produits_disponibles,
    #     'ventes_recentes': ventes_recentes,
    #     'produits_en_alerte': produits_en_alerte,
    #     'is_caissier': user.groups.filter(name='Caissier').exists(),
    #     'is_gerant': user.groups.filter(name='Gérant').exists() or user.is_staff,
    # }

    return render(request, 'gestion_depot/dashboard.html', context)