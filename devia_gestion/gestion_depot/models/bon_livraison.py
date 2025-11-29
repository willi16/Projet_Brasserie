# gestion_depot/models/bon_livraison.py
from django.db import models
from django.contrib.auth.models import User
from .fournisseur import Fournisseur

class BonLivraison(models.Model):
    reference = models.CharField(max_length=50, unique=True)
    date_livraison = models.DateTimeField(auto_now_add=True)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)


    def save(self, *args, **kwargs):
        if not self.reference:
            # Génère une référence automatique
            last_bon = BonLivraison.objects.order_by('-id').first()
            if last_bon and last_bon.reference:
                try:
                    ref_num = int(last_bon.reference.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    ref_num = 1
            else:
                ref_num = 1
            self.reference = f"LIV-{ref_num:04d}"
        super().save(*args, **kwargs)



    def total_quantite(self):
        return sum(ligne.quantite_casiers for ligne in self.lignes.all())

    def total_montant(self):
        return sum(ligne.total() for ligne in self.lignes.all())



    def __str__(self):
        return f"Livraison {self.reference} - {self.total_quantite()} casiers"