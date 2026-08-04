# gestion_depot/models/bon_livraison.py
from django.db import models
from django.contrib.auth.models import User
from .fournisseur import Fournisseur

class BonLivraison(models.Model):
    reference = models.CharField(max_length=50, unique=True)
    date_livraison = models.DateTimeField(auto_now_add=True)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT)
    utilisateur = models.ForeignKey(User, on_delete=models.PROTECT)


    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
        if not self.reference:
            self.reference = f"LIV-{self.pk:04d}"
            super().save(update_fields=['reference'])
            return
        super().save(*args, **kwargs)



    def total_quantite(self):
        return sum(ligne.quantite_casiers for ligne in self.lignes.all())

    def total_montant(self):
        return sum(ligne.total() for ligne in self.lignes.all())



    def __str__(self):
        return f"Livraison {self.reference} - {self.total_quantite()} casiers"