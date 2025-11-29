# gestion_depot/admin.py
from django.contrib import admin
from .models import Produit, Fournisseur, Mouvement, BonVente, LigneVente

# Filtre personnalisé pour 'en_alerte'
class EnAlerteFilter(admin.SimpleListFilter):
    title = 'État du stock'  # Titre affiché dans l’admin
    parameter_name = 'en_alerte'

    def lookups(self, request, model_admin):
        return (
            ('oui', 'En alerte'),
            ('non', 'Stock suffisant'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'oui':
            filtered_products = []
            for obj in queryset:
                if obj.en_alerte():
                    filtered_products.append(obj.id)
            return queryset.filter(id__in=filtered_products)
        if self.value() == 'non':
            filtered_products = []
            for obj in queryset:
                if not obj.en_alerte():
                    filtered_products.append(obj.id)
            return queryset.filter(id__in=filtered_products)
        return queryset

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'casier_contenu', 'prix_vente_casier', 'stock_disponible', 'en_alerte')
    list_filter = ('categorie', 'casier_contenu', EnAlerteFilter)
    search_fields = ('nom',)

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact')

@admin.register(Mouvement)
class MouvementAdmin(admin.ModelAdmin):
    list_display = ('produit', 'type_mouvement', 'quantite_casiers', 'date', 'fournisseur')
    list_filter = ('type_mouvement', 'date')

@admin.register(BonVente)
class BonVenteAdmin(admin.ModelAdmin):
    list_display = ['reference', 'date_vente', 'vendeur', 'client', 'type_paiement', 'statut', 'total']
    list_filter = ['statut', 'type_paiement', 'date_vente']
    search_fields = ['reference', 'client_nom']

    def total(self, obj):
        return obj.total()
    total.short_description = 'Total (FCFA)'
    

@admin.register(LigneVente)
class LigneVenteAdmin(admin.ModelAdmin):
    list_display = ['bon', 'produit', 'fraction', 'quantite_casiers', 'prix_total']
    list_filter = ['bon__statut', 'produit']
    raw_id_fields = ['bon', 'produit'] 