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


class ProduitsMultiCreateTests(BaseTest):
    def _post_data(self, nb=3, produits=None):
        data = {
            'form-TOTAL_FORMS': str(nb),
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': str(nb),
            'form-MAX_NUM_FORMS': str(nb),
        }
        for i in range(nb):
            if produits:
                nom, cat, casier, achat, vente = produits[i]
            else:
                nom, cat, casier, achat, vente = f'Produit multi {i}', 'boisson', '24', '700', '750'
            data[f'form-{i}-nom'] = nom
            data[f'form-{i}-categorie'] = cat
            data[f'form-{i}-casier_contenu'] = casier
            data[f'form-{i}-prix_achat_casier'] = achat
            data[f'form-{i}-prix_vente_casier'] = vente
            data[f'form-{i}-seuil_alerte'] = '5'
        return data

    def test_page_get_rendue_avec_n_formulaires(self):
        self.http_client.login(username='gerant1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:produits_multi_create', args=[3]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['formset'].forms), 3)

    def test_creation_multiple_ok(self):
        self.http_client.login(username='gerant1', password='pass12345')
        nb_avant = Produit.objects.count()
        response = self.http_client.post(
            reverse('gestion_depot:produits_multi_create', args=[3]),
            self._post_data(3),
        )
        self.assertRedirects(response, reverse('gestion_depot:liste_produits'))
        self.assertEqual(Produit.objects.count(), nb_avant + 3)
        self.assertTrue(Produit.objects.filter(nom='Produit multi 0').exists())
        self.assertTrue(Produit.objects.filter(nom='Produit multi 2').exists())

    def test_prix_vente_inferieur_achat_rejete(self):
        self.http_client.login(username='gerant1', password='pass12345')
        nb_avant = Produit.objects.count()
        data = self._post_data(2, produits=[
            ('Produit OK', 'eau', '24', '300', '350'),
            ('Produit invalide', 'eau', '24', '1000', '900'),
        ])
        response = self.http_client.post(
            reverse('gestion_depot:produits_multi_create', args=[2]),
            data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Produit.objects.count(), nb_avant)

    def test_nb_forms_hors_borne_redirige(self):
        self.http_client.login(username='gerant1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:produits_multi_create', args=[1]))
        self.assertRedirects(response, reverse('gestion_depot:liste_produits'))
        response = self.http_client.get(reverse('gestion_depot:produits_multi_create', args=[21]))
        self.assertRedirects(response, reverse('gestion_depot:liste_produits'))


