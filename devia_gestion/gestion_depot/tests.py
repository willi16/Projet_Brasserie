from decimal import Decimal
from django.test import TestCase, override_settings
from django.test import Client as DjangoClient
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta
from gestion_depot.models import (
    Produit, Fournisseur, Client, BonVente, BonLivraison,
    LigneVente, LigneLivraison, Mouvement, ProfilUtilisateur,
    CasierEmporte, Parametre,
)
from gestion_depot.models.parametre import SANCTION_CASIER


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

    def test_validation_mouvement_prend_en_compte_fraction(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        LigneVente.objects.create(bon=bon, produit=self.produit, fraction=Decimal('0.50'), quantite_casiers=Decimal('2'))
        Mouvement.objects.create(
            produit=self.produit, type_mouvement='entree',
            quantite_casiers=Decimal('10'), utilisateur=self.admin,
        )

        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.post(reverse('gestion_depot:valider_bon_vente', args=[bon.id]))
        self.assertRedirects(response, reverse('gestion_depot:liste_bons_vente'))

        bon.refresh_from_db()
        self.assertEqual(bon.statut, 'valide')
        self.assertEqual(self.produit.stock_disponible(), Decimal('9.00'))
        sortie = Mouvement.objects.get(ligne_vente=bon.lignes.first())
        self.assertEqual(sortie.quantite_casiers, Decimal('1.00'))

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

    def test_mise_a_jour_persistee(self):
        bon = BonLivraison.objects.create(fournisseur=self.fournisseur, utilisateur=self.admin)
        autre_fournisseur = Fournisseur.objects.create(nom='Autre fournisseur', contact='00000000')
        bon.fournisseur = autre_fournisseur
        bon.save()
        bon.refresh_from_db()
        self.assertEqual(bon.fournisseur, autre_fournisseur)

    def test_creation_livraison_produit_invalide_redirige_sans_500(self):
        self.http_client.login(username='gerant1', password='pass12345')
        response = self.http_client.post(reverse('gestion_depot:creer_bon_livraison'), {
            'fournisseur': str(self.fournisseur.id),
            'produit': ['abc'],
            'casier_contenu': ['24'],
            'prix_achat_casier': ['700'],
            'quantite': ['2'],
        })
        self.assertRedirects(response, reverse('gestion_depot:creer_bon_livraison'))
        self.assertEqual(BonLivraison.objects.count(), 0)


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

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_manage_users_activer_desactiver_redirige(self):
        self.http_client.login(username='admin1', password='pass12345')
        user = User.objects.create_user(username='testuser', password='pass12345')

        response = self.http_client.post(reverse('gestion_depot:manage_users'), {
            'user_id': user.id, 'action': 'deactivate',
        })
        self.assertRedirects(response, reverse('gestion_depot:manage_users'))
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        response = self.http_client.post(reverse('gestion_depot:manage_users'), {
            'user_id': user.id, 'action': 'activate',
        })
        self.assertRedirects(response, reverse('gestion_depot:manage_users'))
        user.refresh_from_db()
        self.assertTrue(user.is_active)


class CasierEmporteTests(BaseTest):
    def setUp(self):
        super().setUp()
        Mouvement.objects.create(
            produit=self.produit, type_mouvement='entree',
            quantite_casiers=Decimal('10'), utilisateur=self.admin,
        )

    def _creer_bon(self):
        return self.http_client.post(reverse('gestion_depot:creer_bon_vente'), {
            'client_nom': 'Client Casiers',
            'type_paiement': 'especes',
            'produit': [str(self.produit.id)],
            'fraction': ['1.00'],
            'quantite': ['2'],
        })

    def test_creation_bon_sans_enregistrement_de_casiers(self):
        self.http_client.login(username='caissier1', password='pass12345')
        self._creer_bon()
        self.assertEqual(CasierEmporte.objects.count(), 0)

    def test_enregistrement_casiers_apres_creation_bon(self):
        produit = Produit.objects.create(
            nom='Flag 65cl', categorie='biere', casier_contenu=12,
            prix_achat_casier=Decimal('900'), prix_vente_casier=Decimal('950'),
            seuil_alerte=5,
        )
        self.assertEqual(produit.modele, 'GM12')
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        LigneVente.objects.create(bon=bon, produit=produit, fraction=Decimal('1.00'), quantite_casiers=Decimal('2'))

        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.post(
            reverse('gestion_depot:enregistrer_casiers_bon', args=[bon.id]),
            {'nombre_casiers': '3'},
        )
        self.assertRedirects(response, reverse('gestion_depot:detail_bon_vente', args=[bon.id]))
        casier = CasierEmporte.objects.latest('id')
        self.assertEqual(casier.bon, bon)
        self.assertEqual(casier.nombre_casiers, 3)
        self.assertEqual(casier.restant, 3)
        self.assertEqual(casier.modele, 'GM12')
        self.assertEqual(casier.bouteilles_par_casier, 12)
        self.assertFalse(casier.en_retard)

    def test_bon_sans_produit_a_casier_pas_de_suivi(self):
        eau = Produit.objects.create(
            nom='Eau Cristal 1.5L', categorie='eau', casier_contenu=12,
            prix_achat_casier=Decimal('500'), prix_vente_casier=Decimal('550'),
            seuil_alerte=5,
        )
        self.assertEqual(eau.modele, 'NC')
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        LigneVente.objects.create(bon=bon, produit=eau, fraction=Decimal('1.00'), quantite_casiers=Decimal('1'))

        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.post(
            reverse('gestion_depot:enregistrer_casiers_bon', args=[bon.id]),
            {'nombre_casiers': '3'},
        )
        self.assertRedirects(response, reverse('gestion_depot:detail_bon_vente', args=[bon.id]))
        self.assertEqual(CasierEmporte.objects.count(), 0)

    def test_retour_partiel(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        casier = CasierEmporte.objects.create(bon=bon, client=self.client_test, nombre_casiers=5)
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.post(
            reverse('gestion_depot:enregistrer_retour_casiers', args=[casier.id]),
            {'quantite_rendue': '2'},
        )
        self.assertRedirects(response, reverse('gestion_depot:liste_casiers_emportes'))
        casier.refresh_from_db()
        self.assertEqual(casier.nombre_rendus, 2)
        self.assertEqual(casier.restant, 3)
        self.assertIsNone(casier.date_retour_complet)

    def test_retour_complet(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        casier = CasierEmporte.objects.create(bon=bon, client=self.client_test, nombre_casiers=5)
        self.http_client.login(username='caissier1', password='pass12345')
        self.http_client.post(
            reverse('gestion_depot:enregistrer_retour_casiers', args=[casier.id]),
            {'quantite_rendue': '5'},
        )
        casier.refresh_from_db()
        self.assertEqual(casier.restant, 0)
        self.assertIsNotNone(casier.date_retour_complet)

    def test_retour_superieur_au_restant_rejete(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        casier = CasierEmporte.objects.create(bon=bon, client=self.client_test, nombre_casiers=3)
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.post(
            reverse('gestion_depot:enregistrer_retour_casiers', args=[casier.id]),
            {'quantite_rendue': '4'},
        )
        self.assertRedirects(response, reverse('gestion_depot:liste_casiers_emportes'))
        casier.refresh_from_db()
        self.assertEqual(casier.nombre_rendus, 0)

    def test_modele_auto_selon_taille(self):
        grand = Produit.objects.create(
            nom='Bière 65cl', categorie='biere', casier_contenu=12,
            prix_achat_casier=Decimal('900'), prix_vente_casier=Decimal('950'),
            seuil_alerte=5,
        )
        self.assertEqual(grand.modele, 'GM12')
        self.assertEqual(grand.get_modele_display(), 'Grand modèle - 12 bouteilles')

        petit = Produit.objects.create(
            nom='Coca-Cola 33cl', categorie='boisson', casier_contenu=24,
            prix_achat_casier=Decimal('600'), prix_vente_casier=Decimal('650'),
            seuil_alerte=5,
        )
        self.assertEqual(petit.modele, 'PM24')
        self.assertEqual(petit.get_modele_display(), 'Petit modèle - 24 bouteilles')

        eau = Produit.objects.create(
            nom='Eau Source 50cl', categorie='eau', casier_contenu=24,
            prix_achat_casier=Decimal('300'), prix_vente_casier=Decimal('350'),
            seuil_alerte=5,
        )
        self.assertEqual(eau.modele, 'NC')
        self.assertEqual(eau.get_modele_display(), 'Pas de casier')

    def test_en_retard_et_sanction_par_bouteille(self):
        Parametre.objects.create(nom=SANCTION_CASIER, valeur=Decimal('500'))
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        casier = CasierEmporte.objects.create(
            bon=bon, client=self.client_test, modele='GM12',
            nombre_casiers=4, nombre_rendus=1,
        )
        CasierEmporte.objects.filter(id=casier.id).update(
            date_emport=timezone.now() - timedelta(days=4),
        )
        casier.refresh_from_db()
        self.assertTrue(casier.en_retard)
        self.assertEqual(casier.bouteilles_par_casier, 12)
        self.assertEqual(casier.restant_bouteilles, 36)
        self.assertEqual(casier.montant_sanction, Decimal('18000'))

    def test_acces_interdit_sans_role(self):
        User.objects.create_user(username='simple', password='pass12345')
        self.http_client.login(username='simple', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:liste_casiers_emportes'))
        self.assertRedirects(response, reverse('gestion_depot:dashboard'))

    def test_pages_suivi_et_parametres_rendues(self):
        Parametre.objects.create(nom=SANCTION_CASIER, valeur=Decimal('500'))
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        CasierEmporte.objects.create(bon=bon, client=self.client_test, nombre_casiers=4, nombre_rendus=1)

        self.http_client.login(username='gerant1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:liste_casiers_emportes'))
        self.assertEqual(response.status_code, 200)
        response = self.http_client.get(reverse('gestion_depot:liste_casiers_emportes') + '?statut=en_retard')
        self.assertEqual(response.status_code, 200)
        response = self.http_client.get(reverse('gestion_depot:configurer_sanction'))
        self.assertEqual(response.status_code, 200)

    def test_configurer_sanction_reserve_gerant_admin(self):
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:configurer_sanction'))
        self.assertRedirects(response, reverse('gestion_depot:dashboard'))

        self.http_client.login(username='gerant1', password='pass12345')
        response = self.http_client.post(
            reverse('gestion_depot:configurer_sanction'),
            {'montant': '750'},
        )
        self.assertRedirects(response, reverse('gestion_depot:configurer_sanction'))
        self.assertEqual(Parametre.get(SANCTION_CASIER), Decimal('750'))
