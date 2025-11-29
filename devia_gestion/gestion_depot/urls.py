# gestion_depot/urls.py
from django.urls import path
from gestion_depot.views import(
    dashboard,
    rapport_ventes,
    login_view,
    logout_view,
    produit_views,
    fournisseur_views,
    bonVente_views,
    livraison_views,
    profil_views,
    facture_views
    
    
    
    
)

app_name = 'gestion_depot'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    
   
    
    path('rapport/', rapport_ventes, name='rapport_ventes'),
    
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    
    # Produits
    path('produits/', produit_views.liste_produits_avec_stock, name='liste_produits'),
    path('produits/ajouter/', produit_views.ajouter_produit, name='ajouter_produit'),
    path('produits/<int:pk>/modifier/', produit_views.modifier_produit, name='modifier_produit'),
    path('produits/<int:pk>/supprimer/', produit_views.supprimer_produit, name='supprimer_produit'),

    
    # Fournisseurs
    path('fournisseurs/', fournisseur_views.liste_fournisseurs, name='liste_fournisseurs'),
    path('fournisseurs/ajouter/', fournisseur_views.ajouter_fournisseur, name='ajouter_fournisseur'),
    path('fournisseurs/<int:pk>/modifier/', fournisseur_views.modifier_fournisseur, name='modifier_fournisseur'),
    path('fournisseurs/<int:pk>/supprimer/', fournisseur_views.supprimer_fournisseur, name='supprimer_fournisseur'),

    

    # Livraisons
    path('livraisons/', livraison_views.liste_livraisons, name='liste_livraisons'),
    path('livraisons/creer/', livraison_views.creer_bon_livraison, name='creer_bon_livraison'),
    path('livraisons/<int:id>/', livraison_views.detail_bon_livraison, name='detail_bon_livraison'),    
        
    # Ventes
    path('ventes/', bonVente_views.liste_bons_vente, name='liste_bons_vente'),
    path('ventes/creer/', bonVente_views.creer_bon_vente, name='creer_bon_vente'),
    path('ventes/<int:id>/valider/', bonVente_views.valider_bon_vente, name='valider_bon_vente'),
    path('ventes/<int:id>/annuler/', bonVente_views.annuler_bon_vente, name='annuler_bon_vente'),
    path('ventes/<int:id>/', bonVente_views.detail_bon_vente, name='detail_bon_vente'),
    
    
    path('profil/', profil_views.profil_utilisateur, name='profil_utilisateur'),
    path('profil/modifier/', profil_views.modifier_profil, name='modifier_profil'),
    
    path('facture/<int:id>/', facture_views.generer_facture, name='generer_facture'),
]

