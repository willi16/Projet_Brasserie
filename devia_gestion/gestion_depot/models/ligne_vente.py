from django.db import models
from decimal import Decimal
from .produit import Produit
from .bon_vente import BonVente
from django.core.validators import MinValueValidator, MaxValueValidator


class LigneVente(models.Model):
    bon = models.ForeignKey('BonVente', related_name='lignes', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    fraction = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.25')), MaxValueValidator(Decimal('9.99'))],
    )
    quantite_casiers = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, validators=[MinValueValidator(0.01)])

    def prix_total(self):
        prix_casier = self.produit.prix_vente_casier
        return (prix_casier * self.fraction * self.quantite_casiers).quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.quantite_casiers} x {self.produit.nom} ({self.fraction})"