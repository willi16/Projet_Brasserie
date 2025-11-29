from django.db import models
from .produit import Produit

class LigneLivraison(models.Model):
    bon = models.ForeignKey('BonLivraison', related_name='lignes', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_casiers = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    casier_contenu = models.IntegerField(default=24)  # ← Ajoute ce champ
    prix_achat_casier = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ← Ajoute ce champ

    def total(self):
        return self.quantite_casiers * self.prix_achat_casier

    def __str__(self):
        return f"{self.quantite_casiers} x {self.produit.nom} ({self.casier_contenu} btl) - {self.total()} FCFA"