import os
import shutil
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.conf import settings
from gestion_depot.models import (
    Produit, BonVente, LigneVente, Client, Fournisseur,
    bon_livraison, ligne_livraison, Mouvement, ProfilUtilisateur, userActionLog
)

class Command(BaseCommand):
    help = 'Supprime toutes les données et génère des données de test réalistes'

    def handle(self, *args, **options):
        self.stdout.write('⚠️  Suppression de toutes les données...', ending='')
        self.clear_all_data()
        self.stdout.write(' ✅ OK', style_func=self.style.SUCCESS)

        self.stdout.write('🔧 Création des rôles...', ending='')
        self.create_groups()
        self.stdout.write(' ✅ OK', style_func=self.style.SUCCESS)

        self.stdout.write('👥 Création des utilisateurs...', ending='')
        self.create_users()
        self.stdout.write(' ✅ OK', style_func=self.style.SUCCESS)

        self.stdout.write('🛍️  Création des produits...', ending='')
        self.create_products()
        self.stdout.write(' ✅ OK', style_func=self.style.SUCCESS)

        self.stdout.write('💼 Création des clients et fournisseurs...', ending='')
        self.create_clients_fournisseurs()
        self.stdout.write(' ✅ OK', style_func=self.style.SUCCESS)

        self.stdout.write('📥 Création des livraisons (entrées en stock)...', ending='')
        self.create_deliveries()
        self.stdout.write(' ✅ OK', style_func=self.style.SUCCESS)

        self.stdout.write('💰 Création des ventes (sorties de stock)...', ending='')
        self.create_sales()
        self.stdout.write(' ✅ OK', style_func=self.style.SUCCESS)

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Données de test générées avec succès !')
        )
        self.stdout.write('   - Admin: admin / admin123')
        self.stdout.write('   - Gérant: gerant1 / gerant123')
        self.stdout.write('   - Caissier: caissier1 / caissier123')
        self.stdout.write('   - 12 produits, 5 clients, 2 fournisseurs')
        self.stdout.write('   - 8 livraisons, 15 ventes')
        self.stdout.write('   - Stocks mis à jour via Mouvement')

    def clear_all_data(self):
        """Supprime toutes les données existantes."""
        from django.apps import apps
        models_to_clear = [
            'UserActionLog', 'Mouvement', 'LigneVente', 'BonVente',
            'LigneLivraison', 'BonLivraison', 'Produit', 'Client',
            'Fournisseur', 'ProfilUtilisateur'
        ]
        for model_name in models_to_clear:
            model = apps.get_model('gestion_depot', model_name)
            model.objects.all().delete()

        # Supprimer les utilisateurs et groupes
        User.objects.all().delete()
        Group.objects.all().delete()

        # Nettoyer les fichiers médias
        media_dirs = ['photos', 'cartes_id/recto', 'cartes_id/verso', 'factures']
        for d in media_dirs:
            dir_path = os.path.join(settings.MEDIA_ROOT, d)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                os.makedirs(dir_path, exist_ok=True)

    def create_groups(self):
        Group.objects.get_or_create(name='Admin')
        Group.objects.get_or_create(name='Gérant')
        Group.objects.get_or_create(name='Caissier')

    def create_users(self):
        users_data = [
            {'username': 'admin', 'email': 'admin@deiva.tg', 'password': 'admin123', 'groups': ['Admin'], 'is_staff': True, 'is_superuser': True},
            {'username': 'gerant1', 'email': 'gerant1@deiva.tg', 'password': 'gerant123', 'groups': ['Gérant'], 'is_staff': True},
            {'username': 'caissier1', 'email': 'caissier1@deiva.tg', 'password': 'caissier123', 'groups': ['Caissier']},
        ]

        for data in users_data:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                is_staff=data.get('is_staff', False),
                is_superuser=data.get('is_superuser', False)
            )
            for group_name in data['groups']:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)

            # Créer un profil uniquement s'il n'existe pas
            ProfilUtilisateur.objects.get_or_create(
                user=user,
                defaults={
                    'telephone': f"2289{random.randint(10000000, 99999999)}",
                    'adresse': "Lomé, Togo"
                }
            )

    def create_products(self):
        produits_data = [
            ("Coca-Cola 50cl", "boisson", 24, 700, 750),
            ("Fanta Orange 50cl", "boisson", 24, 650, 700),
            ("Sprite 50cl", "boisson", 24, 650, 700),
            ("Pepsi 50cl", "boisson", 24, 650, 700),
            ("Flag 65cl", "biere", 24, 900, 950),
            ("Guiness 65cl", "biere", 24, 1000, 1050),
            ("Stella 65cl", "biere", 24, 950, 1000),
            ("Eau Cristal 1.5L", "eau", 12, 500, 550),
            ("Eau Volvic 1.5L", "eau", 12, 550, 600),
            ("Eau Source 50cl", "eau", 24, 300, 350),
            ("Chips Sel 100g", "sucrerie", 24, 400, 450),
            ("Chips Fromage 100g", "sucrerie", 24, 400, 450),
        ]

        for nom, cat, casier, prix_achat, prix_vente in produits_data:
            Produit.objects.create(
                nom=nom,
                categorie=cat,
                casier_contenu=casier,
                prix_achat_casier=prix_achat,
                prix_vente_casier=prix_vente,
                seuil_alerte=random.randint(3, 8)
            )

    def create_clients_fournisseurs(self):
        clients_data = [
            ("Koffi Mensah", "22890123456"),
            ("Afi Dossou", "22891234567"),
            ("Komlan Amegbeto", "22892345678"),
            ("Ati Kpatcha", "22893456789"),
            ("Yao Dossou", "22894567890"),
        ]

        for nom, tel in clients_data:
            Client.objects.get_or_create(nom=nom, telephone=tel)

        fournisseurs_data = [
            ("Société Boissons Togo", "22897654321"),
            ("Distributeur Bières Lomé", "22898765432"),
        ]

        for nom, tel in fournisseurs_data:
            Fournisseur.objects.get_or_create(nom=nom, contact=tel)

    def create_deliveries(self):
        """Crée des livraisons et met à jour les stocks via Mouvement."""
        produits = list(Produit.objects.all())
        fournisseurs = list(Fournisseur.objects.all())
        admin = User.objects.get(username='admin')

        for i in range(8):
            fournisseur = random.choice(fournisseurs)
            bon = bon_livraison.BonLivraison.objects.create(
                fournisseur=fournisseur,
                utilisateur=admin
            )

            nb_lignes = random.randint(2, 5)
            for _ in range(nb_lignes):
                produit = random.choice(produits)
                quantite = random.randint(10, 50)
                prix_achat = produit.prix_achat_casier

                ligne_livraison.LigneLivraison.objects.create(
                    bon=bon,
                    produit=produit,
                    quantite_casiers=quantite,
                    casier_contenu=produit.casier_contenu,
                    prix_achat_casier=prix_achat
                )

                # Créer le mouvement d'entrée
                Mouvement.objects.create(
                    produit=produit,
                    type_mouvement='entree',
                    quantite_casiers=quantite,
                    fournisseur=fournisseur,
                    utilisateur=admin
                )

    def create_sales(self):
        """Crée des ventes avec fractions et mouvements de sortie."""
        produits = list(Produit.objects.all())
        clients = list(Client.objects.all())
        vendeurs = list(User.objects.filter(groups__name__in=['Caissier', 'Gérant', 'Admin']))
        fractions = [1.00, 0.75, 0.50, 0.25]

        for i in range(15):
            client = random.choice(clients)
            vendeur = random.choice(vendeurs)
            type_paiement = random.choice(['especes', 'credit'])
            
            bon = BonVente.objects.create(
                client=client,
                vendeur=vendeur,
                type_paiement=type_paiement,
                statut='valide'
            )

            nb_lignes = random.randint(1, 4)
            for _ in range(nb_lignes):
                # Choisir un produit avec stock > 0
                produit = random.choice(produits)
                stock_dispo = produit.stock_disponible()
                if stock_dispo <= 0:
                    continue

                fraction = random.choice(fractions)
                quantite = min(random.randint(1, 5), int(stock_dispo // 1))

                if quantite <= 0:
                    continue

                ligne = LigneVente.objects.create(
                    bon=bon,
                    produit=produit,
                    fraction=fraction,
                    quantite_casiers=quantite
                )

                # Créer le mouvement de sortie
                Mouvement.objects.create(
                    produit=produit,
                    type_mouvement='sortie',
                    quantite_casiers=quantite,
                    utilisateur=vendeur,
                    ligne_vente=ligne
                )