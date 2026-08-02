# gestion_depot/admin.py
from django.contrib import admin
from django.db.models import Sum, Case, When, F
from .models import Produit, Fournisseur, Mouvement, BonVente, LigneVente, CasierEmporte, Parametre


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
        if self.value() is None:
            return queryset
        queryset = queryset.annotate(
            _stock=Sum(
                Case(
                    When(mouvement__type_mouvement='entree', then=F('mouvement__quantite_casiers')),
                    When(mouvement__type_mouvement='sortie', then=-F('mouvement__quantite_casiers')),
                    default=0,
                )
            )
        )
        if self.value() == 'oui':
            return queryset.filter(_stock__lte=F('seuil_alerte'))
        if self.value() == 'non':
            return queryset.filter(_stock__gt=F('seuil_alerte'))
        return queryset


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'casier_contenu', 'modele', 'prix_vente_casier', 'stock_disponible', 'en_alerte')
    list_filter = ('categorie', 'casier_contenu', 'modele', EnAlerteFilter)
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
    search_fields = ['reference', 'client__nom']

    @admin.display(description='Total (FCFA)')
    def total(self, obj):
        return obj.total()


@admin.register(LigneVente)
class LigneVenteAdmin(admin.ModelAdmin):
    list_display = ['bon', 'produit', 'fraction', 'quantite_casiers', 'prix_total']
    list_filter = ['bon__statut', 'produit']
    raw_id_fields = ['bon', 'produit']


@admin.register(CasierEmporte)
class CasierEmporteAdmin(admin.ModelAdmin):
    list_display = ['client', 'bon', 'modele', 'nombre_casiers', 'nombre_rendus', 'date_emport', 'date_retour_complet']
    list_filter = ['modele', 'date_emport']
    search_fields = ['client__nom', 'bon__reference']


@admin.register(Parametre)
class ParametreAdmin(admin.ModelAdmin):
    list_display = ['nom', 'valeur']
