# Recalcule le modèle de casier des produits : les casiers ne sont suivis
# que pour la bière et la sucrerie (la boisson gazeuse passe en "pas de casier").

import re
from django.db import migrations

CATEGORIES_AVEC_CASIERS = {'biere', 'sucrerie'}
SEUIL_GRAND_MODELE_CL = 50


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
    if categorie not in CATEGORIES_AVEC_CASIERS:
        return 'NC'
    capacite = _capacite_cl(nom)
    if capacite is not None and capacite < SEUIL_GRAND_MODELE_CL:
        return 'PM24'
    return 'GM12' if casier_contenu == 12 else 'GM20'


def recompute_modele_produits(apps, schema_editor):
    Produit = apps.get_model('gestion_depot', 'Produit')
    for produit in Produit.objects.all():
        produit.modele = _modele_auto(produit.categorie, produit.nom, produit.casier_contenu)
        produit.save(update_fields=['modele'])


class Migration(migrations.Migration):

    dependencies = [
        ("gestion_depot", "0020_remove_casier_facturation_bouteille"),
    ]

    operations = [
        migrations.RunPython(recompute_modele_produits, migrations.RunPython.noop),
    ]