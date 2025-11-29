
from django.db import models
from .client import Client

from django.contrib.auth.models import User

class BonVente(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('valide', 'Validée'),
        ('annule', 'Annulée'),
    ]
    reference = models.CharField(max_length=50, unique=True)
    date_vente = models.DateTimeField(auto_now_add=True)
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True)
    type_paiement = models.CharField(max_length=20, choices=[('especes', 'Espèces'), ('credit', 'Crédit')])
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='valide')


    def save(self, *args, **kwargs):
        if not self.reference:
            # Génère une référence automatique
            last_bon = BonVente.objects.order_by('-id').first()
            if last_bon and last_bon.reference:
                try:
                    ref_num = int(last_bon.reference.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    ref_num = 1
            else:
                ref_num = 1
            self.reference = f"VENTE-{ref_num:04d}"
        super().save(*args, **kwargs)

    
    def total(self):
        return sum(ligne.prix_total() for ligne in self.lignes.all())

    def __str__(self):
        return f"Vente {self.reference} - {self.total()} FCFA"

