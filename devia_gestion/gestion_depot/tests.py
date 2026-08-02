from decimal import Decimal
from django.test import TestCase
from django.test import Client as DjangoClient
from django.urls import reverse
from django.contrib.auth.models import User, Group
from gestion_depot.models import (
    Produit, Fournisseur, Client, BonVente, BonLivraison,
    LigneVente, LigneLivraison, Mouvement, ProfilUtilisateur,
)


class BaseTest(TestCase):
    def setUp(self):
        self.http_client = DjangoClient()
        self.caissier = User.objects.create_user(username='caissier1', password='pass12345')
        self.gerant = User.objects.create_user(username='gerant1', password='pass12345')
        self.admin = User.objects.create_user(username='admin1', password='pass12345', is_superuser=True)
        Group.objects.get_or_create(name='Caissier')
        Group.objects.get_or_create(name='Gérant')
        Group.objects.get_or_create(name='Admin')
        self.caissier.groups.add(Group.objects.get(name='Caissier'))
        self.gerant.groups.add(Group.objects.get(name='Gérant'))

        self.produit = Produit.objects.create(
            nom='Coca-Cola 50cl', categorie='boisson', casier_contenu=24,
            prix_achat_casier=Decimal('700'), prix_vente_casier=Decimal('750'),
            seuil_alerte=5,
        )
        self.fournisseur = Fournisseur.objects.create(nom='Distributeur Test', contact='22890000000')
        self.client_test = Client.objects.create(nom='Client Test')


class ProduitTests(BaseTest):
    def test_stock_disponible(self):
        self.assertEqual(self.produit.stock_disponible(), 0)

    def test_en_alerte(self):
        self.assertTrue(self.produit.en_alerte())

    def test_contrainte_prix_vente_superieur_achat(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Produit.objects.create(
                nom='Produit interdit', categorie='eau', casier_contenu=24,
                prix_achat_casier=Decimal('1000'), prix_vente_casier=Decimal('900'),
                seuil_alerte=5,
            )


class BonVenteTests(BaseTest):
    def test_statut_par_defaut_en_cours(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        self.assertEqual(bon.statut, 'en_cours')

    def test_reference_auto(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        self.assertTrue(bon.reference.startswith('VENTE-'))

    def test_validation_cree_mouvement_de_sortie(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        LigneVente.objects.create(bon=bon, produit=self.produit, fraction=Decimal('1.00'), quantite_casiers=Decimal('2'))
        Mouvement.objects.create(
            produit=self.produit, type_mouvement='entree',
            quantite_casiers=Decimal('10'), utilisateur=self.admin,
        )

        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.post(reverse('gestion_depot:valider_bon_vente', args=[bon.id]))
        self.assertRedirects(response, reverse('gestion_depot:liste_bons_vente'))

        bon.refresh_from_db()
        self.assertEqual(bon.statut, 'valide')
        self.assertEqual(self.produit.stock_disponible(), Decimal('8.00'))

    def test_validation_par_get_interdite(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:valider_bon_vente', args=[bon.id]))
        self.assertEqual(response.status_code, 405)

    def test_creer_bon_vente_fraction_libre(self):
        Mouvement.objects.create(
            produit=self.produit, type_mouvement='entree',
            quantite_casiers=Decimal('10'), utilisateur=self.admin,
        )
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.post(reverse('gestion_depot:creer_bon_vente'), {
            'client_nom': 'Client Libre',
            'type_paiement': 'especes',
            'produit': [str(self.produit.id)],
            'fraction': ['0.33'],
            'quantite': ['2'],
        })
        self.assertRedirects(response, reverse('gestion_depot:liste_bons_vente'))
        ligne = LigneVente.objects.latest('id')
        self.assertEqual(ligne.fraction, Decimal('0.33'))
        self.assertEqual(ligne.quantite_casiers, Decimal('2'))

    def test_creer_bon_vente_fraction_hors_bornes_rejetee(self):
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.post(reverse('gestion_depot:creer_bon_vente'), {
            'client_nom': 'Client',
            'type_paiement': 'especes',
            'produit': [str(self.produit.id)],
            'fraction': ['10.00'],
            'quantite': ['1'],
        })
        self.assertRedirects(response, reverse('gestion_depot:creer_bon_vente'))
        self.assertEqual(LigneVente.objects.count(), 0)

    def test_caissier_ne_voit_que_ses_ventes(self):
        BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        BonVente.objects.create(vendeur=self.gerant, client=self.client_test, type_paiement='especes')
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:liste_bons_vente'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['bons']), 1)


class BonLivraisonTests(BaseTest):
    def test_reference_auto(self):
        bon = BonLivraison.objects.create(fournisseur=self.fournisseur, utilisateur=self.admin)
        self.assertTrue(bon.reference.startswith('LIV-'))


class DocumentTests(BaseTest):
    def test_traversal_bloque(self):
        self.http_client.login(username='admin1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:serve_protected_document', args=['../../etc/passwd']))
        self.assertEqual(response.status_code, 404)


class LoginTests(BaseTest):
    def test_login_page(self):
        response = self.http_client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_fonctionne(self):
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:dashboard'))
        self.assertEqual(response.status_code, 200)