class RapportTests(BaseTest):
    def _creer_bon_valide(self, jours=0):
        bon = BonVente.objects.create(
            vendeur=self.caissier, client=self.client_test,
            type_paiement='especes', statut='valide',
        )
        LigneVente.objects.create(
            bon=bon, produit=self.produit,
            fraction=Decimal('1.00'), quantite_casiers=Decimal('2'),
        )
        if jours:
            BonVente.objects.filter(pk=bon.pk).update(
                date_vente=timezone.now() - timedelta(days=jours),
            )
        return bon

    def test_page_rapport_rendue(self):
        self._creer_bon_valide()
        self.http_client.login(username='gerant1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:rapport_ventes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rapport des ventes')

    def test_ajax_renvoie_les_indicateurs(self):
        self._creer_bon_valide()
        self.http_client.login(username='gerant1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:rapport_ventes_ajax'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(payload['total_revenu'], 0)
        self.assertEqual(len(payload['lignes']), 1)
        self.assertEqual(payload['lignes'][0]['produit'], self.produit.nom)
        self.assertIsNotNone(payload['produit_plus_vendu'])
        self.assertIn('labels_jours', payload)

    def test_ajax_filtre_periode_journalier(self):
        self._creer_bon_valide(jours=30)
        self.http_client.login(username='gerant1', password='pass12345')
        response = self.http_client.get(
            reverse('gestion_depot:rapport_ventes_ajax'),
            {'periode': 'journalier'},
        )
        payload = response.json()
        self.assertEqual(payload['total_revenu'], 0)
        self.assertEqual(len(payload['lignes']), 0)

    def test_ajax_403_pour_caissier(self):
        self.http_client.login(username='caissier1', password='pass12345')
        response = self.http_client.get(reverse('gestion_depot:rapport_ventes_ajax'))
        self.assertEqual(response.status_code, 403)


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


class DataTableTests(BaseTest):
    def _get(self, url_name, params=None, username='caissier1'):
        self.http_client.login(username=username, password='pass12345')
        url = reverse(f'gestion_depot:{url_name}')
        if params:
            url += '?' + '&'.join(f'{k}={v}' for k, v in params.items())
        return self.http_client.get(url)

    def test_produits_renvoie_json_data(self):
        response = self._get('dt_produits', {'draw': '1', 'start': '0', 'length': '10'})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['draw'], '1')
        self.assertIn('recordsTotal', payload)
        self.assertIn('recordsFiltered', payload)
        self.assertTrue(len(payload['data']) >= 1)
        row = payload['data'][0]
        for key in ('nom', 'categorie_display', 'casier_contenu', 'modele_display',
                    'prix_vente_casier', 'stock_actuel', 'statut_html'):
            self.assertIn(key, row)
        self.assertEqual(row['nom'], self.produit.nom)

    def test_produits_recherche_globale(self):
        Produit.objects.create(
            nom='Flag Spécial 65cl', categorie='biere', casier_contenu=12,
            prix_achat_casier=Decimal('900'), prix_vente_casier=Decimal('950'),
            seuil_alerte=5,
        )
        response = self._get('dt_produits', {'search[value]': 'Flag'})
        payload = response.json()
        noms = [r['nom'] for r in payload['data']]
        self.assertIn('Flag Spécial 65cl', noms)
        self.assertNotIn(self.produit.nom, noms)

    def test_produits_recherche_par_colonne(self):
        response = self._get('dt_produits', {'columns[1][search][value]': 'boisson'})
        payload = response.json()
        self.assertEqual(len(payload['data']), 1)
        self.assertEqual(payload['data'][0]['nom'], self.produit.nom)

    def test_produits_tri(self):
        Produit.objects.create(
            nom='AA Bière', categorie='biere', casier_contenu=12,
            prix_achat_casier=Decimal('900'), prix_vente_casier=Decimal('950'),
            seuil_alerte=5,
        )
        response = self._get('dt_produits', {'order[0][column]': '0', 'order[0][dir]': 'desc'})
        payload = response.json()
        noms = [r['nom'] for r in payload['data']]
        self.assertEqual(noms, sorted(noms, reverse=True))

    def test_produits_pagination(self):
        for i in range(5):
            Produit.objects.create(
                nom=f'Produit pag {i}', categorie='eau', casier_contenu=24,
                prix_achat_casier=Decimal('300'), prix_vente_casier=Decimal('350'),
                seuil_alerte=5,
            )
        response = self._get('dt_produits', {'start': '0', 'length': '5'})
        self.assertEqual(len(response.json()['data']), 5)

    def test_fournisseurs_403_pour_caissier(self):
        response = self._get('dt_fournisseurs', username='caissier1')
        self.assertEqual(response.status_code, 403)

    def test_fournisseurs_ok_pour_gerant(self):
        response = self._get('dt_fournisseurs', username='gerant1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['recordsTotal'], 1)

    def test_livraisons_ok_pour_gerant(self):
        response = self._get('dt_livraisons', username='gerant1')
        self.assertEqual(response.status_code, 200)

    def test_ventes_caissier_scope_vendeur(self):
        bon_caissier = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        bon_admin = BonVente.objects.create(vendeur=self.admin, client=self.client_test, type_paiement='especes')
        response = self._get('dt_bons_vente', username='caissier1')
        payload = response.json()
        self.assertEqual(payload['recordsTotal'], 1)
        self.assertEqual(payload['data'][0]['reference'], bon_caissier.reference)

    def test_ventes_filtre_statut(self):
        BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes', statut='valide')
        BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes', statut='annule')
        response = self._get('dt_bons_vente', {'statut': 'valide'}, username='gerant1')
        payload = response.json()
        self.assertEqual(payload['recordsTotal'], 1)
        self.assertEqual(payload['data'][0]['statut_html'].find('badge-success') != -1, True)

    def test_casiers_ok_avec_filtre(self):
        bon = BonVente.objects.create(vendeur=self.caissier, client=self.client_test, type_paiement='especes')
        CasierEmporte.objects.create(bon=bon, client=self.client_test, nombre_casiers=4, nombre_rendus=1)
        response = self._get('dt_casiers', username='caissier1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['recordsTotal'], 1)

    def test_casiers_403_sans_role(self):
        User.objects.create_user(username='simple2', password='pass12345')
        response = self._get('dt_casiers', username='simple2')
        self.assertEqual(response.status_code, 403)

    def test_users_403_pour_gerant(self):
        response = self._get('dt_users', username='gerant1')
        self.assertEqual(response.status_code, 403)

    def test_users_ok_pour_admin(self):
        response = self._get('dt_users', username='admin1')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()['recordsTotal'], 3)

    def test_users_filtre_groupe(self):
        response = self._get('dt_users', {'group': 'Gérant'}, username='admin1')
        payload = response.json()
        self.assertEqual(payload['recordsTotal'], 1)
        self.assertEqual(payload['data'][0]['username'], 'gerant1')

    def test_logs_ok_pour_admin(self):
        response = self._get('dt_logs', username='admin1')
        self.assertEqual(response.status_code, 200)

    def test_logs_403_pour_gerant(self):
        response = self._get('dt_logs', username='gerant1')
        self.assertEqual(response.status_code, 403)

    def test_pages_listes_rendues_avec_datatables(self):
        pages = {
            'liste_produits': 'caissier1',
            'liste_bons_vente': 'caissier1',
            'liste_casiers_emportes': 'caissier1',
            'liste_fournisseurs': 'gerant1',
            'liste_livraisons': 'gerant1',
            'manage_users': 'admin1',
            'user_logs_full': 'admin1',
        }
        for url_name, username in pages.items():
            self.http_client.login(username=username, password='pass12345')
            response = self.http_client.get(reverse(f'gestion_depot:{url_name}'))
            self.assertEqual(response.status_code, 200, msg=f'{url_name} renvoie {response.status_code}')
            self.assertContains(response, 'DataTable')
