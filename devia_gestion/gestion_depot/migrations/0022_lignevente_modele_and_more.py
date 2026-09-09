# Ajoute le modèle de casier vendu sur chaque ligne de vente et recalcule le
# modèle des produits : eau et boisson gazeuse passent en "Emballage".

import re
from django.db import migrations, models

CATEGORIES_AVEC_CASIERS = {'biere', 'sucrerie'}
SEUIL_GRAND_MODELE_CL = 50
MODELES_CASIER = ('GM12', 'GM20', 'PM24')


def _capacite_cl(nom):
    m = re.search(r'([\d.,]+)\s*(ml|cl|l)', nom or '', re.IGNORECASE)
    if not m:
        return None
    try:
        valeur = float(m.group(1).replace(',', '.'))
    except ValueError:
        return None
    unite = m.group(2).lower()
    if unite == 'ml':
        return valeur / 10
    if unite == 'l':
        return valeur * 100
    return valeur


def _modele_auto(categorie, nom, casier_contenu):
    if categorie in ('eau', 'boisson'):
        return 'EMB'
    if categorie not in CATEGORIES_AVEC_CASIERS:
        return 'NC'
    capacite = _capacite_cl(nom)
    if capacite is not None and capacite < SEUIL_GRAND_MODELE_CL:
        return 'PM24'
    return 'GM12' if casier_contenu == 12 else 'GM20'


def recompute_modele_produits(apps, schema_editor):
    Produit = apps.get_model('gestion_depot', 'Produit')
    for produit in Produit.objects.all():
        modele = _modele_auto(produit.categorie, produit.nom, produit.casier_contenu)
        if modele != produit.modele:
            produit.modele = modele
            produit.save(update_fields=['modele'])


def backfill_ligne_vente_modele(apps, schema_editor):
    LigneVente = apps.get_model('gestion_depot', 'LigneVente')
    for ligne in LigneVente.objects.select_related('produit').all():
        if ligne.produit.modele in MODELES_CASIER:
            ligne.modele = ligne.produit.modele
            ligne.save(update_fields=['modele'])


class Migration(migrations.Migration):

    dependencies = [
        ("gestion_depot", "0021_recompute_modele_biere_sucrerie"),
    ]

    operations = [
        migrations.AddField(
            model_name="lignevente",
            name="modele",
            field=models.CharField(
                blank=True,
                choices=[
                    ("GM12", "Grand modèle - 12 bouteilles"),
                    ("GM20", "Grand modèle - 20 bouteilles"),
                    ("PM24", "Petit modèle - 24 bouteilles"),
                ],
                max_length=10,
                null=True,
            ),
        ),
        migrations.RunPython(recompute_modele_produits, migrations.RunPython.noop),
        migrations.RunPython(backfill_ligne_vente_modele, migrations.RunPython.noop),
    ]