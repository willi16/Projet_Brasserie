from django.db import models
from .produit import Produit
from .bon_vente import BonVente
from django.core.validators import MinValueValidator


class LigneVente(models.Model):
    FRACTION_CHOICES = [
        (1.00, 'Casier complet'),
        (0.75, '3/4 de casier'),
        (0.50, 'Demi-casier'),
        (0.25, '1/4 de casier'),
    ]
    bon = models.ForeignKey('BonVente', related_name='lignes', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    fraction = models.DecimalField(max_digits=3, decimal_places=2, choices=FRACTION_CHOICES, validators=[MinValueValidator(0.25)])
    quantite_casiers = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, validators=[MinValueValidator(0.01)])

    def prix_total(self):
        prix_casier = self.produit.prix_vente_casier
        return int(prix_casier * self.fraction * self.quantite_casiers)

    def __str__(self):
        return f"{self.quantite_casiers} x {self.produit.nom} ({self.get_fraction_display()})"