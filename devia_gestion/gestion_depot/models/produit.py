from django.db import models
from django.core.validators import MinValueValidator

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

    @classmethod
    def modele_from_casier_contenu(cls, casier_contenu):
        return {
            12: 'GM12',
            20: 'GM20',
            24: 'PM24',
        }.get(casier_contenu, 'GM12')

    def get_modele(self):
        return Produit.modele_from_casier_contenu(self.casier_contenu)

    
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