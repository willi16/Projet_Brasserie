import re
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator

# Catégories dont les casiers peuvent être emportés et rendus
CATEGORIES_AVEC_CASIERS = {'biere', 'sucrerie'}

# Nombre de bouteilles par casier autorisé pour chaque catégorie de produit
CASIERS_PAR_CATEGORIE = {
    'boisson': [12, 16, 20],
    'biere': [12, 20, 24],
    'eau': [6, 12, 15, 24],
    'sucrerie': [12, 20, 24],
    'canette': [24],
}

# Capacité (cl) à partir de laquelle on considère un "grand modèle"
SEUIL_GRAND_MODELE_CL = 50

# Bouteilles par casier selon le modèle
BOUTEILLES_PAR_MODELE = {'GM12': 12, 'GM20': 20, 'PM24': 24}


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
        ('canette', 'Canette'),
    ]
    CASIER_CHOICES = [
        (6, '6 bouteilles'),
        (12, '12 bouteilles'),
        (15, '15 bouteilles'),
        (16, '16 bouteilles'),
        (20, '20 bouteilles'),
        (24, '24 bouteilles'),
    ]

    MODELE_CHOICES = [
        ('GM12', 'Grand modèle - 12 bouteilles'),
        ('GM20', 'Grand modèle - 20 bouteilles'),
        ('PM24', 'Petit modèle - 24 bouteilles'),
        ('EMB', 'Emballage'),
        ('NC', 'Pas de casier'),
    ]

    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    casier_contenu = models.IntegerField(choices=CASIER_CHOICES)
    modele = models.CharField(max_length=10, choices=MODELE_CHOICES, default='GM12')
    pourcentage_prix_vente = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('25.00'),
        validators=[MinValueValidator(0)],
        help_text="Pourcentage de majoration appliqué sur le prix d'achat pour calculer le prix de vente.",
    )
    prix_achat_casier = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'), validators=[MinValueValidator(0)])
    prix_vente_casier = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'), validators=[MinValueValidator(0)])
    seuil_alerte = models.IntegerField(default=5, validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        self.modele = self.get_modele()
        super().save(*args, **kwargs)

    def get_modele(self):
        """Emballage pour l'eau et la boisson gazeuse, pas de casier pour les canettes,
        petit modèle (< 50cl) ou grand modèle (>= 50cl) pour la bière et la sucrerie."""
        if self.categorie in ('eau', 'boisson'):
            return 'EMB'
        if self.categorie not in CATEGORIES_AVEC_CASIERS:
            return 'NC'
        capacite = capacite_cl(self.nom)
        if capacite is not None and capacite < SEUIL_GRAND_MODELE_CL:
            return 'PM24'
        return 'GM12' if self.casier_contenu == 12 else 'GM20'

    @property
    def libelle_modele(self):
        """Libellé affiché : « Emballage N bouteilles » pour l'eau/la boisson gazeuse."""
        if self.modele == 'EMB':
            return f"Emballage {self.casier_contenu} bouteilles"
        return self.get_modele_display()

    def modeles_possibles(self):
        """Modèles de casier proposables selon la contenance (50cl : 12 ou 20, 65cl+ : 12, < 50cl : 24)."""
        capacite = capacite_cl(self.nom)
        if capacite is None:
            return list(BOUTEILLES_PAR_MODELE)
        if capacite < SEUIL_GRAND_MODELE_CL:
            return ['PM24']
        if capacite == SEUIL_GRAND_MODELE_CL:
            return ['GM12', 'GM20']
        return ['GM12']

    def modele_par_defaut(self):
        possibles = self.modeles_possibles()
        if self.modele in possibles:
            return self.modele
        return possibles[0]

    
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