# gestion_depot/views/__init__.py
from .dashboard_views import dashboard
from .bonVente_views import (
    creer_bon_vente,
    detail_bon_vente,
    liste_bons_vente,
    annuler_bon_vente,
    valider_bon_vente
)
from .rapport_views import rapport_ventes
from .auth_views import login_view, logout_view 
from .produit_views import (
    liste_produits_avec_stock,
    ajouter_produit,
    modifier_produit,
    supprimer_produit
)
from .fournisseur_views import (
    liste_fournisseurs,
    ajouter_fournisseur,
    modifier_fournisseur,
    supprimer_fournisseur
)

from .livraison_views import (
    liste_livraisons,
    creer_bon_livraison
)
__all__ = [
    'dashboard', 
    'creer_bon_vente', 
    'rapport_ventes',
    'login_view',
    'logout_view',
    'liste_produits_avec_stock',
    'ajouter_produit',
    'modifier_produit',
    'supprimer_produit',
    'liste_fournisseurs',
    'ajouter_fournisseur',
    'modifier_fournisseur',
    'supprimer_fournisseur',
    'liste_livraisons',
    'creer_bon_livraison',
    'detail_bon_vente',
    'liste_bons_vente',
    'annuler_bon_vente',
    'valider_bon_vente'
]