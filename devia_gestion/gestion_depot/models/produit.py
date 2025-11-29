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

    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    casier_contenu = models.IntegerField(choices=CASIER_CHOICES)
    prix_achat_casier = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    prix_vente_casier = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    seuil_alerte = models.IntegerField(default=5, validators=[MinValueValidator(0)])

    
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