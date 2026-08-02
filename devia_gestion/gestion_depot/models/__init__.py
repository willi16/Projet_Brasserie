# gestion_depot/models/__init__.py
from .produit import Produit
from .fournisseur import Fournisseur
from .mouvement import Mouvement

from .ligne_vente import LigneVente

from .bon_vente import BonVente
from .client import Client

from .bon_livraison import BonLivraison
from .ligne_livraison import LigneLivraison

from .profil import ProfilUtilisateur
from .userActionLog import UserActionLog


__all__ = [
    'Produit', 'Client', 'Fournisseur', 'Mouvement', 'LigneVente',
    'BonVente', 'BonLivraison', 'LigneLivraison', 'ProfilUtilisateur',
    'UserActionLog',
]
