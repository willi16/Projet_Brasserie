import re
from django.db import models
from django.core.validators import MinValueValidator

# Catégories dont les casiers peuvent être emportés et rendus
CATEGORIES_AVEC_CASIERS = {'boisson', 'biere'}

# Capacité (cl) à partir de laquelle on considère un "grand modèle"
SEUIL_GRAND_MODELE_CL = 50


def capacite_cl(nom):
    """Extrait la capacité d'une bouteille depuis le nom du produit (ex. '50cl', '1.5L', '330ml')."""
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


class Produit(models.Model):
    CATEGORIE_CHOICES = [
        ('boisson', 'Boisson Gazeuse'),
        ('biere', 'Bière'),
        ('eau', 'Eau'),
        ('sucrerie', 'Sucrerie'),
    ]
    CASIER_CHOICES = [
        (6, '6 bouteilles'),
        (12, '12 bouteilles'),
        (20, '20 bouteilles'),
        (24, '24 bouteilles'),
    ]

    MODELE_CHOICES = [
        ('GM12', 'Grand modèle - 12 bouteilles'),
        ('GM20', 'Grand modèle - 20 bouteilles'),
        ('PM24', 'Petit modèle - 24 bouteilles'),
        ('NC', 'Pas de casier'),
    ]

    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    casier_contenu = models.IntegerField(choices=CASIER_CHOICES)
    modele = models.CharField(max_length=10, choices=MODELE_CHOICES, default='GM12')
    prix_achat_casier = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    prix_vente_casier = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    seuil_alerte = models.IntegerField(default=5, validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        self.modele = self.get_modele()
        super().save(*args, **kwargs)

    def get_modele(self):
        """Grand modèle (GM12/GM20) si boisson/bière >= 50cl, petit modèle (PM24) sinon, pas de casier pour le reste."""
        if self.categorie not in CATEGORIES_AVEC_CASIERS:
            return 'NC'
        capacite = capacite_cl(self.nom)
        if capacite is not None and capacite < SEUIL_GRAND_MODELE_CL:
            return 'PM24'
        return 'GM12' if self.casier_contenu == 12 else 'GM20'

    
    def stock_disponible(self):
        entrees = self.mouvement_set.filter(type_mouvement='entree').aggregate(total=models.Sum('quantite_casiers'))['total'] or 0
        sorties = self.mouvement_set.filter(type_mouvement='sortie').aggregate(total=models.Sum('quantite_casiers'))['total'] or 0
        return round(entrees - sorties, 2)

    def en_alerte(self):
        return self.stock_disponible() <= self.seuil_alerte

    def __str__(self):
        return f"{self.nom} ({self.casier_contenu} btl)"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(prix_vente_casier__gte=models.F('prix_achat_casier')),
                name='prix_vente_superieur_achat'
            )
        ]